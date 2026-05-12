"""SQL aggregations powering the Command Center Dashboard.

These services run lightweight, real-time queries over ``telemetry_events``
and shape the results into the schemas consumed by the Next.js dashboard.

The MVP keeps things database-portable (SQLite + Postgres) by extracting
``ra_id`` / ``ra_name`` / ``unit_name`` from the ``attributes`` JSON column
in Python rather than via dialect-specific JSON operators. With the volumes
expected for the demo (≤ 100k rows in the 7-day window) this is fast enough
and avoids a migration to add denormalized columns.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ...models.telemetry_event import TelemetryEvent
from ..schemas import (
    AttentionUnitOut,
    RecentEventOut,
    RegionDetailOut,
    RegionPressureOut,
    TimeSeriesPointOut,
    TopicSliceOut,
    UnitDetailOut,
)
from .regions import DF_REGIONS, REGION_BY_ID

KNOWN_TOPICS: tuple[str, ...] = (
    "fila", "infraestrutura", "atendimento", "medicamento", "agendamento", "outros"
)


def _normalize_topic(topic: str) -> str:
    return topic if topic in KNOWN_TOPICS else "outros"


def _as_utc(dt: datetime) -> datetime:
    """SQLite drops timezone info — coerce naive timestamps to UTC."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


@dataclass
class _EventRow:
    received_at: datetime
    topic: str
    sentiment: int
    severity: int
    unit_code: str | None
    attributes: dict[str, Any]


def _load_events(session: Session, since: datetime) -> list[_EventRow]:
    rows = (
        session.query(
            TelemetryEvent.received_at,
            TelemetryEvent.topic,
            TelemetryEvent.sentiment,
            TelemetryEvent.severity,
            TelemetryEvent.unit_code,
            TelemetryEvent.attributes,
        )
        .filter(TelemetryEvent.status == "classified")
        .filter(TelemetryEvent.received_at >= since)
        .all()
    )
    return [_EventRow(_as_utc(r[0]), r[1], r[2], r[3], r[4], r[5]) for r in rows]


def heatmap_by_ra(session: Session) -> list[RegionPressureOut]:
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    prior_24h = now - timedelta(hours=48)
    events = _load_events(session, prior_24h)

    by_ra: dict[str, list[_EventRow]] = defaultdict(list)
    for ev in events:
        ra = ev.attributes.get("ra_id") if isinstance(ev.attributes, dict) else None
        if ra:
            by_ra[ra].append(ev)

    out: list[RegionPressureOut] = []
    for ra in DF_REGIONS:
        bucket = by_ra.get(ra.ra_id, [])
        recent = [e for e in bucket if e.received_at >= last_24h]
        prior = [e for e in bucket if e.received_at < last_24h]
        topic_counts: dict[str, int] = defaultdict(int)
        sev_sum = 0
        neg_count = 0
        for ev in recent:
            topic_counts[_normalize_topic(ev.topic)] += 1
            sev_sum += max(ev.severity, 0)
            if ev.sentiment <= -1:
                neg_count += 1
        top_topic = max(topic_counts.items(), key=lambda kv: kv[1])[0] if topic_counts else "outros"
        density = len(recent) / max(ra.population, 1) * 100_000
        score_raw = density * 0.6 + (sev_sum / max(len(recent), 1)) * 18 + (
            neg_count / max(len(recent), 1)
        ) * 25
        pressure = max(0, min(100, int(round(score_raw))))
        delta = len(recent) - len(prior)
        trend = "up" if delta > max(3, len(prior) * 0.15) else (
            "down" if delta < -max(3, len(prior) * 0.15) else "stable"
        )
        out.append(
            RegionPressureOut(
                ra_id=ra.ra_id,
                ra_name=ra.name,
                pressure_score=pressure,
                event_count=len(recent),
                top_topic=top_topic,  # type: ignore[arg-type]
                trend=trend,  # type: ignore[arg-type]
            )
        )
    return sorted(out, key=lambda r: r.pressure_score, reverse=True)


def topic_breakdown(session: Session) -> list[TopicSliceOut]:
    since = datetime.now(UTC) - timedelta(hours=24)
    events = _load_events(session, since)
    counts: dict[str, int] = defaultdict(int)
    for ev in events:
        counts[_normalize_topic(ev.topic)] += 1
    total = sum(counts.values()) or 1
    items = [
        TopicSliceOut(
            topic=t,  # type: ignore[arg-type]
            count=counts.get(t, 0),
            pct=round(counts.get(t, 0) / total * 1000) / 10,
        )
        for t in KNOWN_TOPICS
    ]
    return sorted(items, key=lambda s: s.count, reverse=True)


