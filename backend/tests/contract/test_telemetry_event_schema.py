"""TelemetryEvent JSON Schema contract tests."""

from __future__ import annotations

from typing import Any

import pytest
from jsonschema import Draft202012Validator


def test_schema_is_valid(telemetry_event_schema: dict[str, Any]) -> None:
    Draft202012Validator.check_schema(telemetry_event_schema)


def test_valid_event_passes_schema(
    telemetry_event_schema: dict[str, Any],
    valid_telemetry_event: dict[str, Any],
) -> None:
    Draft202012Validator(telemetry_event_schema).validate(valid_telemetry_event)


@pytest.mark.parametrize(
    "mutator",
    [
        lambda e: e.pop("text_anonymized"),
        lambda e: e.update({"sentiment": 5}),
        lambda e: e.update({"severity": -1}),
        lambda e: e.update({"confidence": 1.5}),
        lambda e: e.update({"region_code": "abc"}),
        lambda e: e.update({"source_slug": "Has Spaces"}),
        lambda e: e.update({"status": "weird"}),
        lambda e: e.update({"iso_37120": ["16.1"]}),
    ],
)
def test_invalid_payloads_fail_schema(
    telemetry_event_schema: dict[str, Any],
    valid_telemetry_event: dict[str, Any],
    mutator,
) -> None:
    payload = dict(valid_telemetry_event)
    mutator(payload)
    validator = Draft202012Validator(telemetry_event_schema)
    errors = list(validator.iter_errors(payload))
    assert errors, "expected validation errors but payload was accepted"
