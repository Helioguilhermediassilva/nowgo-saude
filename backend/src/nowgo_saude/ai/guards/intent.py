"""Intent guard \u2014 enforces public-health scope (T026, FR-005).

Rejects requests whose surface text is clearly off-topic for the
NowGo Sa\u00fade domain (citizen complaints, health-unit operations, sentiment,
queue/wait times, drug shortage, vaccine coverage, sanitary alerts).

This is a *coarse* filter \u2014 it errs on the side of accepting borderline
cases because the downstream guards (clinical, output) catch unsafe
content even when intent is permissive. False positives here are costlier
than false negatives, since they silence legitimate citizen signal.

The list of off-topic markers is intentionally short and explicit; we do
not try to enumerate every possible irrelevant query. Anything not
matching off-topic markers AND not matching at least one in-scope marker
flips to the conservative ``ambiguous`` verdict, which is *allowed* but
tagged so the worker can log it for tuning.
"""

from __future__ import annotations

import re

from .base import GuardVerdict

# Off-topic markers: explicit attempts to redirect the model away from
# the public-health surface. ASCII-only on purpose so that any accented
# variant is treated as in-scope (we'd rather process Portuguese with
# diacritics than silently drop it).
_OFF_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("creative_writing", re.compile(r"\b(escreva|write)\s+(um|uma|a|an)\s+(poema|poem|conto|story|piada|joke|letra de m[uú]sica)\b", re.I)),
    ("code_generation", re.compile(r"\b(escreva|write|generate)\s+(c[oó]digo|code|um script|a python|um programa)\b", re.I)),
    ("personal_advice", re.compile(r"\b(meu relacionamento|my relationship|namorad[oa]|c[oô]njuge|spouse)\b", re.I)),
    ("financial_advice", re.compile(r"\b(investir|investment|bolsa de valores|stock market|criptomoeda|crypto)\b", re.I)),
    ("legal_advice", re.compile(r"\b(processo judicial|advogad[oa]|lawyer|tribunal de just[ií]a)\b", re.I)),
)

# In-scope markers: at least one of these signals the request is on-topic
# enough to bypass the ambiguity verdict. The set is broad on purpose
# (synonyms in PT-BR + EN) since recall is more important than precision.
_IN_SCOPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("complaint", re.compile(r"\b(reclama[cç][aã]o|complaint|denuncia|denúncia)\b", re.I)),
    ("queue_wait", re.compile(r"\b(fila|wait\s*time|tempo de espera|aguard\w+)\b", re.I)),
    ("unit_ops", re.compile(r"\b(ubs|upa|posto de sa[uú]de|hospital|cl[ií]nica|health\s*(unit|center))\b", re.I)),
    ("supply", re.compile(r"\b(medicament|vacin|insumo|estoque|stock|shortage|desabastecimento)\b", re.I)),
    ("sanitary", re.compile(r"\b(surto|outbreak|epidem|dengue|covid|gripe|influenza|sarampo|measles)\b", re.I)),
    ("citizen_signal", re.compile(r"\b(cidad[aã]o|munic[ií]pe|paciente|patient|usu[aá]rio do sus)\b", re.I)),
    ("coverage", re.compile(r"\b(cobertura|coverage|aten[cç][aã]o b[aá]sica|primary\s*care)\b", re.I)),
    ("topic_keywords", re.compile(r"\b(satisfa[cç][aã]o|sentiment|atendimento|servi[cç]o p[uú]blico)\b", re.I)),
)


def check_intent(text: str) -> GuardVerdict:
    """Return :class:`GuardVerdict` for ``text`` against the public-health scope.

    Verdicts
    --------
    allowed=True, reason=""                \u2014 in-scope (matched at least one
                                             in-scope marker).
    allowed=True, reason="ambiguous"        \u2014 neutral text, neither clearly
                                             in nor out of scope; let the
                                             worker decide.
    allowed=False, reason="off_topic"       \u2014 matched an off-topic marker.
    """
    if not text or not text.strip():
        # Empty input is not a guard concern \u2014 callers MUST validate
        # non-emptiness upstream (typically pydantic). We return ok() so
        # the guard composition stays associative.
        return GuardVerdict.ok()

    off_hits: list[str] = [tag for tag, pat in _OFF_TOPIC_PATTERNS if pat.search(text)]
    if off_hits:
        return GuardVerdict.deny(
            reason="off_topic",
            detail=f"matched off-topic markers: {','.join(off_hits)}",
            matched=tuple(off_hits),
        )

    in_hits: list[str] = [tag for tag, pat in _IN_SCOPE_PATTERNS if pat.search(text)]
    if in_hits:
        return GuardVerdict(
            allowed=True, reason="", detail="", matched_patterns=tuple(in_hits)
        )

    # Neither off-topic nor explicitly in-scope \u2014 admit, but tag.
    return GuardVerdict(allowed=True, reason="ambiguous", detail="no in-scope marker matched")
