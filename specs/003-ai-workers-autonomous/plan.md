# Implementation Plan: AI Workers Autônomos

**Branch:** `003-ai-workers-autonomous` | **Date:** 2026-05-08
**Spec:** ./spec.md

## Summary

Conjunto de workers Python orquestrados por LangGraph, consumindo a base
de eventos anonimizada (feature 001) e publicando sinais, recomendações
e resumos para o painel (feature 002) e para o assistente (feature 004).
Provider LLM padrão é Grok (xAI) via adapter; substituível por NVIDIA NIM
on-prem. Todo output passa por filtros de finalidade e clínico antes de
ser persistido.

## Technical Context

- **Language/Runtime:** Python 3.12.
- **Orquestração de IA:** LangGraph (fluxos), LlamaIndex (indexação e
  consulta a embeddings em pgvector), Pydantic v2 para schemas de IO.
- **LLM Provider:** Grok (xAI) via adapter da feature 001; ativação de
  modelos por tipo de tarefa (classificação, anomalia, recomendação,
  sumarização). Capacidade de live search do Grok para enriquecer
  recomendações com notícias públicas sobre saúde no DF.
- **Filas:** Celery + Redis (compartilhado com feature 001).
- **Storage:** PostgreSQL (AnomalySignal, Recommendation, DailyBrief,
  WorkerRun, HumanDecision); pgvector para embeddings de eventos.
- **Observabilidade:** OpenTelemetry com semântica `gen-ai` do OTel.
- **Segurança:** detector de prompt injection (rebuff-like), allowlist
  de tópicos, filtro clínico de output, egress_guard compartilhado.
- **Testing:** pytest, pytest-asyncio, golden tests para prompts,
  testcontainers para Postgres+Redis.

## Constitution Check

| Princípio | Aderência |
|-----------|-----------|
| I. Soberania | LLM externo apenas para payload anonimizado; design pronto para NIM on-prem |
| II. LGPD | Apenas dados anonimizados consumidos |
| III. Guardrails | Intent classifier + filtros de output + HITL |
| IV. Não-Clínica | Filtro clínico bloqueia diagnóstico/prescrição |
| V. Sensor | Sinais derivam de telemetria cidadã |
| VI. Smart City | DailyBrief usa KPIs com referência |
| VII. Observabilidade | Spans gen-ai padronizados |
| VIII. Workflow | Spec → Plan → Tasks |
| IX. Segurança | Anti prompt injection; rate limit; HITL |

## Project Structure

backend/src/nowgo_saude/ai/
  workers/
    classifier.py
    anomaly_detector.py
    recommender.py
    daily_briefer.py
  graphs/                # LangGraph state machines
  prompts/               # versionados, com testes golden
  guards/                # intent, clinical, prompt-injection, output-filter
  models/                # AnomalySignal, Recommendation, DailyBrief, WorkerRun, HumanDecision
  feedback/              # ingestão de HumanDecision como sinal
  api/                   # endpoints HITL e leitura
workers/src/workers/
  ai_classifier_worker.py
  ai_anomaly_worker.py
  ai_recommender_worker.py
  ai_daily_brief_worker.py

## Phase 0: Research

1. Comparativo Grok vs. NIMs locais para tarefas alvo (latência, custo,
   qualidade em pt-BR).
2. Algoritmo de detecção de anomalias (z-score robusto vs.
   STL-decomposition vs. Prophet) para séries operacionais.
3. Padrão LangGraph para fluxos com HITL e retry.
4. Detector de prompt injection (rebuff, NeMo Guardrails, custom).
5. Filtro clínico: classificador binário (clínico vs. operacional)
   treinado/avaliado em corpus pt-BR.
6. Estratégia de golden tests para prompts e versionamento.
7. Modelo de custo + budget por gestor.

## Phase 1: Design & Contracts

- `data-model.md`: AnomalySignal, Recommendation, DailyBrief,
  WorkerRun, HumanDecision, com índices e constraints.
- `contracts/ai-api.openapi.yaml`: GET /signals, GET /recommendations,
  POST /recommendations/{id}/decision, GET /daily-brief/{date}.
- `contracts/worker-events.schema.json`: eventos publicados na fila.
- `quickstart.md`: cenário com seed → anomaly → recommendation
  → HITL → brief.

## Phase 2: Task Planning Approach

/tasks vai produzir:
1. Setup do módulo `ai/` e dependências (LangGraph, LlamaIndex).
2. Tests-first: contract tests dos endpoints; golden tests dos prompts;
   E2E dos cenários 1–5.
3. Models e migrations.
4. Guards (intent, clinical, prompt-injection, output filter).
5. Workers (classifier, anomaly, recommender, daily_briefer) com
   LangGraph.
6. Endpoints HITL e leitura.
7. Wire egress_guard para Grok com payload já filtrado por guards.
8. Observabilidade gen-ai e dashboard de custo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (vazio)   | -          | -                                    |

## Progress Tracking

- [x] Initial Constitution Check passed
