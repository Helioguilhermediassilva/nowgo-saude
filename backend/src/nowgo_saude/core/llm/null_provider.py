"""NullProvider — deterministic stand-in for tests and degraded mode.

Used in three places:

1. Unit tests that need an ``LLMProvider`` but must not hit the network.
2. The degraded-mode worker path (FR-034 of spec 003) when the real provider
   reports unhealthy or the egress guard trips.
3. Local dev environments where ``GROK_API_KEY`` is empty.

It returns an empty string by default; callers in degraded mode are expected
to layer their own heuristics on top of a ``NullProvider`` result rather than
relying on its text content.
"""

from __future__ import annotations

from typing import Any

from .provider import LLMProvider, LLMResponse


class NullProvider(LLMProvider):
    """Returns canned, deterministic responses without any network I/O."""

    name = "null"

    def __init__(self, *, canned_text: str = "") -> None:
        self._canned_text = canned_text

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        system: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            text=self._canned_text,
            provider=self.name,
            model="null-1.0",
            tokens_in=len(prompt.split()),
            tokens_out=len(self._canned_text.split()),
            latency_ms=0,
        )

    def health(self) -> bool:
        return True
