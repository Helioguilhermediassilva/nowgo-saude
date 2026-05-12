"""Attention-units detection.

Surfaces health units (UPA/UBS/Hospital) showing anomalous growth in citizen
complaints over the last 24h vs a 14-day baseline. Reasons and severity are
derived from the event mix; the dashboard renders the top-N units sorted by
attention score.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ...models.telemetry_event import TelemetryEvent
from ..schemas import AttentionUnitOut
from .aggregations import _as_utc

_REASON_TEMPLATES: dict[str, str] = {
    "fila": "Crescimento de {growth}% em queixas de fila vs média 14d",
    "medicamento": "Anomalia em reclamações de medicamento (+{growth}% vs baseline)",
    "atendimento": "Picos consecutivos de atendimento p95 acima do baseline",
    "infraestrutura": "Aumento de menções a infraestrutura precária (+{growth}%)",
    "agendamento": "Crescimento em queixas de agendamento (+{growth}%)",
    "outros": "Pressão sustentada acima do baseline (+{growth}%)",
}


def _severity(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 80:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def attention_units(
    session: Session, *, limit: int = 12, ra_id: str | None = None
) -> list[AttentionUnitOut]:
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    baseline_start = now - timedelta(days=15)
    baseline_end = last_24h

    rows = (
        session.query(
            TelemetryEvent.unit_code,
            TelemetryEvent.received_at,
            TelemetryEvent.topic,
            TelemetryEvent.severity,
            TelemetryEvent.sentiment,
            TelemetryEvent.attributes,
        )
        .filter(TelemetryEvent.status == "classified")
        .filter(TelemetryEvent.received_at >= baseline_start)
        .filter(TelemetryEvent.unit_code.is_not(None))
        .all()
    )

    by_unit: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"recent": [], "baseline": [], "name": None, "ra": None}
    )
    for unit_code, received_raw, topic, severity, sentiment, attrs in rows:
        attrs_dict = attrs if isinstance(attrs, dict) else {}
        if ra_id is not None and attrs_dict.get("ra_id") != ra_id:
            continue
        received = _as_utc(received_raw)
        bucket = by_unit[unit_code]
        if not bucket["name"]:
            bucket["name"] = attrs_dict.get("unit_name") or f"Unidade {unit_code}"
            bucket["ra"] = attrs_dict.get("ra_name") or "Distrito Federal"
        record = (received, topic, severity, sentiment)
        if received >= last_24h:
            bucket["recent"].append(record)
        elif baseline_end > received >= baseline_start:
            bucket["baseline"].append(record)

    out: list[AttentionUnitOut] = []
    for unit_code, b in by_unit.items():
        recent = b["recent"]
        baseline = b["baseline"]
        if len(recent) < 3:
            continue
        baseline_daily = max(len(baseline) / 14.0, 0.1)
        growth_pct = ((len(recent) - baseline_daily) / baseline_daily) * 100.0
        if growth_pct < 20:
            continue
        sev_sum = sum(max(s, 0) for _, _, s, _ in recent)
        neg = sum(1 for *_, sent in recent if sent <= -1)
        density = min(len(recent), 80)
        raw = density * 0.6 + (sev_sum / max(len(recent), 1)) * 14 + min(growth_pct, 120) * 0.25 + (
            neg / max(len(recent), 1)
        ) * 18
        score = max(0, min(100, round(raw)))
        topic_counts: dict[str, int] = defaultdict(int)
        for _, t, _, _ in recent:
            topic_counts[t] += 1
        top_topic = max(topic_counts.items(), key=lambda kv: kv[1])[0]
        reason_template = _REASON_TEMPLATES.get(top_topic, _REASON_TEMPLATES["outros"])
        reason = reason_template.format(growth=round(growth_pct))
        out.append(
            AttentionUnitOut(
                unit_id=unit_code,
                name=b["name"],
                ra_name=b["ra"],
                attention_score=score,
                severity=_severity(score),  # type: ignore[arg-type]
                reason=reason,
                growth_pct=round(growth_pct, 1),
                event_count_24h=len(recent),
            )
        )
    out.sort(key=lambda u: u.attention_score, reverse=True)
    return out[:limit]
