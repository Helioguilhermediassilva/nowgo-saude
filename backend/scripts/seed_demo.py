"""Idempotent demo seed for the Command Center Dashboard.

Generates synthetic telemetry events distributed across DF Regiões
Administrativas and a small set of CNES units, with attributes carrying
``ra_id``, ``ra_name``, ``unit_name``, optional ``wait_minutes`` and
``appointment_coverage_pct`` so the dashboard aggregations have signal.

Idempotency: every seeded event sets ``attributes.seed = "demo-v1"`` and
uses a deterministic ``external_id`` (``DEMO-{ra}-{unit}-{slot}``). Re-runs
are safe because the unique index ``(source_id, external_id)`` short-circuits
duplicates.

Usage:
    DATABASE_URL=postgresql+psycopg://… \
    ADMIN_TOKEN=… \
    python -m scripts.seed_demo --events 5000

Environment variables read by the FastAPI ``Settings`` (NOWGO_DATABASE_URL,
NOWGO_PII_TOKEN_SECRET, NOWGO_PII_VAULT_KEY, NOWGO_PII_VAULT_KEY_VERSION)
must be set when running outside the Cloud Run container.
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from nowgo_saude.dashboard.services.regions import DF_REGIONS
from nowgo_saude.db import SessionLocal, init_db
from nowgo_saude.models.source import Source
from nowgo_saude.models.telemetry_event import TelemetryEvent

SEED_TAG = "demo-v1"
SOURCE_SLUG = "ouvidor_sus_df"

UNITS = [
    ("2645238", "UPA Ceilândia", "RA-IX"),
    ("2658275", "Hospital Regional de Samambaia", "RA-XII"),
    ("9012345", "UBS 3 Sol Nascente", "RA-XXIX"),
    ("2645289", "Hospital Materno-Infantil de Brasília", "RA-I"),
    ("9007711", "UPA Recanto das Emas", "RA-XV"),
    ("2645301", "Hospital Regional de Taguatinga", "RA-III"),
    ("9011223", "UBS 2 Riacho Fundo", "RA-XVII"),
    ("2645320", "Hospital de Base", "RA-I"),
    ("9015544", "UBS 1 Águas Claras", "RA-XX"),
    ("2645445", "UPA São Sebastião", "RA-XIV"),
]

TOPIC_WEIGHTS = [
    ("fila", 0.32),
    ("atendimento", 0.21),
    ("medicamento", 0.15),
    ("agendamento", 0.13),
    ("infraestrutura", 0.10),
    ("outros", 0.09),
]

PHRASES = {
    "fila": "Fila longa para atendimento, sem informação sobre tempo de espera.",
    "atendimento": "Atendimento demorado, equipe parecia sobrecarregada.",
    "medicamento": "Medicamento em falta na unidade, precisei buscar em outra.",
    "agendamento": "Não conseguiu agendar consulta, sistema indisponível.",
    "infraestrutura": "Ar-condicionado não funciona, banheiro com problema.",
    "outros": "Comentário sobre o serviço prestado na unidade.",
}


def _ensure_source(session) -> Source:  # type: ignore[no-untyped-def]
    src = session.query(Source).filter(Source.slug == SOURCE_SLUG).one_or_none()
    if src:
        return src
    src = Source(
        slug=SOURCE_SLUG,
        kind="ouvidoria_oficial",
        display_name="OuvidorSUS DF",
        enabled=True,
        config={},
        retention_policy={"event_days": 365, "pii_days": 30, "raw_days": 7},
        iso_37120_default=["15.1", "15.4"],
    )
    session.add(src)
    session.commit()
    session.refresh(src)
    return src


def _pick_topic(rng: random.Random) -> str:
    r = rng.random()
    acc = 0.0
    for topic, w in TOPIC_WEIGHTS:
        acc += w
        if r <= acc:
            return topic
    return "outros"


def _purge_prior(session, source_id: int) -> int:  # type: ignore[no-untyped-def]
    """Delete previously seeded demo events so a refresh re-anchors timestamps."""
    deleted = (
        session.query(TelemetryEvent)
        .filter(
            TelemetryEvent.source_id == source_id,
            TelemetryEvent.external_id.like("DEMO-%"),
        )
        .delete(synchronize_session=False)
    )
    session.commit()
    return int(deleted)


def seed(*, events: int, hours_back: int, seed_value: int, refresh: bool = False) -> tuple[int, int, int]:
    rng = random.Random(seed_value)
    init_db()
    session = SessionLocal()
    try:
        source = _ensure_source(session)
        purged = _purge_prior(session, source.id) if refresh else 0
        now = datetime.now(UTC)
        inserted = skipped = 0
        # ~12% of events fall in the last 24h to simulate a moderate spike
        # over the daily baseline (~7.1% if traffic were uniform across the
        # 14-day horizon), giving 60-80% growth on a few hot units.
        recent_cut_seconds = 24 * 3600
        for i in range(events):
            if rng.random() < 0.12 and hours_back > 24:
                offset_seconds = rng.randint(0, recent_cut_seconds)
            else:
                offset_seconds = rng.randint(recent_cut_seconds, hours_back * 3600)
            received = now - timedelta(seconds=offset_seconds)
            unit_code, unit_name, ra_id = rng.choice(UNITS)
            ra = next((r for r in DF_REGIONS if r.ra_id == ra_id), DF_REGIONS[0])
            topic = _pick_topic(rng)
            sentiment = rng.choices([-2, -1, 0, 1], weights=[1, 4, 3, 1], k=1)[0]
            severity = rng.choices([0, 1, 2, 3], weights=[2, 4, 3, 1], k=1)[0]
            confidence = round(rng.uniform(0.62, 0.97), 3)
            attrs = {
                "seed": SEED_TAG,
                "ra_id": ra.ra_id,
                "ra_name": ra.name,
                "unit_name": unit_name,
                "channel": rng.choice(["web", "app", "telefone"]),
                "language": "pt-BR",
            }
            if topic == "fila":
                attrs["wait_minutes"] = rng.randint(15, 240)
            if topic == "agendamento":
                attrs["appointment_coverage_pct"] = round(rng.uniform(45, 92), 1)
            event = TelemetryEvent(
                source_id=source.id,
                external_id=f"DEMO-{ra.ra_id}-{unit_code}-{i}",
                received_at=received,
                occurred_at=received - timedelta(minutes=rng.randint(1, 90)),
                region_code="5300108",
                unit_code=unit_code,
                topic=topic,
                subtopic=None,
                sentiment=sentiment,
                severity=severity,
                confidence=confidence,
                text_anonymized=PHRASES[topic],
                pii_tokens=[],
                attributes=attrs,
                iso_37120=["15.1", "15.4"] if topic in ("fila", "atendimento") else ["15.1"],
                iso_37122=[],
                status="classified",
            )
            session.add(event)
            try:
                session.commit()
                inserted += 1
            except IntegrityError:
                session.rollback()
                skipped += 1
        return inserted, skipped, purged
    finally:
        session.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--events", type=int, default=6000)
    p.add_argument("--hours-back", type=int, default=336)  # 14 days
    p.add_argument("--seed", type=int, default=20260509)
    p.add_argument(
        "--refresh",
        action="store_true",
        help="Delete prior DEMO-* events before reseeding so timestamps re-anchor to now.",
    )
    args = p.parse_args()
    inserted, skipped, purged = seed(
        events=args.events,
        hours_back=args.hours_back,
        seed_value=args.seed,
        refresh=args.refresh,
    )
    print(f"seeded events: inserted={inserted} skipped={skipped} purged={purged}")


if __name__ == "__main__":
    main()
