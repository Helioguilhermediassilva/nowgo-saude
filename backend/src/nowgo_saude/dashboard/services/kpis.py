"""Smart-City KPI catalog and live calculations.

Each KPI carries the international framework + clause it traces to
(ISO 37120 / ITU-T Y.4900 / IMD), per Constitution Principle VI and
spec FR-009. Live values are derived from ``telemetry_events`` over the
last 24h, with a delta against the prior 24h.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ...models.telemetry_event import TelemetryEvent
from ..schemas import KPIOut, SmartCityFramework
from .aggregations import _as_utc
from .regions import DF_TOTAL_POPULATION


@dataclass(frozen=True)
class _KpiSpec:
    id: str
    name: str
    unit: str
    framework: SmartCityFramework
    reference: str
    source: str


_CATALOG: tuple[_KpiSpec, ...] = (
    _KpiSpec(
        id="kpi.queue.wait_p95",
        name="Tempo de espera p95 (UPAs)",
        unit="min",
        framework="ISO 37120",
        reference="ISO 37120 §15.4 — tempo médio de atendimento",
        source="OuvidorSUS + sensores operacionais",
    ),
    _KpiSpec(
        id="kpi.complaint.rate_24h",
        name="Reclamações por 100k hab. (24h)",
        unit="/100k",
        framework="IMD Smart City",
        reference="IMD §Saúde — percepção do residente",
        source="OuvidorSUS + X/Twitter",
    ),
    _KpiSpec(
        id="kpi.coverage.appointment",
        name="Cobertura de agendamento (semana)",
        unit="%",
        framework="ITU-T Y.4900",
        reference="ITU-T Y.4900 §7.2 — eficácia do serviço",
        source="Pipeline operacional",
    ),
    _KpiSpec(
        id="kpi.unit.attention_count",
        name="Unidades em atenção crítica",
        unit="unid.",
        framework="ISO 37120",
        reference="ISO 37120 §15.5 — leitos disponíveis",
        source="Worker de anomalias",
    ),
)


def _delta_pct(current: float, prior: float) -> float | None:
    if prior <= 0:
        return None
    return round((current - prior) / prior * 100.0, 1)


def compute_kpis(session: Session) -> list[KPIOut]:
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    prior_24h = now - timedelta(hours=48)

    rows_raw = (
        session.query(
            TelemetryEvent.received_at,
            TelemetryEvent.topic,
            TelemetryEvent.severity,
            TelemetryEvent.unit_code,
            TelemetryEvent.attributes,
        )
        .filter(TelemetryEvent.status == "classified")
        .filter(TelemetryEvent.received_at >= prior_24h)
        .all()
    )
    rows = [(_as_utc(r[0]), r[1], r[2], r[3], r[4]) for r in rows_raw]
    recent = [r for r in rows if r[0] >= last_24h]
    prior = [r for r in rows if r[0] < last_24h]

    queue_p95_recent = _wait_p95(recent)
    queue_p95_prior = _wait_p95(prior)
    rate_recent = len(recent) / max(DF_TOTAL_POPULATION, 1) * 100_000
    rate_prior = len(prior) / max(DF_TOTAL_POPULATION, 1) * 100_000
    coverage_recent = _coverage(recent)
    coverage_prior = _coverage(prior)
    attention_count_recent = _attention_count(recent)
    attention_count_prior = _attention_count(prior)

    values: dict[str, tuple[float, float]] = {
        "kpi.queue.wait_p95": (queue_p95_recent, queue_p95_prior),
        "kpi.complaint.rate_24h": (round(rate_recent, 1), rate_prior),
        "kpi.coverage.appointment": (coverage_recent, coverage_prior),
        "kpi.unit.attention_count": (float(attention_count_recent), float(attention_count_prior)),
    }

    out: list[KPIOut] = []
    for spec in _CATALOG:
        cur, prv = values[spec.id]
        out.append(
            KPIOut(
                id=spec.id,
                name=spec.name,
                value=cur,
                unit=spec.unit,
                delta=_delta_pct(cur, prv),
                framework=spec.framework,
                reference=spec.reference,
                source=spec.source,
                updated_at=now,
            )
        )
    return out


def _wait_p95(rows: list) -> float:
    waits = [
        (a or {}).get("wait_minutes")
        for *_, a in rows
        if isinstance(a, dict) and isinstance(a.get("wait_minutes"), (int, float))
    ]
    if not waits:
        return 0.0
    waits.sort()
    idx = max(0, min(len(waits) - 1, int(round(0.95 * (len(waits) - 1)))))
    return float(waits[idx])


def _coverage(rows: list) -> float:
    samples = [
        (a or {}).get("appointment_coverage_pct")
        for *_, a in rows
        if isinstance(a, dict) and isinstance(a.get("appointment_coverage_pct"), (int, float))
    ]
    if not samples:
        return 0.0
    return round(sum(samples) / len(samples), 1)


def _attention_count(rows: list) -> int:
    by_unit: dict[str, int] = defaultdict(int)
    for _, _, sev, unit, _ in rows:
        if unit and sev >= 2:
            by_unit[unit] += 1
    return sum(1 for v in by_unit.values() if v >= 5)
