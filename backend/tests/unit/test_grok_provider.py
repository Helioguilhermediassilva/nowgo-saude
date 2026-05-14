"""Unit tests for GrokProvider (T027).

Uses ``httpx.MockTransport`` to avoid any real network I/O. Validates:
- happy-path translation to LLMResponse,
- transport failures collapsed into LLMUnavailableError,
- egress_guard refusals translated into LLMUnavailableError,
- health probe never raises.
"""

from __future__ import annotations

import httpx
import pytest

from nowgo_saude.config import Settings
from nowgo_saude.core.llm import LLMResponse, LLMUnavailableError
from nowgo_saude.core.llm.grok_provider import GrokProvider


def _settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "grok_api_key": "test-key",
        "grok_base_url": "https://api.x.ai",
        "grok_model": "grok-2-latest",
        "egress_allowlist": ["api.x.ai"],
    }
    defaults.update(overrides)
    return Settings(**defaults)  # type: ignore[arg-type]


def _ok_response(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v1/chat/completions"
    return httpx.Response(
        200,
        json={
            "model": "grok-2-latest",
            "choices": [{"message": {"content": "fila_grande"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        },
    )


def test_complete_returns_llm_response_on_2xx() -> None:
    provider = GrokProvider(_settings(), transport=httpx.MockTransport(_ok_response))
    response = provider.complete("classify this complaint", system="you are triage")
    assert isinstance(response, LLMResponse)
    assert response.text == "fila_grande"
    assert response.provider == "grok"
    assert response.model == "grok-2-latest"
    assert response.tokens_in == 12
    assert response.tokens_out == 3


def test_constructor_raises_when_api_key_missing() -> None:
    with pytest.raises(LLMUnavailableError):
        GrokProvider(_settings(grok_api_key=""))


def test_5xx_collapsed_to_llm_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "upstream"})

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="upstream"):
        provider.complete("x")


def test_429_collapsed_to_llm_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate"})

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="rate limited"):
        provider.complete("x")


def test_4xx_collapsed_to_llm_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "bad request"})

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="client error 400"):
        provider.complete("x")


def test_timeout_collapsed_to_llm_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("simulated")

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="timed out"):
        provider.complete("x")


def test_malformed_payload_collapsed_to_llm_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": "shape"})

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="malformed"):
        provider.complete("x")


def test_egress_violation_for_host_outside_allowlist() -> None:
    """Base URL outside the allowlist must trip the guard before any HTTP call."""
    settings = _settings(grok_base_url="https://evil.example.com", egress_allowlist=["api.x.ai"])

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - never called
        raise AssertionError("HTTP call must not happen when egress is blocked")

    provider = GrokProvider(settings, transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="egress_guard denied"):
        provider.complete("x")


def test_egress_violation_for_pii_in_prompt() -> None:
    """PII residue in the prompt must be blocked before serialization."""

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("HTTP call must not happen when PII is detected")

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    with pytest.raises(LLMUnavailableError, match="egress_guard denied"):
        provider.complete("CPF do cidadão: 123.456.789-09")


def test_health_returns_true_on_2xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/models"
        return httpx.Response(200, json={"data": []})

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    assert provider.health() is True


def test_health_returns_false_on_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("nope")

    provider = GrokProvider(_settings(), transport=httpx.MockTransport(handler))
    assert provider.health() is False


def test_health_returns_false_when_host_not_allowlisted() -> None:
    settings = _settings(grok_base_url="https://evil.example.com")
    provider = GrokProvider(settings, transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    assert provider.health() is False
