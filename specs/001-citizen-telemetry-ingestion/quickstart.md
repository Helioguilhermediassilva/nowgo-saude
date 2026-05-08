# Quickstart: Citizen Telemetry Ingestion (Feature 001)

**Phase:** 1 (design) | **Date:** 2026-05-08

Smoke test ponta-a-ponta usando coletores mock (sem credencial externa).
Valida cenários de aceitação 1, 3 e 4 do `spec.md`.

## Pré-requisitos

- Docker / Docker Compose v2
- Python 3.11+ e Poetry 2.x
- Repositório clonado em `~/nowgo-saude`

## 1. Subir infraestrutura local

```bash
cd ~/nowgo-saude/infra/docker
docker compose -f docker-compose.dev.yaml up -d postgres redis minio otel-collector jaeger
docker compose -f docker-compose.dev.yaml ps
```

Esperado: 5 serviços com `healthy` (Postgres, Redis, MinIO) ou
`running` (otel-collector, Jaeger).

## 2. Instalar e migrar backend

```bash
cd ~/nowgo-saude/backend
poetry install
poetry run alembic upgrade head
```

Esperado: extensões `vector`, `pgcrypto`, `pg_trgm` criadas
(via `infra/docker/postgres/init/00-extensions.sql`); tabelas
`telemetry.sources`, `telemetry.telemetry_events`,
`pii_vault.pii_vault_records`, `telemetry.pipeline_runs`,
`audit.audit_entries` presentes.

## 3. Carregar fontes mock

```bash
poetry run python -m nowgo_saude.scripts.load_dev_sources
```

Cria 2 sources em modo dev:

- `ouvidor_sus_df` (`kind=ouvidoria_oficial`, fixture local)
- `grok_x_search` (`kind=social_publica`, adapter mock)

## 4. Iniciar API e workers

Em terminais separados:

```bash
# t1: API admin
poetry run uvicorn nowgo_saude.app:app --reload --port 8000

# t2: workers
cd ~/nowgo-saude/workers
poetry -C ../backend run celery -A workers.app worker -Q ingestion,anonymizer,classifier --concurrency=2 -l info

# t3: beat (agendador)
poetry -C ../backend run celery -A workers.app beat -l info
```

## 5. Cenário 1 — OuvidorSUS feliz path

```bash
curl -s http://localhost:8000/api/v1/sources | jq '.[].slug'
poetry run python -m nowgo_saude.scripts.trigger_run --source ouvidor_sus_df
```

Aguarde até 30 s. Em outro terminal:

```bash
curl -s http://localhost:8000/api/v1/pipeline-runs?source_slug=ouvidor_sus_df | jq
```

Critério de aceitação: `status=succeeded` e `events_collected >= 3`.
Validar evento canônico:

```bash
poetry run python -c "
from sqlalchemy import select
from nowgo_saude.db import session
from nowgo_saude.models import TelemetryEvent
with session() as s:
    e = s.scalars(select(TelemetryEvent).limit(1)).one()
    assert e.text_anonymized
    assert all(t.startswith('pii:') for t in (e.pii_tokens or []))
    assert e.confidence is not None
    print('OK', e.id, e.topic, e.severity)
"
```

## 6. Cenário 3 — anonimização garantida

```bash
poetry run pytest backend/tests/integration/test_anonymization_guarantee.py -q
```

Critério: 0 falhas. Verificação assert: `text_anonymized` não contém
CPF/CNS/email/telefone; tokens `pii:*` batem com `PIIVaultRecord`.

## 7. Cenário 4 — fonte indisponível

Pause o serviço da fonte e dispare:

```bash
poetry run python -m nowgo_saude.scripts.toggle_mock --source ouvidor_sus_df --offline
poetry run python -m nowgo_saude.scripts.trigger_run --source ouvidor_sus_df
```

Esperado: `pipeline_run.status=failed`, `error_summary` preenchido,
DLQ incrementada, retry agendado com backoff exponencial.
Releigando: `toggle_mock --online` e o próximo run termina em `succeeded`.

## 8. Observabilidade

- Jaeger UI: http://localhost:16686 — procurar serviço `nowgo-saude-backend`.
- Métricas Prometheus do collector: http://localhost:8889/metrics
  (`nowgo_saude_*` counters/histograms).
- Auditoria: `select * from audit.audit_entries order by at desc limit 20;`
  deve mostrar `egress.grok` (cenário Grok), `event.classify` e nenhum
  `pii.reidentify` (não acionado neste smoke).

## 9. Limpeza

```bash
cd ~/nowgo-saude/infra/docker
docker compose -f docker-compose.dev.yaml down -v
```

## Critérios consolidados de smoke

| Cenário | Critério | Origem |
|---------|----------|--------|
| 1 | OuvidorSUS produz ≥ 3 eventos classificados em ≤ 30 s | spec §AC-1 |
| 3 | `text_anonymized` sem PII; tokens reversíveis no Vault | spec §AC-3 |
| 4 | Fonte offline gera retry e `error_summary` sem perda | spec §AC-4 |
| OTel | Trace ponta-a-ponta da requisição até worker visível em Jaeger | constitution §VII |
| Audit | Cadeia hash íntegra (`prev_hash` confere) | constitution §VII |
