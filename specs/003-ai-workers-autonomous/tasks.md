# Tasks: AI Workers Autônomos

**Input:** specs/003-ai-workers-autonomous/
**Prerequisites:** plan.md (✓), spec.md (✓), feature 001 disponível
(modelos de evento, `LLMProvider`, `egress_guard`,
auditoria).

## Path Conventions

- **AI module:** `backend/src/nowgo_saude/ai/`
- **Workers:** `workers/src/workers/`
- **Specs:** `specs/003-ai-workers-autonomous/`

---

## Phase 3.1: Setup

- [ ] **T001** Criar módulo `backend/src/nowgo_saude/ai/` com
  subpastas `workers/`, `graphs/`, `prompts/`,
  `guards/`, `models/`, `feedback/`,
  `api/`.
- [ ] **T002** [P] Adicionar dependências via Poetry: `langgraph`,
  `llama-index`, `langchain-core`,
  `numpy`, `statsmodels`,
  `opentelemetry-instrumentation-langchain`.
- [ ] **T003** [P] Configurar pasta de prompts versionados em
  `backend/src/nowgo_saude/ai/prompts/` com convenção
  `<task>_v<n>.md` e changelog.
- [ ] **T004** [P] Configurar registro de modelos/versões em
  `backend/src/nowgo_saude/ai/registry.py`.

## Phase 3.2: Research & Design

- [ ] **T005** `research.md` resolvendo os 7 tópicos do plan §0.
- [ ] **T006** `data-model.md` (AnomalySignal, Recommendation,
  DailyBrief, WorkerRun, HumanDecision).
- [ ] **T007** [P] `contracts/ai-api.openapi.yaml` (GET /signals,
  /recommendations, /daily-brief/{date}; POST /recommendations/{id}/decision).
- [ ] **T008** [P] `contracts/worker-events.schema.json`.
- [ ] **T009** `quickstart.md` (seed → anomaly → recommendation
  → HITL → brief).

## Phase 3.3: Tests First (TDD)

- [ ] **T010** [P] Contract test `GET /api/v1/ai/signals` em
  `backend/tests/contract/test_ai_signals.py`.
- [ ] **T011** [P] Contract test `GET /api/v1/ai/recommendations`
  em `backend/tests/contract/test_ai_recommendations.py`.
- [ ] **T012** [P] Contract test `POST /api/v1/ai/recommendations/{id}/decision`
  em `backend/tests/contract/test_ai_decision.py`.
- [ ] **T013** [P] Contract test `GET /api/v1/ai/daily-brief/{date}`
  em `backend/tests/contract/test_ai_daily_brief.py`.
- [ ] **T014** [P] Integration test cenário 1 (anomaly detector cria
  AnomalySignal) em
  `backend/tests/integration/test_anomaly_detector.py`.
- [ ] **T015** [P] Integration test cenário 2 (recommender produz
  Recommendation com confidence e fontes) em
  `backend/tests/integration/test_recommender.py`.
- [ ] **T016** [P] Integration test cenário 3 (DailyBrief 07:00) em
  `backend/tests/integration/test_daily_briefer.py`.
- [ ] **T017** [P] Integration test cenário 4 (HumanDecision registra
  feedback) em
  `backend/tests/integration/test_human_decision.py`.
- [ ] **T018** [P] Integration test cenário 5 (classificação ambígua
  vai para triagem humana) em
  `backend/tests/integration/test_classifier_handoff.py`.
- [ ] **T019** [P] Edge: LLM externo indisponível → modo degradado em
  `backend/tests/integration/test_llm_failover.py`.
- [ ] **T020** [P] Edge: throttling de recomendações em
  `backend/tests/integration/test_recommendation_throttling.py`.
- [ ] **T021** [P] Edge: pedido implícito clínico → bloqueado em
  `backend/tests/integration/test_clinical_filter.py`.
- [ ] **T022** [P] Golden tests dos prompts (classifier, anomaly,
  recommender, briefer) em
  `backend/tests/golden/test_prompts.py`.
- [ ] **T023** [P] Teste anti prompt injection em
  `backend/tests/security/test_prompt_injection.py`.

## Phase 3.4: Core Implementation

