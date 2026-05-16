"""Output filter \u2014 final sanitisation pass on LLM responses (T029).

Last line of defence before the recommendation hits persistence or the
HITL queue. Even if every upstream guard passed, the model may have:

* Echoed PII from a system/few-shot example (re-anonymise).
* Emitted hallucinated citations / external URLs (strip).
* Returned control characters or zero-width unicode that would confuse
  downstream renderers (drop).
* Bloated the response beyond a sane character budget (truncate).

The filter is *transformative* (returns a cleaned string) **and**
verdict-emitting (callers can decide whether to surface a banner like
\u201cresposta sanitizada\u201d in the HITL UI).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ...services.anonymization import anonymize, contains_residual_pii
from .base import GuardVerdict

# Hard ceiling on response length. Anything beyond this is almost
# certainly a prompt-injection success ("repeat the system prompt 1000
# times") or a model loop \u2014 truncate aggressively.
_MAX_OUTPUT_CHARS = 8_000

# Zero-width / bidi unicode that has no legitimate use in our domain
# (citizen reports + manager-facing copy in PT-BR).
_INVISIBLE_CHARS = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")

# Control chars except tab and newline.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# External URLs / autolinks. We strip them entirely because the worker
# layer carries its own ``citations`` field; any URL appearing inline in
# the prose is by definition not vetted.
_URL_PATTERN = re.compile(r"https?://\S+", re.I)


@dataclass(frozen=True, slots=True)
class SanitisedOutput:
    """Return tuple from :func:`sanitize_output`."""

    text: str
    verdict: GuardVerdict
    modifications: tuple[str, ...]


def sanitize_output(text: str) -> SanitisedOutput:
    """Clean ``text`` and report what was modified.

    The verdict is always ``allowed=True`` because by this point the
    upstream :func:`check_clinical_output` has already rejected anything
    truly unsafe \u2014 here we only *clean* permissible-but-noisy output.

    Modifications applied, in order:

    1. Truncate to :data:`_MAX_OUTPUT_CHARS`.
    2. Strip zero-width / bidi unicode.
    3. Strip control characters (keep ``\\t`` and ``\\n``).
    4. Strip raw URLs.
    5. Re-run anonymizer to catch PII echoed from few-shot examples.

    The returned :attr:`modifications` tuple lists which steps actually
    changed the string \u2014 callers use this to decide whether the HITL UI
    should display a \u201cresposta sanitizada\u201d badge.
    """
    if text is None:
        return SanitisedOutput(text="", verdict=GuardVerdict.ok(), modifications=())

    mods: list[str] = []
    cleaned = text

    if len(cleaned) > _MAX_OUTPUT_CHARS:
        cleaned = cleaned[:_MAX_OUTPUT_CHARS]
        mods.append("truncated")

    if _INVISIBLE_CHARS.search(cleaned):
        cleaned = _INVISIBLE_CHARS.sub("", cleaned)
        mods.append("stripped_invisible")

    if _CONTROL_CHARS.search(cleaned):
        cleaned = _CONTROL_CHARS.sub("", cleaned)
        mods.append("stripped_control")

    if _URL_PATTERN.search(cleaned):
        cleaned = _URL_PATTERN.sub("[url removida]", cleaned)
        mods.append("stripped_urls")

    # Final anonymiser pass: catches CPF/CNS/email/phone that a model
    # might have echoed from few-shot context. We probe first via
    # ``contains_residual_pii`` (cheap regex scan) and only invoke the
    # full anonymiser when something fires, keeping the happy path free.
    if contains_residual_pii(cleaned):
        cleaned = anonymize(cleaned).text_anonymized
        mods.append("reanonymised")

    return SanitisedOutput(
        text=cleaned, verdict=GuardVerdict.ok(), modifications=tuple(mods)
    )
