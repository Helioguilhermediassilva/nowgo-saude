"""Deterministic guards applied before/after every LLM call.

These are *not* classifiers — they are conservative pattern matchers tuned
for high recall. Anything they flag is either rejected outright or routed
through the human-in-the-loop queue. False positives are acceptable; false
negatives (clinical advice leaking, prompt injection succeeding) are not.

Each guard returns a :class:`GuardVerdict` so the worker layer can log the
exact reason and audit it.
"""

from __future__ import annotations

from .base import GuardVerdict
from .clinical import check_clinical_output
from .intent import check_intent
from .output_filter import sanitize_output
from .prompt_injection import detect_prompt_injection

__all__ = [
    "GuardVerdict",
    "check_clinical_output",
    "check_intent",
    "detect_prompt_injection",
    "sanitize_output",
]
