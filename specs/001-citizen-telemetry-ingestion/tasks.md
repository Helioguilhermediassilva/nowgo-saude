# Tasks: Citizen Telemetry Ingestion

**Input:** specs/001-citizen-telemetry-ingestion/
**Prerequisites:** plan.md (✓), spec.md (✓). research.md, data-model.md,
contracts/, quickstart.md serão produzidos pelas tasks de Phase 0/1.

## Path Conventions

- **Backend:** `backend/src/nowgo_saude/`, `backend/tests/`
- **Workers:** `workers/src/workers/`, `workers/tests/`
- **Infra:** `infra/`
- **Specs:** `specs/001-citizen-telemetry-ingestion/`

---

## Phase 3.1: Setup

- [ ] **T001** Criar layout do monorepo conforme plan.md em
  `backend/`, `workers/`, `infra/`; adicionar
  `pyproject.toml` no backend usando Poetry.
- [ ] **T002** [P] Adicionar dependências backend via Poetry: `fastapi`,
  `uvicorn[standard]`, `pydantic>=2`,
  `sqlalchemy>=2`, `alembic`,
  `psycopg[binary]`, `celery`,
  `redis`, `httpx`, `presidio-analyzer`,
  `presidio-anonymizer`, `opentelemetry-distro`,
  `python-jose`, `pgvector`.
- [ ] **T003** [P] Adicionar dev-dependencies: `pytest`,
  `pytest-asyncio`, `testcontainers`,
  `ruff`, `mypy`, `pre-commit`.
- [ ] **T004** [P] Criar `infra/docker-compose.dev.yaml` com
  Postgres 16 + pgvector, Redis 7, MinIO, OTel Collector, Jaeger.
- [ ] **T005** [P] Configurar `.pre-commit-config.yaml`,
  `ruff.toml`, `mypy.ini` e `.editorconfig`.

## Phase 3.2: Research & Design (Phase 0/1 do plan)

- [ ] **T006** Produzir `specs/001-citizen-telemetry-ingestion/research.md`
  resolvendo os 6 tópicos do plan §Phase 0.
- [ ] **T007** Produzir `specs/001-citizen-telemetry-ingestion/data-model.md`
  com TelemetryEvent, Source, PIIVaultRecord, PipelineRun, AuditEntry.
- [ ] **T008** [P] Produzir `contracts/telemetry-event.schema.json`
  (JSON Schema do evento canônico).
- [ ] **T009** [P] Produzir `contracts/ingestion-api.openapi.yaml`
  com endpoints admin (sources, pipeline-runs, events:reprocess, metrics).
- [ ] **T010** Produzir `quickstart.md` com smoke test
  ponta-a-ponta usando coletores mock.

## Phase 3.3: Tests First (TDD) — MUST falhar antes de 3.4

- [ ] **T011** [P] Contract test do schema TelemetryEvent em
  `backend/tests/contract/test_telemetry_event_schema.py`.
- [ ] **T012** [P] Contract test `POST /api/v1/sources` em
  `backend/tests/contract/test_sources_api.py`.
- [ ] **T013** [P] Contract test `GET /api/v1/pipeline-runs` em
  `backend/tests/contract/test_pipeline_runs_api.py`.
- [ ] **T014** [P] Contract test `POST /api/v1/events:reprocess` em
  `backend/tests/contract/test_events_reprocess_api.py`.
- [ ] **T015** [P] Integration test cenário 1 (OuvidorSUS → evento
  classificado em ≤ 5 min) em
  `backend/tests/integration/test_ouvidoria_pipeline.py`.
- [ ] **T016** [P] Integration test cenário 2 (X/Twitter via Grok → evento
  marcado como fonte pública) em
  `backend/tests/integration/test_grok_x_pipeline.py`.
- [ ] **T017** [P] Integration test cenário 3 (PII pseudonimizada antes da
  persistência analítica) em
  `backend/tests/integration/test_anonymization_guarantee.py`.
- [ ] **T018** [P] Integration test cenário 4 (fonte indisponível → retry
  com backoff, sem perda) em
  `backend/tests/integration/test_source_unavailable.py`.
- [ ] **T019** [P] Integration test edge case: anonimização falha → evento
  em quarentena cifrada e alerta crítico, em
  `backend/tests/integration/test_anonymization_failure_quarantine.py`.

## Phase 3.4: Core Implementation (apenas após 3.3 falhando)

- [ ] **T020** [P] Modelo TelemetryEvent em
  `backend/src/nowgo_saude/models/telemetry_event.py`.
- [ ] **T021** [P] Modelo Source em
  `backend/src/nowgo_saude/models/source.py`.
- [ ] **T022** [P] Modelo PIIVaultRecord (schema segregado) em
  `backend/src/nowgo_saude/models/pii_vault.py`.
- [ ] **T023** [P] Modelo PipelineRun em
  `backend/src/nowgo_saude/models/pipeline_run.py`.
