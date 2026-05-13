"""Alert derivation from event clusters.

The MVP synthesises alerts from anomaly signals captured on heatmap +
attention-units services. A real Feature 003 worker will eventually persist
these into a dedicated ``alerts`` table; until then this gives the operator
useful, traceable items in production.

G2.4 introduces server-side filtering (severity/status/raId/topic) and
pagination so the dedicated `/alerts` page can render large windows
without overwhelming the UI.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..schemas import AlertEventList, AlertEventOut, AlertSeverityCounts
from .aggregations import heatmap_by_ra
from .units import attention_units


def _alert_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(f"{prefix}:{key}".encode(), usedforsecurity=False).hexdigest()
    return f"alert-{prefix}-{digest[:10]}"


def _derive_all(session: Session) -> list[AlertEventOut]:
    """Synthesize the full alert universe before filters/pagination.

    The internal attention-units sample size is capped so the in-memory
    pipeline stays bounded even if the DB grows.
    """
    now = datetime.now(UTC)
    out: list[AlertEventOut] = []

    for unit in attention_units(session, limit=50):
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
                ra_id=None,
                topic=None,
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
                ra_id=region.ra_id,
                topic=region.top_topic,
            )
        )

    out.sort(key=lambda a: a.triggered_at, reverse=True)
    return out


def _matches(
    alert: AlertEventOut,
    *,
    severities: set[str] | None,
    statuses: set[str] | None,
    ra_id: str | None,
    topic: str | None,
) -> bool:
    if severities is not None and alert.severity not in severities:
        return False
    if statuses is not None and alert.status not in statuses:
        return False
    if ra_id is not None and alert.ra_id != ra_id:
        return False
    if topic is not None and alert.topic != topic:
        return False
    return True


def _counts(alerts: Iterable[AlertEventOut]) -> AlertSeverityCounts:
    counts = AlertSeverityCounts()
    for a in alerts:
        if a.severity == "critical":
            counts.critical += 1
        elif a.severity == "high":
            counts.high += 1
        elif a.severity == "medium":
            counts.medium += 1
        elif a.severity == "low":
            counts.low += 1
    return counts


def list_alerts(
    session: Session,
    *,
    severities: list[str] | None = None,
    statuses: list[str] | None = None,
    ra_id: str | None = None,
    topic: str | None = None,
    limit: int = 12,
    offset: int = 0,
) -> AlertEventList:
    all_alerts = _derive_all(session)
    sev_set = set(severities) if severities else None
    st_set = set(statuses) if statuses else None

    filtered = [
        a for a in all_alerts
        if _matches(a, severities=sev_set, statuses=st_set, ra_id=ra_id, topic=topic)
    ]
    page = filtered[offset : offset + limit]
    return AlertEventList(
        items=page,
        total=len(filtered),
        limit=limit,
        offset=offset,
        severity_counts=_counts(filtered),
    )


def derive_alerts(session: Session, *, limit: int = 12) -> list[AlertEventOut]:
    """Backwards-compatible helper for dashboards that only need the top N."""
    return list_alerts(session, limit=limit).items
