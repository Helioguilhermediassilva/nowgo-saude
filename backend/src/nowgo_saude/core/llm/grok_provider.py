"""GrokProvider — concrete LLMProvider backed by xAI's Grok API (T027).

Wraps every outbound HTTP call with :func:`egress_guard.assert_safe`, so
Constitution Principles I (Sovereignty) and II (LGPD by Design) are enforced
at the boundary regardless of how callers compose the request.

The xAI API is OpenAI-compatible: ``POST {base_url}/v1/chat/completions``
with a ``messages`` array. We translate every transport-level failure
(timeout, 5xx, egress violation) into :class:`LLMUnavailableError` so
callers only have to handle one exception type when switching providers.

Tests inject an ``httpx.MockTransport`` via the ``transport`` constructor
arg — production code never passes it, so the real HTTP stack is used.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from ...config import Settings, get_settings
from .egress_guard import EgressViolationError, assert_safe
from .provider import LLMProvider, LLMResponse, LLMUnavailableError

_CHAT_PATH = "/v1/chat/completions"


class GrokProvider(LLMProvider):
    """xAI Grok adapter. Synchronous, single-shot completions."""

    name = "grok"

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        if not self._settings.grok_api_key:
            raise LLMUnavailableError("grok_api_key is not configured")

        self._model = self._settings.grok_model
        self._base_url = self._settings.grok_base_url.rstrip("/")
        self._timeout = self._settings.grok_timeout_seconds
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=transport,
            headers={
                "Authorization": f"Bearer {self._settings.grok_api_key}",
                "Content-Type": "application/json",
            },
        )

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        system: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        # Egress guard inspects the *outbound* text. Joining system+prompt
        # mirrors what httpx will serialize, so a PII residue in either is
        # caught before any byte leaves the process.
        outbound_text = "\n".join(m["content"] for m in messages)
        try:
            assert_safe(self._base_url, outbound_text, allowlist=self._settings.egress_allowlist)
        except EgressViolationError as exc:
            raise LLMUnavailableError(f"egress_guard denied call: {exc.kind}") from exc

        body = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        started = time.perf_counter()
        try:
            response = self._client.post(_CHAT_PATH, json=body)
        except httpx.TimeoutException as exc:
            raise LLMUnavailableError("grok request timed out") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"grok transport error: {type(exc).__name__}") from exc
        latency_ms = int((time.perf_counter() - started) * 1000)

        if response.status_code >= 500:
            raise LLMUnavailableError(f"grok upstream {response.status_code}")
        if response.status_code == 429:
            raise LLMUnavailableError("grok rate limited")
        if response.status_code >= 400:
            raise LLMUnavailableError(f"grok client error {response.status_code}")

        try:
            payload = response.json()
            choice = payload["choices"][0]
            text = choice["message"]["content"] or ""
            usage = payload.get("usage", {}) or {}
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailableError("grok returned malformed payload") from exc

        return LLMResponse(
            text=text,
            provider=self.name,
            model=payload.get("model", self._model),
            tokens_in=int(usage.get("prompt_tokens", 0)),
            tokens_out=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
        )

    def health(self) -> bool:
        """Best-effort probe: never raises.

        Returns ``True`` only when egress is permitted and the upstream
        responds to ``GET /v1/models`` with a 2xx within the configured
        timeout. Used by ``/health`` and the degraded-mode switch.
        """
        try:
            assert_safe(self._base_url, "", allowlist=self._settings.egress_allowlist)
        except EgressViolationError:
            return False
        try:
            r = self._client.get("/v1/models")
        except httpx.HTTPError:
            return False
        return 200 <= r.status_code < 300

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._client.close()


__all__ = ["GrokProvider"]
