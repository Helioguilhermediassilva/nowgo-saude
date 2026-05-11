"""Alert derivation from event clusters.

The MVP synthesises alerts from anomaly signals captured on heatmap +
attention-units services. A real Feature 003 worker will eventually persist
these into a dedicated ``alerts`` table; until then this gives the operator
useful, traceable items in production.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..schemas import AlertEventOut
from .aggregations import heatmap_by_ra
from .units import attention_units


def _alert_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(f"{prefix}:{key}".encode("utf-8"), usedforsecurity=False).hexdigest()
    return f"alert-{prefix}-{digest[:10]}"


def derive_alerts(session: Session, *, limit: int = 12) -> list[AlertEventOut]:
    now = datetime.now(UTC)
    out: list[AlertEventOut] = []

    for unit in attention_units(session, limit=limit):
        if unit.attention_score < 75:
            continue
        out.append(
            AlertEventOut(
                id=_alert_id("unit", unit.unit_id),
                rule_name=f"Anomalia operacional ({unit.name})",
                severity=unit.severity,
                triggered_at=now - timedelta(minutes=int(60 - min(unit.attention_score, 60))),
                scope=unit.name,
                message=unit.reason,
                status="open",
            )
        )

    for region in heatmap_by_ra(session):
        if region.pressure_score < 70 or region.event_count < 10:
            continue
        sev = (
            "critical" if region.pressure_score >= 88
            else "high" if region.pressure_score >= 78
            else "medium"
        )
        out.append(
            AlertEventOut(
                id=_alert_id("ra", region.ra_id),
                rule_name=f"Pressão sustentada ({region.ra_name})",
                severity=sev,  # type: ignore[arg-type]
                triggered_at=now - timedelta(minutes=int(120 - min(region.pressure_score, 120))),
                scope=f"RA {region.ra_name}",
                message=(
                    f"Score de pressão {region.pressure_score} com {region.event_count} eventos "
                    f"(top: {region.top_topic})"
                ),
                status="open" if region.pressure_score >= 80 else "acknowledged",
            )
        )

    out.sort(key=lambda a: a.triggered_at, reverse=True)
    return out[:limit]
