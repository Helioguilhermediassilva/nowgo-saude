# Tasks: Command Center Dashboard

**Input:** specs/002-command-center-dashboard/
**Prerequisites:** plan.md (✓), spec.md (✓), feature 001 base disponível.

## Path Conventions

- **Frontend:** `frontend/`
- **Backend dashboard module:** `backend/src/nowgo_saude/dashboard/`
- **Specs:** `specs/002-command-center-dashboard/`

---

## Phase 3.1: Setup

- [ ] **T001** Inicializar Next.js 14 (App Router, TS) em
  `frontend/` via `npx create-next-app@latest`.
- [ ] **T002** [P] Adicionar Tailwind CSS, shadcn/ui, Lucide-react,
  MapLibre GL, Recharts via `npm install`.
- [ ] **T003** [P] Configurar Playwright e Vitest no
  `frontend/` via `npm install -D @playwright/test vitest @testing-library/react`.
- [ ] **T004** [P] Configurar ESLint, Prettier e `.editorconfig`.
- [ ] **T005** Criar módulo backend `backend/src/nowgo_saude/dashboard/`
  com estrutura `api/`, `services/`, `rules/`,
  `notifications/`, `models/`.
- [ ] **T006** [P] Criar `frontend/lib/otel.ts` e wiring
  OpenTelemetry (browser + server) com exporter para o coletor local.

## Phase 3.2: Research & Design

- [ ] **T007** `research.md` resolvendo os 6 tópicos do plan §0.
- [ ] **T008** `data-model.md` (DashboardView, Widget, AlertRule,
  AlertEvent, KPIDefinition + materialized views).
- [ ] **T009** [P] `contracts/dashboard-api.openapi.yaml`
  (GET /kpis, /heatmap, /units/attention, /regions/{id}/details, /alerts;
  POST /alerts/rules).
- [ ] **T010** [P] `contracts/sse-stream.md` (formato dos eventos
  incrementais, heartbeats, reconexão).
- [ ] **T011** `quickstart.md` (cenário ponta-a-ponta com seed).
- [ ] **T012** Catálogo inicial de KPIs com mapeamento ISO 37120 §15,
  ITU-T Y.4900, IMD em
  `backend/src/nowgo_saude/dashboard/services/kpi_catalog.py`
  (apenas estrutura/metadado nesta task; implementação em 3.4).

## Phase 3.3: Tests First (TDD)

- [ ] **T013** [P] Contract test `GET /api/v1/dashboard/heatmap` em
  `backend/tests/contract/test_dashboard_heatmap.py`.
- [ ] **T014** [P] Contract test `GET /api/v1/dashboard/units/attention`
  em `backend/tests/contract/test_dashboard_attention.py`.
- [ ] **T015** [P] Contract test `GET /api/v1/dashboard/kpis` em
  `backend/tests/contract/test_dashboard_kpis.py`.
- [ ] **T016** [P] Contract test `POST /api/v1/dashboard/alerts/rules`
  em `backend/tests/contract/test_alerts_rules.py`.
- [ ] **T017** [P] E2E Playwright cenário 1 (mapa atualiza ≤ 60 s) em
  `frontend/tests/e2e/heatmap_freshness.spec.ts`.
- [ ] **T018** [P] E2E cenário 2 (unidade em atenção crítica destacada) em
  `frontend/tests/e2e/attention_unit.spec.ts`.
- [ ] **T019** [P] E2E cenário 3 (drill-down região → unidade → evento) em
  `frontend/tests/e2e/drilldown.spec.ts`.
- [ ] **T020** [P] E2E cenário 4 (alerta dispara notificação) em
  `frontend/tests/e2e/alert_rule.spec.ts`.
- [ ] **T021** [P] E2E cenário 5 (RBAC Diretor de Hospital) em
  `frontend/tests/e2e/rbac_director.spec.ts`.
- [ ] **T022** [P] E2E edge case (banner de degradação) em
  `frontend/tests/e2e/degraded_banner.spec.ts`.

## Phase 3.4: Core Implementation

- [ ] **T023** [P] Modelos DashboardView, Widget, AlertRule, AlertEvent,
  KPIDefinition em
  `backend/src/nowgo_saude/dashboard/models/`.
