# Implementation Plan: Command Center Dashboard

**Branch:** `002-command-center-dashboard` | **Date:** 2026-05-08
**Spec:** ./spec.md

## Summary

Aplicação web Next.js consumindo APIs do backend FastAPI (feature 001) e
do serviço de KPIs/alertas. Renderiza heatmaps geográficos do DF,
listas de atenção crítica, séries temporais e KPIs Smart City. Suporta
RBAC por perfil e exportação. Integração de notificações (in-app, e-mail).

## Technical Context

- **Language/Runtime:** TypeScript 5, Node 20.
- **Frontend Framework:** Next.js 14 (App Router), React 18, Tailwind CSS,
  shadcn/ui. Mapas com MapLibre GL + tiles próprios; visualizações com
  Recharts/visx.
- **Backend (read API + alertas):** FastAPI módulo `nowgo_saude.dashboard`
  reusando models e auth da feature 001.
- **Storage:** materialized views agregadas em PostgreSQL; Redis para
  caching de respostas hot.
- **Auth:** JWT stub (MVP) compartilhado com feature 001; OIDC adapter
  pronto para gov.br/AD-GDF.
- **Real-time:** Server-Sent Events (SSE) para atualizações incrementais.
- **Testing:** Vitest + React Testing Library; Playwright para E2E;
  pytest para o módulo backend.
- **Performance Goals:** carga inicial p95 ≤ 2 s, atualização ≤ 500 ms,
  200 usuários concorrentes.
- **Constraints:** WCAG 2.1 AA; on-prem; sem CDN externa para assets
  sensíveis.

## Constitution Check

| Princípio | Aderência |
|-----------|-----------|
| I. Soberania | Frontend e backend on-prem; mapas com tiles locais |
| II. LGPD | Drill-down expõe apenas pseudônimos; auditoria de acessos |
| III. Guardrails | Sem entrada de IA aberta nesta feature |
| IV. Não-Clínica | Indicadores estritamente operacionais |
| V. Cidadão como Sensor | Heatmap de percepção pública é o widget central |
| VI. Smart City | KPIs declaram framework em metadado |
| VII. Observabilidade | OTel front + back; auditoria de exportações |
| VIII. Workflow | Spec → Plan → Tasks |
| IX. Segurança | RBAC; CSP estrita; CSRF; exportações auditadas |

## Project Structure

frontend/
  app/                       # Next.js App Router
    (dashboard)/             # rotas autenticadas
      page.tsx               # painel principal
      regions/[id]/page.tsx
      units/[id]/page.tsx
      alerts/page.tsx
    api/auth/[...]/route.ts  # adapter OIDC (stub JWT no MVP)
  components/
    map/HeatmapDF.tsx
    widgets/{KPI,Attention,TimeSeries,TopicDist}.tsx
  lib/{api,auth,rbac,otel}.ts
  tests/{unit,e2e}/

backend/
  src/nowgo_saude/dashboard/
    api/                     # GET /kpis, /heatmap, /units, /alerts
    services/                # agregadores e cálculo de KPIs
    rules/                   # AlertRule engine
    notifications/           # email + in-app
    models/                  # DashboardView, Widget, AlertRule, AlertEvent, KPIDefinition

## Phase 0: Research

1. Tiles do DF: usar dados da Codeplan/IBGE; gerar tiles MBTiles servidos
   localmente.
2. Estratégia de materialized views para heatmap e listas de atenção,
   refresh incremental.
3. Engine de regras de alerta: declarativo (JSON-Logic) vs. expression
   language.
4. Catálogo inicial de KPIs com mapeamento ISO 37120 §15, ITU-T Y.4900,
   IMD Smart City Index.
5. Estratégia de SSE vs. WebSocket para atualizações incrementais.
6. Padrão de exportação PDF (server-side com WeasyPrint) e CSV streaming.

## Phase 1: Design & Contracts

- `data-model.md`: DashboardView, Widget, AlertRule, AlertEvent,
  KPIDefinition; views materializadas e índices.
- `contracts/dashboard-api.openapi.yaml`: GET /kpis, /heatmap,
  /units/attention, /regions/{id}/details, /alerts, POST /alerts/rules.
- `contracts/sse-stream.md`: contrato dos eventos incrementais.
- `quickstart.md`: cenário ponta-a-ponta com seed de eventos.
- Contract tests (failing).

## Phase 2: Task Planning Approach

/tasks vai derivar:
1. Setup Next.js + Tailwind + shadcn/ui + Playwright; setup módulo backend.
2. Tests-first: contract tests da API; E2E dos cenários 1–5.
3. Models e materialized views; KPIDefinition seed.
4. Endpoints (heatmap, atenção, detalhes, alertas).
5. Engine de AlertRule + worker de avaliação periódica.
6. Frontend: layout, map, widgets, drill-down, alertas, exportação.
7. RBAC e auditoria; banner de degradação.
8. Performance e a11y (WCAG 2.1 AA).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (vazio)   | -          | -                                    |

## Progress Tracking

- [ ] Phase 0/1/2 itens
- [x] Initial Constitution Check passed
