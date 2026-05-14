"""Unit tests for the LLMProvider contract and NullProvider (T026)."""

from __future__ import annotations

import pytest

from nowgo_saude.core.llm import (
    LLMProvider,
    LLMResponse,
    LLMUnavailableError,
    NullProvider,
)


def test_llm_provider_is_abstract() -> None:
    """Cannot instantiate the bare interface — callers must use a concrete impl."""
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_null_provider_returns_empty_text_by_default() -> None:
    provider = NullProvider()
    response = provider.complete("classify this complaint")
    assert isinstance(response, LLMResponse)
    assert response.text == ""
    assert response.provider == "null"
    assert response.model == "null-1.0"


def test_null_provider_returns_canned_text_when_configured() -> None:
    provider = NullProvider(canned_text="fila_grande")
    response = provider.complete("any prompt")
    assert response.text == "fila_grande"
    assert response.tokens_out == 1  # split() == ["fila_grande"]


def test_null_provider_counts_input_tokens_as_words() -> None:
    provider = NullProvider()
    response = provider.complete("um dois tres quatro")
    assert response.tokens_in == 4


def test_null_provider_health_always_true() -> None:
    assert NullProvider().health() is True


def test_null_provider_ignores_system_and_metadata() -> None:
    """Sanity: optional kwargs are accepted but do not affect output (FR-008)."""
    provider = NullProvider(canned_text="ok")
    r1 = provider.complete("x")
    r2 = provider.complete(
        "x",
        system="you are a triage assistant",
        metadata={"trace_id": "abc"},
        temperature=0.0,
        max_tokens=10,
    )
    assert r1.text == r2.text == "ok"


def test_llm_unavailable_is_runtime_error() -> None:
    """Callers catch RuntimeError for the broadest fallback path."""
    assert issubclass(LLMUnavailableError, RuntimeError)


def test_llm_response_is_immutable() -> None:
    """frozen=True makes accidental mutation of audit data impossible."""
    response = NullProvider().complete("x")
    with pytest.raises((AttributeError, Exception)):
        response.text = "tampered"  # type: ignore[misc]