- [ ] **T024** [P] Modelos AnomalySignal, Recommendation, DailyBrief,
  WorkerRun, HumanDecision em
  `backend/src/nowgo_saude/ai/models/`.
- [ ] **T025** Migrations Alembic em
  `backend/alembic/versions/0003_ai.py`.
- [ ] **T026** [P] Guard de intenção (escopo saúde pública) em
  `backend/src/nowgo_saude/ai/guards/intent.py`.
- [ ] **T027** [P] Guard clínico (bloqueia diagnóstico/prescrição) em
  `backend/src/nowgo_saude/ai/guards/clinical.py`.
- [ ] **T028** [P] Guard anti prompt injection em
  `backend/src/nowgo_saude/ai/guards/prompt_injection.py`.
- [ ] **T029** [P] Guard de output (sanitização final) em
  `backend/src/nowgo_saude/ai/guards/output_filter.py`.
- [ ] **T030** [P] Worker classifier (LangGraph) em
  `backend/src/nowgo_saude/ai/workers/classifier.py`
  com handoff para humano se confidence < limiar.
- [ ] **T031** [P] Worker anomaly_detector (z-score robusto + STL) em
  `backend/src/nowgo_saude/ai/workers/anomaly_detector.py`.
- [ ] **T032** [P] Worker recommender (LangGraph com retrieval em
  pgvector + live search Grok) em
  `backend/src/nowgo_saude/ai/workers/recommender.py`.
- [ ] **T033** [P] Worker daily_briefer em
  `backend/src/nowgo_saude/ai/workers/daily_briefer.py`.
- [ ] **T034** Modo degradado (heurísticas) ativado quando LLM indisponível
  em `backend/src/nowgo_saude/ai/workers/degraded_mode.py`.
- [ ] **T035** Endpoints AI (signals, recommendations, decision,
  daily-brief) em `backend/src/nowgo_saude/ai/api/`.
- [ ] **T036** Workers entrypoints em `workers/src/workers/`
  (`ai_classifier_worker`, `ai_anomaly_worker`,
  `ai_recommender_worker`, `ai_daily_brief_worker`).

## Phase 3.5: Integration

- [ ] **T037** Wire `egress_guard` (feature 001) para todas
  as chamadas Grok em
  `backend/src/nowgo_saude/ai/llm_client.py`.
- [ ] **T038** Wire OpenTelemetry semantic `gen-ai` em
  `backend/src/nowgo_saude/ai/observability.py`.
- [ ] **T039** Loop de feedback HumanDecision → registro estruturado em
  `backend/src/nowgo_saude/ai/feedback/loop.py`.
- [ ] **T040** Throttler global de recomendações em
  `backend/src/nowgo_saude/ai/throttling.py`.
- [ ] **T041** Cost monitor + budget alerts em
  `backend/src/nowgo_saude/ai/cost_monitor.py`.

## Phase 3.6: Polish

- [ ] **T042** [P] Unit tests dos guards em
  `backend/tests/unit/test_guards.py`.
- [ ] **T043** [P] Unit tests do anomaly_detector (matemática) em
  `backend/tests/unit/test_anomaly_math.py`.
- [ ] **T044** Validação de NFR-001 (latência ≤ 5 min p95) em
  `backend/tests/performance/test_ai_latency.py`.
- [ ] **T045** [P] Atualizar `quickstart.md`.
- [ ] **T046** Post-Design Constitution Check em plan.md.

## Dependencies

- T010–T023 (tests + golden) DEVEM falhar antes de T024+.
- T024 antes de T025; T025 antes de T035.
- T026–T029 (guards) antes de T030–T033 (workers).
- T030–T033 antes de T036 (entrypoints).
- T037 antes de qualquer chamada real ao Grok em produção.
- Phase 3.5 após Phase 3.4.

## Validation Checklist

- [ ] Cada endpoint AI tem contract test (T010–T013).
- [ ] Cada worker tem integration test e golden test.
- [ ] Cada guard tem unit test específico (T042).
- [ ] Detecção de prompt injection coberta (T023).
- [ ] Filtro clínico verificado (T021).
- [ ] HITL registrado e auditado (T017).
