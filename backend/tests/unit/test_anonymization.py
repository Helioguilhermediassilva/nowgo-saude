"""Unit tests for the regex-based PII anonymizer."""

from __future__ import annotations

from nowgo_saude.services.anonymization import (
    anonymize,
    contains_residual_pii,
)


def test_anonymizes_cpf_and_phone() -> None:
    text = "Meu CPF é 123.456.789-09 e telefone (61) 99999-1234, contato joao@example.com."
    result = anonymize(text)
    assert "123.456.789-09" not in result.text_anonymized
    assert "joao@example.com" not in result.text_anonymized
    categories = {token.split(":")[1] for token in result.pii_tokens}
    assert {"cpf", "phone", "email"}.issubset(categories)
    assert not contains_residual_pii(result.text_anonymized)


def test_returns_failure_for_empty_text() -> None:
    result = anonymize("")
    assert result.failed is True
    assert result.failure_reason == "empty_text"


def test_repeated_pii_collapses_to_single_token() -> None:
    text = "CPF 123.456.789-09 aparece duas vezes: 123.456.789-09."
    result = anonymize(text)
    cpf_tokens = [t for t in result.pii_tokens if t.startswith("pii:cpf:")]
    assert len(cpf_tokens) == 1


def test_text_without_pii_is_unchanged() -> None:
    text = "Cidadão relata atraso no atendimento na UBS."
    result = anonymize(text)
    assert result.text_anonymized == text
    assert result.pii_tokens == []
