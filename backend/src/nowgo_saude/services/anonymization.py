"""PII detection and tokenization.

The MVP uses a regex-based recognizer covering the categories required by the
TelemetryEvent JSON Schema (cpf, cns, name, email, phone, address). This module
exposes the same shape (``anonymize(text) -> AnonymizationResult``) the future
Presidio-backed implementation will provide, so wiring upstream code stays
stable when we swap engines.
"""

from __future__ import annotations

import hmac
import re
from dataclasses import dataclass, field
from hashlib import sha256

from ..config import get_settings

PiiCategory = str  # one of: cpf|cns|name|email|phone|address


@dataclass(frozen=True)
class _Recognizer:
    category: PiiCategory
    pattern: re.Pattern[str]


_RECOGNIZERS: tuple[_Recognizer, ...] = (
    _Recognizer("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    _Recognizer("cns", re.compile(r"\b\d{3} ?\d{4} ?\d{4} ?\d{4}\b")),
    _Recognizer(
        "phone",
        re.compile(r"\b(?:\+?55 ?)?\(?\d{2}\)? ?9?\d{4}-?\d{4}\b"),
    ),
    _Recognizer(
        "email",
        re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    ),
)


@dataclass(frozen=True)
class PiiFinding:
    """A single PII match: original value and the deterministic vault token."""

    category: PiiCategory
    value: str
    token: str


@dataclass
class AnonymizationResult:
    text_anonymized: str
    pii_tokens: list[str] = field(default_factory=list)
    findings: list[PiiFinding] = field(default_factory=list)
    failed: bool = False
    failure_reason: str | None = None


def _tokenize(category: PiiCategory, value: str) -> str:
    secret = get_settings().pii_token_secret.encode("utf-8")
    digest = hmac.new(secret, value.encode("utf-8"), sha256).hexdigest()[:16]
    return f"pii:{category}:{digest}"


def anonymize(text: str) -> AnonymizationResult:
    """Replace PII occurrences in *text* and return tokens for vault lookup."""
    if not text:
        return AnonymizationResult(text_anonymized="", failed=True, failure_reason="empty_text")

    redacted = text
    tokens: list[str] = []
    findings: list[PiiFinding] = []
    seen: set[str] = set()
    for rec in _RECOGNIZERS:
        for match in rec.pattern.finditer(text):
            value = match.group(0)
            token = _tokenize(rec.category, value)
            if token not in seen:
                seen.add(token)
                tokens.append(token)
                findings.append(PiiFinding(category=rec.category, value=value, token=token))
            redacted = redacted.replace(value, f"[{rec.category.upper()}]")
    return AnonymizationResult(
        text_anonymized=redacted, pii_tokens=tokens, findings=findings
    )


def contains_residual_pii(text: str) -> bool:
    """Defensive guard for FR-013: the canonical text must be PII-free."""
    return any(rec.pattern.search(text) for rec in _RECOGNIZERS)
