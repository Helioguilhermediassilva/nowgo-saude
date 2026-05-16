"""Shared verdict type returned by every guard.

Guards are pure functions: ``(text, *kwargs) -> GuardVerdict``. They never
mutate state, never raise on policy violations (only on programmer errors)
and never reach the network. This keeps them safe to compose, easy to fuzz
and trivial to audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GuardVerdict:
    """Outcome of a single guard evaluation.

    Attributes
    ----------
    allowed:
        ``True`` if the payload may proceed downstream. The semantics of
        "downstream" depends on the caller (forward to LLM, persist
        recommendation, surface to end-user, etc).
    reason:
        Machine-readable tag identifying *why* the guard rejected the
        payload. ``""`` when ``allowed=True``. Stable strings: callers
        rely on them for metrics/audit grouping.
    detail:
        Human-readable explanation safe to surface in audit logs. Never
        contains the offending substring verbatim \u2014 only the category and
        offset \u2014 so an audit dump cannot itself leak PII.
    matched_patterns:
        Tags of every pattern that fired. Useful when several heuristics
        catch the same payload; allows downstream tuning without re-running
        the guard.
    """

    allowed: bool
    reason: str = ""
    detail: str = ""
    matched_patterns: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def ok(cls) -> GuardVerdict:
        return cls(allowed=True)

    @classmethod
    def deny(
        cls, reason: str, detail: str = "", matched: tuple[str, ...] = ()
    ) -> GuardVerdict:
        return cls(allowed=False, reason=reason, detail=detail, matched_patterns=matched)
