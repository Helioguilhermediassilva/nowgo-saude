"""Clinical guard \u2014 blocks diagnosis, prescription and treatment advice (T027).

Applied to **LLM output** before any human sees it (and before any
downstream system acts on it). NowGo Sa\u00fade is an *operational* tool for
public-health managers, not a clinical decision-support system. Any LLM
response that drifts into individual clinical guidance is rejected and
the recommendation routes to the human escalation queue \u2014 never
auto-approved \u2014 per Constitution Principle IX and spec FR-005.

The implementation is intentionally conservative:
- Matches on Portuguese (PT-BR) clinical verbs ("diagnosticar", "prescrever",
  "indicar [medicamento]", "iniciar [droga]", "tomar [dose]") plus their
  English equivalents.
- Catches dose-like patterns (number + mg/ml/UI/comprimido) which are
  near-certain markers of prescription drift.
- Catches differential-diagnosis phrasing ("provavelmente \u00e9 X", "trata-se
  de Y", "compat\u00edvel com Z").
"""

from __future__ import annotations

import re

from .base import GuardVerdict

# Verb + object patterns. Each pattern is paired with a stable tag for
# audit grouping.
_CLINICAL_VERBS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("diagnosis_verb", re.compile(r"\b(diagnostic\w+|diagnose[sd]?|diagnosing)\b", re.I)),
    ("prescription_verb", re.compile(r"\b(prescrev\w+|prescrib\w+|receit[aeo]\w*)\b", re.I)),
    ("treatment_verb", re.compile(r"\b(tratar|treat\w*|medicar|medicat\w+)\s+(o\s+paciente|the\s+patient|com|with)\b", re.I)),
    ("recommend_drug", re.compile(r"\b(recomend\w+|recommend\w+|indic\w+)\s+(o\s+uso|the\s+use|tomar|taking|the?\s+drug|o\s+medicamento)\b", re.I)),
    ("start_drug", re.compile(r"\b(iniciar|start\w*|begin\w*)\s+(tratamento|treatment|antibi[oó]tic\w+|terapia)\b", re.I)),
    ("dose_instruction", re.compile(r"\b(tomar|take|administer\w*|administrar)\s+\d+\s*(mg|ml|g|ui|comprimid|tablet|capsul)", re.I)),
)

# Dose / drug name patterns. These fire on their own \u2014 a bare dose
# instruction is treated as prescription drift even without an explicit
# verb.
_DOSE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("dose_mg", re.compile(r"\b\d+\s*mg\s+(de\s+\w+|of\s+\w+|a cada|every|por dia|per day)\b", re.I)),
    ("dose_frequency", re.compile(r"\b\d+\s*x\s*(ao dia|por dia|a day|daily)\b", re.I)),
)

# Differential / definitive diagnosis phrasing.
_DIFFERENTIAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("definitive_dx", re.compile(r"\b(trata-se de|isto [eé]|this is)\s+(uma?|an?)\s+\w+", re.I)),
    ("probable_dx", re.compile(r"\b(provavelmente|likely|most likely)\s+(\u00e9|is|um caso de|a case of)\b", re.I)),
    ("compatible_dx", re.compile(r"\b(compat[ií]vel com|consistent with|suggestive of|sugest\w+\s+de)\b", re.I)),
)

_ALL_PATTERNS = _CLINICAL_VERBS + _DOSE_PATTERNS + _DIFFERENTIAL_PATTERNS


def check_clinical_output(text: str) -> GuardVerdict:
    """Reject LLM outputs that drift into clinical guidance.

    Returns
    -------
    GuardVerdict.ok()                         when no clinical patterns fire.
    GuardVerdict.deny("clinical_drift", ...)  when one or more patterns match.

    Pattern tags are surfaced via :attr:`matched_patterns` so the
    HITL queue can group similar drifts together for prompt-tuning.
    """
    if not text or not text.strip():
        return GuardVerdict.ok()

    hits: list[str] = [tag for tag, pat in _ALL_PATTERNS if pat.search(text)]
    if not hits:
        return GuardVerdict.ok()

    return GuardVerdict.deny(
        reason="clinical_drift",
        detail=f"output triggered clinical patterns: {','.join(hits)}",
        matched=tuple(hits),
    )
