"""LLMProvider — pluggable interface for language-model backends (T026).

Constitution Principle I requires that any LLM dependency be substitutable
without changes to domain code. Every consumer (classifier, anomaly detector,
recommender, assistant) types its dependency as ``LLMProvider`` and receives
the concrete implementation through the application factory.

The interface is intentionally minimal: a single ``complete`` call returning
a structured ``LLMResponse``. Streaming, embeddings and tool-use are not part
of the MVP contract and will be added as separate methods when needed, so
existing implementations keep working.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class LLMUnavailableError(RuntimeError):
    """Raised when the provider cannot serve a request.

    Callers treat this as a signal to fall back to the degraded mode
    (heuristics) declared in FR-034 of spec 003. The exception message MUST
    NOT carry user PII or upstream payloads — only the operational reason.
    """


@dataclass(frozen=True)
class LLMResponse:
    """Structured outcome of a completion call.

    ``provider`` and ``model`` are required for observability (Principle VII):
    every span must carry ``ai.provider`` and ``ai.model``. ``tokens_in`` /
    ``tokens_out`` enable cost monitoring (T041 of spec 003).
    """

    text: str
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Contract every concrete LLM backend must satisfy.

    Implementations are constructed once at app startup (or per-worker) and
    reused across requests. They MUST be safe to call from sync code; async
    variants will be added as ``acomplete`` later without breaking this
    interface.
    """

    #: Stable identifier used in audit trails and OTel attributes
    #: (e.g. ``"grok"``, ``"null"``, ``"nvidia-nim"``).
    name: str

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        system: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Synchronously produce a completion for ``prompt``.

        ``system`` is the domain-restricted system prompt required by
        Principle III (Purpose-Bound AI). ``metadata`` is opaque context the
        caller attaches for downstream auditing — implementations MUST NOT
        forward it to the upstream service.

        Implementations MUST raise :class:`LLMUnavailableError` on any
        condition that prevents a deterministic response (timeout, 5xx,
        egress block, rate limit). They MUST NOT raise raw HTTP errors.
        """

    @abstractmethod
    def health(self) -> bool:
        """Return ``True`` if the backend is reachable and serving.

        Used by ``/health`` probes and by the degraded-mode switch. MUST NOT
        raise: callers expect a boolean within a short timeout.
        """