def time_series(session: Session, hours: int) -> list[TimeSeriesPointOut]:
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    since = now - timedelta(hours=hours)
    events = _load_events(session, since)
    buckets: dict[datetime, int] = defaultdict(int)
    for ev in events:
        bucket = ev.received_at.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        buckets[bucket] += 1
    out: list[TimeSeriesPointOut] = []
    for i in range(hours, -1, -1):
        ts = now - timedelta(hours=i)
        out.append(TimeSeriesPointOut(ts=ts, value=buckets.get(ts, 0)))
    return out


def region_detail(session: Session, ra_id: str) -> RegionDetailOut | None:
    """Drill-down aggregation scoped to a single Região Administrativa.

    Mirrors the heatmap math (24h window vs prior 24h) plus topic mix,
    hourly time series, and the units within the RA exhibiting attention
    signals. Returns ``None`` when ``ra_id`` does not exist in DF_REGIONS.
    """
    from .units import attention_units  # local import avoids cycles

    ra = REGION_BY_ID.get(ra_id)
    if ra is None:
        return None

    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    prior_24h = now - timedelta(hours=48)
    events = _load_events(session, prior_24h)
    ra_events = [
        ev for ev in events
        if isinstance(ev.attributes, dict) and ev.attributes.get("ra_id") == ra_id
    ]
    recent = [e for e in ra_events if e.received_at >= last_24h]
    prior = [e for e in ra_events if e.received_at < last_24h]

    topic_counts: dict[str, int] = defaultdict(int)
    sev_sum = 0
    neg_count = 0
    for ev in recent:
        topic_counts[_normalize_topic(ev.topic)] += 1
        sev_sum += max(ev.severity, 0)
        if ev.sentiment <= -1:
            neg_count += 1
    top_topic = (
        max(topic_counts.items(), key=lambda kv: kv[1])[0] if topic_counts else "outros"
    )
    total_recent = sum(topic_counts.values()) or 1
    topics = [
        TopicSliceOut(
            topic=t,  # type: ignore[arg-type]
            count=topic_counts.get(t, 0),
            pct=round(topic_counts.get(t, 0) / total_recent * 1000) / 10,
        )
        for t in KNOWN_TOPICS
    ]
    topics.sort(key=lambda s: s.count, reverse=True)

    density = len(recent) / max(ra.population, 1) * 100_000
    score_raw = density * 0.6 + (sev_sum / max(len(recent), 1)) * 18 + (
        neg_count / max(len(recent), 1)
    ) * 25
    pressure = max(0, min(100, int(round(score_raw))))
    delta = len(recent) - len(prior)
    trend = "up" if delta > max(3, len(prior) * 0.15) else (
        "down" if delta < -max(3, len(prior) * 0.15) else "stable"
    )

    buckets: dict[datetime, int] = defaultdict(int)
    for ev in recent:
        b = ev.received_at.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        buckets[b] += 1
    series: list[TimeSeriesPointOut] = []
    for i in range(24, -1, -1):
        ts = now - timedelta(hours=i)
        series.append(TimeSeriesPointOut(ts=ts, value=buckets.get(ts, 0)))

    units: list[AttentionUnitOut] = attention_units(session, limit=10, ra_id=ra_id)

    return RegionDetailOut(
        ra_id=ra.ra_id,
        ra_name=ra.name,
        population=ra.population,
        pressure_score=pressure,
        event_count_24h=len(recent),
        event_count_prev_24h=len(prior),
        top_topic=top_topic,  # type: ignore[arg-type]
        trend=trend,  # type: ignore[arg-type]
        topics=topics,
        timeseries=series,
        units=units,
    )