- [ ] **T024** Migrations Alembic + materialized views (heatmap_by_ra_15m,
  unit_attention_score, kpi_daily) em
  `backend/alembic/versions/0002_dashboard.py`.
- [ ] **T025** [P] Serviço de heatmap em
  `backend/src/nowgo_saude/dashboard/services/heatmap.py`.
- [ ] **T026** [P] Serviço de unidades em atenção em
  `backend/src/nowgo_saude/dashboard/services/attention.py`.
- [ ] **T027** [P] Serviço de KPIs (consome `kpi_catalog`) em
  `backend/src/nowgo_saude/dashboard/services/kpis.py`.
- [ ] **T028** Engine declarativa de AlertRule (JSON-Logic) em
  `backend/src/nowgo_saude/dashboard/rules/engine.py`.
- [ ] **T029** Worker periódico de avaliação de alertas em
  `workers/src/workers/alert_evaluator.py`.
- [ ] **T030** Notificadores (in-app, e-mail) em
  `backend/src/nowgo_saude/dashboard/notifications/`.
- [ ] **T031** Endpoints REST + SSE em
  `backend/src/nowgo_saude/dashboard/api/` (depende de T023–T028).
- [ ] **T032** [P] Layout principal e navegação Next.js em
  `frontend/app/(dashboard)/layout.tsx`.
- [ ] **T033** [P] Componente `HeatmapDF` em
  `frontend/components/map/HeatmapDF.tsx`.
- [ ] **T034** [P] Widgets KPI / Attention / TimeSeries / TopicDist em
  `frontend/components/widgets/`.
- [ ] **T035** Página principal do dashboard em
  `frontend/app/(dashboard)/page.tsx` (depende de T032–T034).
- [ ] **T036** Drill-down região e unidade em
  `frontend/app/(dashboard)/regions/[id]/page.tsx` e
  `frontend/app/(dashboard)/units/[id]/page.tsx`.
- [ ] **T037** Página de alertas em
  `frontend/app/(dashboard)/alerts/page.tsx`.
- [ ] **T038** Cliente SSE + reconexão em
  `frontend/lib/sse.ts`.

## Phase 3.5: Integration

- [ ] **T039** Adapter de auth (JWT stub agora; interface OIDC) em
  `frontend/app/api/auth/[...]/route.ts` e
  `frontend/lib/auth.ts`.
- [ ] **T040** Middleware RBAC por perfil (Secretário, Diretor,
  Analista) em `frontend/middleware.ts` e no backend dashboard.
- [ ] **T041** Banner de degradação consumindo `GET /pipeline/health`
  em `frontend/components/system/DegradedBanner.tsx`.
- [ ] **T042** Exportação PDF (WeasyPrint) e CSV streaming em
  `backend/src/nowgo_saude/dashboard/api/exports.py`.
- [ ] **T043** Auditoria de acessos e exportações via serviço da feature
  001 em `backend/src/nowgo_saude/dashboard/api/audit_hooks.py`.

## Phase 3.6: Polish

- [ ] **T044** [P] Testes unitários da engine de regras em
  `backend/tests/unit/test_alert_rules_engine.py`.
- [ ] **T045** [P] Testes unitários dos cálculos de KPI em
  `backend/tests/unit/test_kpis.py`.
- [ ] **T046** Validação de performance (p95 carga ≤ 2 s, update ≤ 500 ms,
  200 concorrentes) com Lighthouse + k6 em
  `frontend/tests/perf/`.
- [ ] **T047** Auditoria WCAG 2.1 AA com axe-core em
  `frontend/tests/a11y/`.
- [ ] **T048** [P] Atualizar `quickstart.md`.
- [ ] **T049** Post-Design Constitution Check em plan.md.

## Dependencies

- T001 → T002–T004; T005 antes do backend dashboard.
- T013–T022 (tests) DEVEM falhar antes de iniciar T023+.
- T023 antes de T024 e T031.
- T032–T034 antes de T035–T037.
- Phase 3.5 após Phase 3.4. Phase 3.6 ao final.

## Validation Checklist

- [ ] Cada endpoint de `dashboard-api.openapi.yaml` tem contract test.
- [ ] Cada cenário de aceitação tem E2E.
- [ ] Cada KPI publicado declara framework em metadado.
- [ ] Tasks [P] não compartilham arquivos.
