"""egress_guard — last-mile check before any byte leaves the cluster (T042).

Two-layer enforcement of Constitution Principles I and II at the network
boundary:

1. **Hostname allowlist.** Outbound calls only proceed if the target is on
   ``settings.egress_allowlist``. Defense in depth against accidental
   exfiltration to typo'd hosts, hijacked DNS, or future regressions in
   provider adapters.
2. **PII residue check.** Even after the anonymization pipeline, every
   outbound payload is re-scanned with the same recognizers. A hit blocks
   the call — never leak raw PII to third-party APIs.

This module is intentionally pure: it raises on violation and the caller
decides whether to audit, retry, or fall back. Persisting an audit entry
requires a ``Session`` which not every caller has (workers, scheduled jobs);
callers that do have one wrap the call in a try/except and log via
``services.audit.record``.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


class EgressViolationError(RuntimeError):
    """Raised when ``egress_guard`` denies an outbound call.

    Inherits from ``RuntimeError`` (not ``LLMUnavailableError``) because
    violations are governance failures, not transient unavailability.
    Adapters MUST translate this to :class:`LLMUnavailableError` if they
    want callers to enter degraded mode rather than surface the violation.
    """

    def __init__(self, *, kind: str, detail: str, hostname: str | None = None) -> None:
        self.kind = kind
        self.detail = detail
        self.hostname = hostname
        super().__init__(f"egress denied [{kind}]: {detail}")


@dataclass(frozen=True)
class EgressDecision:
    """Pure outcome of an inspection — useful for tests and dry-run audits."""

    allowed: bool
    kind: str  # "allowed" | "host_not_allowed" | "pii_residue"
    detail: str
    hostname: str | None = None


def _resolve_hostname(target: str) -> str:
    """Accept a bare hostname or a full URL and return the hostname only."""
    if "://" in target:
        host = urlparse(target).hostname or ""
    else:
        host = target.split("/", 1)[0]
    return host.lower().strip()


def inspect(
    target: str,
    payload: str,
    *,
    allowlist: list[str],
) -> EgressDecision:
    """Pure inspection: returns a structured decision without raising.

    Used by callers that need to record the decision (allowed or denied)
    in an audit trail before acting on it. The runtime guard
    :func:`assert_safe` is a thin wrapper that raises on a denied decision.
    """
    host = _resolve_hostname(target)
    if not host:
        return EgressDecision(
            allowed=False,
            kind="host_not_allowed",
            detail="empty or unparseable target",
            hostname=None,
        )

    normalized_allow = {h.lower().strip() for h in allowlist}
    if host not in normalized_allow:
        return EgressDecision(
            allowed=False,
            kind="host_not_allowed",
            detail=f"{host!r} is not on the egress allowlist",
            hostname=host,
        )

    # Lazy import: avoids a circular dep with services/anonymization which
    # imports from config, and config does not need core/.
    from ...services.anonymization import contains_residual_pii

    if payload and contains_residual_pii(payload):
        return EgressDecision(
            allowed=False,
            kind="pii_residue",
            detail="payload still contains PII after anonymization",
            hostname=host,
        )

    return EgressDecision(allowed=True, kind="allowed", detail="ok", hostname=host)


def assert_safe(target: str, payload: str, *, allowlist: list[str] | None = None) -> None:
    """Inspect and raise :class:`EgressViolationError` on a denied decision.

    ``allowlist`` defaults to ``settings.egress_allowlist`` so most callers
    just pass ``(target, payload)``. Tests can inject an explicit list to
    avoid touching the global Settings cache.
    """
    if allowlist is None:
        # Local import for the same reason as above.
        from ...config import get_settings

        allowlist = get_settings().egress_allowlist

    decision = inspect(target, payload, allowlist=allowlist)
    if decision.allowed:
        return
    raise EgressViolationError(
        kind=decision.kind,
        detail=decision.detail,
        hostname=decision.hostname,
    )


__all__ = [
    "EgressDecision",
    "EgressViolationError",
    "assert_safe",
    "inspect",
]
