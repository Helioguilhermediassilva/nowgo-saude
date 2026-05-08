# Implementation Plan: Citizen Telemetry Ingestion

**Branch:** `001-citizen-telemetry-ingestion` | **Date:** 2026-05-08
**Spec:** ./spec.md

## Summary

Pipeline de ingestão multi-fonte (OuvidorSUS, X/Twitter, fontes plugáveis)
com anonimização LGPD, classificação operacional inicial e disponibilização
em base analítica. Roda como conjunto de workers assíncronos atrás de uma
fila de eventos, com persistência transacional em PostgreSQL e armazenamento
de embeddings em pgvector para uso futuro pelas features 003 e 004.

## Technical Context

- **Language/Runtime:** Python 3.12 (workers e API), Node 20 (apenas frontend
  operacional do pipeline na feature 002).
- **Primary Frameworks:** FastAPI (API de admin do pipeline), Celery + Redis
  (fila de eventos), httpx (clientes HTTP), Pydantic v2 (validação).
- **Storage:** PostgreSQL 16 (eventos transacionais, auditoria, PIIVault em
  schema segregado), pgvector (embeddings), MinIO (payloads brutos cifrados
  para reprocessamento).
- **LLM Provider:** Grok via xAI API (MVP) através de adapter
  `LLMProvider`; substituível por NVIDIA NIM on-prem sem alteração
  de código de domínio. Usado para enriquecimento (classificação semântica)
  apenas com payload pós-anonimização.
- **Coleta X/Twitter:** API Grok com capacidade de busca em X (live search)
  para posts públicos sobre saúde no DF. Catálogo de termos em config.
- **Auth:** JWT stub (MVP) com adapter `AuthProvider` plugável para
  OIDC gov.br/AD-GDF.
- **Testing:** pytest, pytest-asyncio, testcontainers (Postgres, Redis).
- **Target Deployment:** NowGo AI Platform on-prem; Docker Compose para dev.
- **Performance Goals:** ingestão sustentada ≥ 100 ev/s; p95 origem→disponível
  ≤ 5 min; anonimização < 200 ms por evento.
- **Constraints:** LGPD (Art. 7º III, Art. 11 II "a"); air-gap-ready (toda
  saída externa passa por egress controlado e somente após anonimização).

## Constitution Check

| Princípio | Aderência |
|-----------|-----------|
| I. Soberania | Núcleo on-prem; egress externo (Grok) restrito a payload anonimizado |
| II. LGPD | Anonimização pré-persistência; PIIVault segregado; retenção configurável |
| III. Guardrails | Filtro de relevância de domínio aplicado pré-classificação |
| IV. IA Não-Clínica | Classificação restrita a temas operacionais |
| V. Cidadão como Sensor | Núcleo da feature |
| VI. Smart City | Mapeamento ISO 37120 §15 declarado em metadado |
| VII. Observabilidade | OpenTelemetry obrigatório; auditoria imutável |
| VIII. Workflow | Spec → Plan → Tasks |
| IX. Segurança | PII como sensível; vault cifrado; RBAC; rate-limit no egress |

Sem desvios. Complexity Tracking vazio.

## Project Structure

### Documentation (this feature)

specs/001-citizen-telemetry-ingestion/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    ingestion-api.openapi.yaml
    telemetry-event.schema.json
  tasks.md

### Source Code (repository root)

backend/
  src/
    nowgo_saude/
      ingestion/
        collectors/        # OuvidorSUS, GrokXSearch, EmailIMAP, WebForm
        anonymizer/        # PII detection + pseudonymization + vault
        classifier/        # region/unit/topic/sentiment/severity
        pipeline/          # Celery tasks, orchestration
        api/               # FastAPI admin endpoints
      core/
        llm/               # LLMProvider interface + Grok adapter
        auth/              # AuthProvider interface + JWTStub adapter
        audit/             # immutable audit trail
        observability/     # otel setup
      models/              # SQLAlchemy entities
  tests/
    contract/
    integration/
    unit/

workers/
  src/
    workers/
      ingestion_worker.py
      anonymizer_worker.py
      classifier_worker.py
  tests/

infra/
  docker-compose.dev.yaml
  postgres/init/
  otel-collector.yaml

## Phase 0: Research

Output: research.md. Tópicos a resolver:
1. Catálogo confirmado de fontes acessíveis no MVP (OuvidorSUS API real
   vs. mock; pacto com SES-DF para credenciais).
2. Estratégia de coleta X/Twitter via Grok: endpoints, quotas, custos,
   filtros geográficos para DF.
3. Biblioteca de detecção de PII em pt-BR (Presidio com recognizers
   customizados vs. spaCy + regex próprias).
4. Esquema de pseudonimização (HMAC-SHA256 com chave em Vault) e formato
   de chave por categoria de PII.
5. Política de retenção por classe de evento (alinhada com LGPD e
   diretrizes da SES-DF).
6. Mapeamento concreto ISO 37120 §15 (saúde) → atributos do TelemetryEvent.

## Phase 1: Design & Contracts

Outputs:
- `data-model.md`: TelemetryEvent, Source, PIIVaultRecord,
  PipelineRun, AuditEntry. Relações, índices, constraints.
- `contracts/ingestion-api.openapi.yaml`: endpoints administrativos
  (POST /sources, GET /pipeline-runs, POST /events:reprocess, GET /metrics).
- `contracts/telemetry-event.schema.json`: contrato canônico do
  evento publicado para as features 002/003/004.
- `quickstart.md`: smoke test ponta-a-ponta com OuvidorSUS mock e
  X/Twitter mock, validando anonimização e classificação.
- Contract tests (failing) para cada endpoint e para o schema do evento.

## Phase 2: Task Planning Approach

/tasks derivará tarefas em ordem:
1. Setup de monorepo (backend, workers, infra) e ferramentas de qualidade.
2. Tests-first: contract tests dos endpoints e do schema do evento;
   integration tests dos cenários de aceitação 1–4 da spec.
3. Modelos (TelemetryEvent, Source, PIIVaultRecord, PipelineRun, AuditEntry).
4. Núcleo: anonymizer, classifier, audit.
5. Coletores: OuvidorSUS, GrokXSearch (com adapter `LLMProvider`).
6. Pipeline (Celery tasks) + DLQ + retry/backoff.
7. API admin + RBAC + JWT stub.
8. Observabilidade (OTel, métricas Prometheus, logs estruturados).
9. Polish: performance, documentação executável (quickstart), revisão LGPD.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (vazio)   | -          | -                                    |

## Progress Tracking

- [ ] Phase 0: Research complete
- [ ] Phase 1: Design complete
- [ ] Phase 2: Task planning approach described
- [x] Initial Constitution Check passed
- [ ] Post-Design Constitution Check passed
- [ ] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)