- [ ] **T024** [P] Modelo AuditEntry (append-only) em
  `backend/src/nowgo_saude/models/audit_entry.py`.
- [ ] **T025** Migrations Alembic iniciais em
  `backend/alembic/versions/0001_initial.py` (depende de T020–T024).
- [ ] **T026** [P] Interface `LLMProvider` em
  `backend/src/nowgo_saude/core/llm/provider.py`.
- [ ] **T027** Adapter Grok (xAI) em
  `backend/src/nowgo_saude/core/llm/grok_provider.py`
  (depende de T026).
- [ ] **T028** [P] Interface `AuthProvider` + JWT stub em
  `backend/src/nowgo_saude/core/auth/`.
- [ ] **T029** [P] Serviço de anonimização (PII detection +
  pseudonimização HMAC) em
  `backend/src/nowgo_saude/ingestion/anonymizer/service.py`.
- [ ] **T030** [P] Serviço de classificação operacional (região, unidade,
  tema, sentimento, gravidade) em
  `backend/src/nowgo_saude/ingestion/classifier/service.py`
  (consome `LLMProvider` pós-anonimização).
- [ ] **T031** [P] Serviço de auditoria imutável em
  `backend/src/nowgo_saude/core/audit/service.py`.
- [ ] **T032** [P] Coletor OuvidorSUS em
  `backend/src/nowgo_saude/ingestion/collectors/ouvidor_sus.py`.
- [ ] **T033** [P] Coletor GrokXSearch (X/Twitter via Grok) em
  `backend/src/nowgo_saude/ingestion/collectors/grok_x_search.py`.
- [ ] **T034** Orquestração Celery (cadeia coleta→anonimização→classificação)
  em `backend/src/nowgo_saude/ingestion/pipeline/tasks.py`
  (depende de T029–T033).
- [ ] **T035** DLQ + retry/backoff exponencial em
  `backend/src/nowgo_saude/ingestion/pipeline/retry.py`.
- [ ] **T036** Quarentena cifrada para falhas de anonimização em
  `backend/src/nowgo_saude/ingestion/pipeline/quarantine.py`.
- [ ] **T037** Endpoints admin (sources, pipeline-runs, events:reprocess,
  metrics) em `backend/src/nowgo_saude/ingestion/api/`
  (depende de T020–T028).
- [ ] **T038** Workers entrypoints em
  `workers/src/workers/` consumindo as tasks de T034.

## Phase 3.5: Integration

- [ ] **T039** Wire SQLAlchemy + Alembic ao app FastAPI em
  `backend/src/nowgo_saude/db.py`.
- [ ] **T040** Wire OpenTelemetry (traces, métricas, logs) em
  `backend/src/nowgo_saude/core/observability/otel.py`.
- [ ] **T041** Wire RBAC + JWT middleware em
  `backend/src/nowgo_saude/ingestion/api/middleware.py`.
- [ ] **T042** Wire egress controlado para API Grok (rate limit, allowlist
  de payloads pós-anonimização, circuit breaker) em
  `backend/src/nowgo_saude/core/llm/egress_guard.py`.
- [ ] **T043** Painel de métricas do pipeline (Prometheus exporter) em
  `backend/src/nowgo_saude/core/observability/metrics.py`.

## Phase 3.6: Polish

- [ ] **T044** [P] Testes unitários do anonymizer (cobertura ≥ 90%) em
  `backend/tests/unit/test_anonymizer.py`.
- [ ] **T045** [P] Testes unitários do classifier em
  `backend/tests/unit/test_classifier.py`.
- [ ] **T046** Validação de performance contra NFR-001/NFR-002 (script
  de carga com Locust) em `backend/tests/performance/load_ingestion.py`.
- [ ] **T047** [P] Atualizar `quickstart.md` com passos verificados.
- [ ] **T048** Revisão LGPD assinada (checklist anexado a
  `specs/001-citizen-telemetry-ingestion/lgpd-review.md`).
- [ ] **T049** Post-Design Constitution Check em plan.md (marcar item).

## Dependencies

- T001 antes de tudo.
- T002–T005 dependem de T001.
- T006–T010 (research/design) podem rodar em paralelo após T001.
- T011–T019 (tests) DEVEM falhar antes de iniciar T020+.
- T020–T024 antes de T025; T025 antes de T034 e T037.
- T026 antes de T027; T029–T030 antes de T034.
- T034 antes de T038.
- T037 depende de T020–T028.
- Phase 3.5 após Phase 3.4.
- Phase 3.6 ao final.

## Validation Checklist

- [ ] Todo contrato (T008, T009) tem teste correspondente (T011–T014).
- [ ] Toda entidade de data-model tem task de modelo (T020–T024).
- [ ] Todos os 4 cenários de aceitação têm integration test (T015–T018).
- [ ] Edge cases críticos cobertos (T019).
- [ ] Tasks [P] não tocam o mesmo arquivo.
- [ ] Cada task referencia caminho exato no monorepo.
