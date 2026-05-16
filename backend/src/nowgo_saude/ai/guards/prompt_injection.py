"""Prompt-injection guard (T028, FR-009).

Run on **citizen-supplied text** (the LLM's *input*) before it reaches any
provider. Catches the well-known classes of injection patterns documented
across the OWASP Top 10 for LLM Apps:

* **Instruction overrides** \u2014 "ignore previous instructions", "disregard the
  system prompt", "you are now a different assistant".
* **Role hijacking** \u2014 fake system/assistant turns embedded inside user
  content ("system: ...", "<|im_start|>system").
* **Tool/command exfiltration** \u2014 attempts to coerce the model into
  printing environment variables, API keys, or internal prompts.
* **Encoded payloads** \u2014 base64/hex/url-encoded blocks longer than a
  small threshold, which are almost never legitimate in citizen reports.

The guard is keyword-driven on purpose: we never *interpret* the
content (no nested LLM, no recursion), only flag the surface forms.
False positives are tolerable \u2014 the citizen's text is still ingested
into the data warehouse; only the LLM call is suppressed.
"""

from __future__ import annotations

import re

from .base import GuardVerdict

_INSTRUCTION_OVERRIDES: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Match the verb followed (within ~30 chars) by an "above/previous"
    # qualifier; lets natural PT-BR phrasing like "esqueça as instru\u00e7\u00f5es
    # anteriores" through without requiring rigid adjacency.
    ("ignore_previous", re.compile(r"\b(ignore|disregard|forget|esque[cç]a|desconsidere)\b[\w\s\u00c0-\u017f]{0,30}\b(all|every|todas?|qualquer|previous|anterior(es)?|above|acima|instru[cç][oõ]es?)\b", re.I)),
    ("new_instructions", re.compile(r"\b(new|novas?)\s+(instructions?|instru[cç][oõ]es?|rules?|regras?)\s+(below|abaixo|a seguir|follow)\b", re.I)),
    ("override_system", re.compile(r"\b(override|substitua|replace)\s+(the\s+)?(system|prompt|instru[cç][aã]o)\b", re.I)),
    ("you_are_now", re.compile(r"\byou\s+are\s+now\s+(an?|a different|no longer)\b", re.I)),
    ("voce_e_agora", re.compile(r"\b(voc[eê]|tu)\s+(\u00e9|es|s[aã]o)\s+agora\s+um[a]?\b", re.I)),
)

_ROLE_HIJACK: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("fake_system_turn", re.compile(r"(^|\n)\s*(system|sistema|assistant|assistente)\s*:\s*", re.I)),
    ("im_start_token", re.compile(r"<\|im_(start|end)\|>", re.I)),
    ("chatml_role", re.compile(r"<\|(system|user|assistant)\|>", re.I)),
    ("triple_dash_role", re.compile(r"(^|\n)---\s*(system|assistant)\s*---", re.I)),
)

_EXFILTRATION: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("print_system_prompt", re.compile(r"\b(print|show|reveal|imprim\w+|mostre|revele)\s+(the\s+)?(system|original|initial)\s+(prompt|instru[cç][aã]o)\b", re.I)),
    ("print_env_secret", re.compile(r"\b(print|show|echo|dump|imprim\w+|mostre)\s+(your|seu|sua|the)?\s*(api[\s_-]?key|token|env(ironment)?\s+vars?|secret|senha)\b", re.I)),
    ("repeat_above", re.compile(r"\b(repeat|repita|copy|copie)\s+(everything|tudo|all|your)\s+(above|acima|previous|anterior|system|instructions)\b", re.I)),
)

# Encoded payloads. We deliberately set thresholds short enough to catch
# realistic injection but long enough to skip cases like a citizen
# pasting a short URL/token from a legitimate notification.
_ENCODED_PAYLOAD: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("base64_block", re.compile(r"(?:[A-Za-z0-9+/]{40,}={0,2})")),
    ("hex_block", re.compile(r"\b(?:[0-9a-fA-F]{64,})\b")),
)


def detect_prompt_injection(text: str) -> GuardVerdict:
    """Flag prompt-injection attempts in ``text``.

    Returns
    -------
    GuardVerdict.ok()                                when no patterns match.
    GuardVerdict.deny("prompt_injection", ...)        otherwise.

    Callers MUST treat denial as final \u2014 do **not** retry with a softened
    payload, since the most common reason for a softened-retry pattern is
    a sophisticated injection that already succeeded.
    """
    if not text or not text.strip():
        return GuardVerdict.ok()

    hits: list[str] = []
    for group in (_INSTRUCTION_OVERRIDES, _ROLE_HIJACK, _EXFILTRATION, _ENCODED_PAYLOAD):
        hits.extend(tag for tag, pat in group if pat.search(text))

    if not hits:
        return GuardVerdict.ok()

    return GuardVerdict.deny(
        reason="prompt_injection",
        detail=f"matched injection patterns: {','.join(hits)}",
        matched=tuple(hits),
    )
