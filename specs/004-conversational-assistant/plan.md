# Implementation Plan: Assistente Conversacional

**Branch:** `004-conversational-assistant` | **Date:** 2026-05-08
**Spec:** ./spec.md

## Summary

Camada conversacional para gestores, com RAG sobre a base operacional
(features 001 e 003), múltiplas camadas de guardrails (intenção,
clínico, prompt injection, output) e citação obrigatória de fontes.
LLM provider plugável; Grok no MVP, NIM on-prem no roadmap.

## Technical Context

- **Frontend:** Next.js 14 reutilizando layout do painel (feature 002),
  com novo módulo `(dashboard)/assistant/page.tsx` e componente
  `ChatPanel`; streaming de tokens via SSE.
- **Backend:** módulo `backend/src/nowgo_saude/assistant/` em
  FastAPI; LangGraph para orquestração; LlamaIndex para RAG sobre
  pgvector; reuso dos `guards` da feature 003.
- **Provider:** Grok (xAI) via `LLMProvider`; live search Grok
  permitido apenas para perguntas explicitamente sobre notícias públicas
  de saúde no DF, com citação obrigatória.
- **Auth/RBAC:** JWT stub no MVP; OIDC adapter pronto.
- **Storage:** ChatSession, ChatMessage, GuardDecision, CitationRef,
  AssistantRun em PostgreSQL; índices vetoriais pgvector.
- **Observabilidade:** OpenTelemetry semantic `gen-ai`; auditoria
  imutável reusando serviço da feature 001.
- **Testing:** pytest, pytest-asyncio, golden tests, testset de
  adversariais (prompt injection), Playwright para E2E.

## Constitution Check

| Princípio | Aderência |
|-----------|-----------|
| I. Soberania | Guardrails on-prem; egress só com prompt sanitizado |
| II. LGPD | Apenas dados pseudonimizados; recusa identificação |
| III. Guardrails | 4 camadas: intent, clinical, prompt-injection, output |
| IV. Não-Clínica | Filtro clínico in/out |
| V. Sensor | Chat consulta percepção pública |
| VI. Smart City | KPIs respondidos com referência |
| VII. Observabilidade | Spans gen-ai; auditoria por mensagem |
| VIII. Workflow | Spec → Plan → Tasks |
| IX. Segurança | RBAC; rate limit; sem leakage do system prompt |

## Project Structure

backend/src/nowgo_saude/assistant/
  api/                       # POST /chat, GET /sessions, /messages
  graphs/                    # LangGraph: input → guards → retrieve → generate → guards
  retrieval/                 # LlamaIndex sobre pgvector + filtros RBAC
  prompts/                   # versionados; system prompt hardcoded
  models/                    # ChatSession, ChatMessage, GuardDecision, CitationRef, AssistantRun

frontend/app/(dashboard)/assistant/
  page.tsx
  components/{ChatPanel,Message,Citations,SafetyBadge}.tsx
  lib/chat-stream.ts

## Phase 0: Research

1. RAG estratégia: chunking, embeddings (modelo embarcável vs. Grok
   embeddings), reranking.
2. Filtro RBAC em retrieval (segurança em depth).
3. Conjunto adversarial pt-BR para prompt injection (curadoria interna).
4. Detector clínico em pt-BR (classificador binário).
5. Estratégia de citação: identificadores estáveis e sanitizados.
6. UX de bloqueio amigável (sem leakage do system prompt).
7. Streaming SSE com guardrails de output incrementais.

## Phase 1: Design & Contracts

- `data-model.md`: ChatSession, ChatMessage, GuardDecision,
  CitationRef, AssistantRun.
- `contracts/assistant-api.openapi.yaml`: POST /chat (SSE),
  GET /sessions, GET /sessions/{id}/messages.
- `contracts/assistant-stream.md`: formato dos chunks SSE
  (token, citação, guard event, end-of-turn).
- `quickstart.md`: cenário ponta-a-ponta com RBAC e bloqueios.

## Phase 2: Task Planning Approach

/tasks vai produzir:
1. Setup do módulo assistant (back) e da página assistant (front).
2. Tests-first: contract de API/SSE, E2E dos cenários 1–6, adversariais
   de prompt injection, golden tests do system prompt.
3. Models e migrations.
4. Pipeline LangGraph (input guards → retrieval RBAC → generate →
   output guards → cite).
5. Endpoints + streaming.
6. Frontend ChatPanel com streaming, citações e badges de safety.
7. Wire egress_guard, OTel gen-ai, auditoria, rate limit.
8. Eval set automatizado para regressão de guardrails.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (vazio)   | -          | -                                    |

## Progress Tracking

- [x] Initial Constitution Check passed