def _severity_for_score(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 80:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def unit_detail(session: Session, unit_id: str) -> UnitDetailOut | None:
    """Drill-down aggregation scoped to a single health unit.

    Loads up to 15 days of classified events for ``unit_id`` so we can
    compute the 24h vs 14d-baseline growth (matching ``attention_units``),
    the 7-day daily series, and a feed of the most recent anonymized
    events. Returns ``None`` when the unit has no events at all.
    """
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    prev_24h_start = now - timedelta(hours=48)
    week_start = now - timedelta(days=7)
    baseline_start = now - timedelta(days=15)

    rows = (
        session.query(
            TelemetryEvent.id,
            TelemetryEvent.received_at,
            TelemetryEvent.topic,
            TelemetryEvent.sentiment,
            TelemetryEvent.severity,
            TelemetryEvent.text_anonymized,
            TelemetryEvent.attributes,
        )
        .filter(TelemetryEvent.status == "classified")
        .filter(TelemetryEvent.unit_code == unit_id)
        .filter(TelemetryEvent.received_at >= baseline_start)
        .all()
    )
    if not rows:
        return None

    unit_name: str | None = None
    ra_name: str | None = None
    ra_id: str | None = None
    recent: list[tuple[datetime, str, int, int, str, str]] = []
    prev_window: list[datetime] = []
    baseline_window: list[datetime] = []
    week_events: list[tuple[datetime, str, int, int, str, str]] = []
    for ev_id, raw_ts, topic, sentiment, severity, text, attrs in rows:
        ts = _as_utc(raw_ts)
        attrs_dict = attrs if isinstance(attrs, dict) else {}
        if unit_name is None:
            unit_name = attrs_dict.get("unit_name") or f"Unidade {unit_id}"
            ra_name = attrs_dict.get("ra_name") or "Distrito Federal"
            ra_id = attrs_dict.get("ra_id") or ""
        record = (ts, _normalize_topic(topic), int(sentiment), int(severity), text or "", ev_id)
        if ts >= last_24h:
            recent.append(record)
        elif ts >= prev_24h_start:
            prev_window.append(ts)
        if ts >= week_start:
            week_events.append(record)
        if baseline_start <= ts < last_24h:
            baseline_window.append(ts)

    baseline_daily = max(len(baseline_window) / 14.0, 0.1)
    growth_pct = ((len(recent) - baseline_daily) / baseline_daily) * 100.0
    sev_sum = sum(max(s, 0) for _, _, _, s, _, _ in recent)
    neg = sum(1 for _, _, sent, _, _, _ in recent if sent <= -1)
    density = min(len(recent), 80)
    raw = (
        density * 0.6
        + (sev_sum / max(len(recent), 1)) * 14
        + min(max(growth_pct, 0), 120) * 0.25
        + (neg / max(len(recent), 1)) * 18
    )
    score = max(0, min(100, int(round(raw))))

    topic_counts: dict[str, int] = defaultdict(int)
    for _, t, _, _, _, _ in recent:
        topic_counts[t] += 1
    top_topic = (
        max(topic_counts.items(), key=lambda kv: kv[1])[0] if topic_counts else "outros"
    )
    total_recent = sum(topic_counts.values()) or 1
    topics = [
        TopicSliceOut(
            topic=t,  # type: ignore[arg-type]
            count=topic_counts.get(t, 0),
            pct=round(topic_counts.get(t, 0) / total_recent * 1000) / 10,
        )
        for t in KNOWN_TOPICS
    ]
    topics.sort(key=lambda s: s.count, reverse=True)

    day_buckets: dict[datetime, int] = defaultdict(int)
    for ts, *_ in week_events:
        bucket = ts.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        day_buckets[bucket] += 1
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    series: list[TimeSeriesPointOut] = []
    for i in range(6, -1, -1):
        ts = today - timedelta(days=i)
        series.append(TimeSeriesPointOut(ts=ts, value=day_buckets.get(ts, 0)))

    delta = len(recent) - len(prev_window)
    trend = "up" if delta > max(3, len(prev_window) * 0.15) else (
        "down" if delta < -max(3, len(prev_window) * 0.15) else "stable"
    )

    recent_sorted = sorted(week_events, key=lambda r: r[0], reverse=True)[:15]
    recent_events = [
        RecentEventOut(
            id=ev_id,
            received_at=ts,
            topic=t,  # type: ignore[arg-type]
            severity=sev,
            sentiment=sent,
            text=text,
        )
        for ts, t, sent, sev, text, ev_id in recent_sorted
    ]

    return UnitDetailOut(
        unit_id=unit_id,
        name=unit_name or f"Unidade {unit_id}",
        ra_id=ra_id or "",
        ra_name=ra_name or "Distrito Federal",
        attention_score=score,
        severity=_severity_for_score(score),  # type: ignore[arg-type]
        event_count_24h=len(recent),
        event_count_prev_24h=len(prev_window),
        event_count_7d=len(week_events),
        growth_pct=round(growth_pct, 1),
        top_topic=top_topic,  # type: ignore[arg-type]
        trend=trend,  # type: ignore[arg-type]
        topics=topics,
        timeseries=series,
        recent_events=recent_events,
    )
