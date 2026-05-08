# Tasks: Assistente Conversacional

**Input:** specs/004-conversational-assistant/
**Prerequisites:** plan.md (✓), spec.md (✓), features 001/002/003
disponíveis (LLMProvider, guards, eventos pseudonimizados, painel).

## Path Conventions

- **Backend:** `backend/src/nowgo_saude/assistant/`
- **Frontend:** `frontend/app/(dashboard)/assistant/`
- **Specs:** `specs/004-conversational-assistant/`

---

## Phase 3.1: Setup

- [ ] **T001** Criar módulo `backend/src/nowgo_saude/assistant/`
  com `api/`, `graphs/`, `retrieval/`,
  `prompts/`, `models/`.
- [ ] **T002** Criar página `frontend/app/(dashboard)/assistant/page.tsx`
  e pasta `components/` e `lib/` locais.
- [ ] **T003** [P] Adicionar dependências backend via Poetry:
  `llama-index-vector-stores-postgres`,
  `llama-index-embeddings-huggingface` (modelo embarcável local).
- [ ] **T004** [P] Curar conjunto adversarial pt-BR (prompt injection,
  clínico, fora de escopo) em
  `backend/tests/adversarial/dataset.jsonl`.

## Phase 3.2: Research & Design

- [ ] **T005** `research.md` resolvendo os 7 tópicos do plan §0.
- [ ] **T006** `data-model.md` (ChatSession, ChatMessage,
  GuardDecision, CitationRef, AssistantRun).
- [ ] **T007** [P] `contracts/assistant-api.openapi.yaml`
  (POST /chat com SSE, GET /sessions, GET /sessions/{id}/messages).
- [ ] **T008** [P] `contracts/assistant-stream.md` (formato SSE:
  token, citation, guard_event, end-of-turn).
- [ ] **T009** `quickstart.md` ponta-a-ponta com RBAC e bloqueios.
- [ ] **T010** [P] System prompt hardcoded versionado em
  `backend/src/nowgo_saude/assistant/prompts/system_v1.md`,
  com escopo restrito a saúde pública e proibições explícitas.

## Phase 3.3: Tests First (TDD)

- [ ] **T011** [P] Contract test `POST /api/v1/assistant/chat` em
  `backend/tests/contract/test_assistant_chat.py`.
- [ ] **T012** [P] Contract test `GET /api/v1/assistant/sessions`
  em `backend/tests/contract/test_assistant_sessions.py`.
- [ ] **T013** [P] Stream test SSE em
  `backend/tests/contract/test_assistant_stream.py`.
- [ ] **T014** [P] Integration cenário 1 (ranking pressão hoje + drill-down)
  em `backend/tests/integration/test_pressure_query.py`.
- [ ] **T015** [P] Integration cenário 2 (previsão 48h com IC) em
  `backend/tests/integration/test_forecast_query.py`.
- [ ] **T016** [P] Integration cenário 3 (fora de escopo bloqueado) em
  `backend/tests/integration/test_out_of_scope.py`.
- [ ] **T017** [P] Integration cenário 4 (pedido clínico bloqueado) em
  `backend/tests/integration/test_clinical_blocked.py`.
- [ ] **T018** [P] Integration cenário 5 (RBAC negativa) em
  `backend/tests/integration/test_rbac_refusal.py`.
- [ ] **T019** [P] Integration cenário 6 (citação de fontes) em
  `backend/tests/integration/test_citations.py`.
- [ ] **T020** [P] Edge: prompt injection cobertura ≥ 95% em
  `backend/tests/security/test_prompt_injection_chat.py`
  (consome `dataset.jsonl`).
- [ ] **T021** [P] Edge: dados insuficientes → "não há dados" em
  `backend/tests/integration/test_insufficient_data.py`.
- [ ] **T022** [P] Edge: rate limit após N bloqueios em
  `backend/tests/integration/test_rate_limit_escalation.py`.
- [ ] **T023** [P] Edge: identificação de cidadão (LGPD) recusada em
  `backend/tests/integration/test_pii_request_refusal.py`.
- [ ] **T024** [P] Golden tests do system prompt em
  `backend/tests/golden/test_assistant_prompts.py`.
- [ ] **T025** [P] E2E Playwright: chat fluxo feliz + bloqueios em
  `frontend/tests/e2e/assistant_happy_and_blocked.spec.ts`.

## Phase 3.4: Core Implementation

- [ ] **T026** [P] Modelos ChatSession, ChatMessage, GuardDecision,
  CitationRef, AssistantRun em
  `backend/src/nowgo_saude/assistant/models/`.
- [ ] **T027** Migrations Alembic em
  `backend/alembic/versions/0004_assistant.py`.
- [ ] **T028** [P] Retrieval LlamaIndex com filtro RBAC pré-busca em
  `backend/src/nowgo_saude/assistant/retrieval/rbac_retriever.py`.
- [ ] **T029** [P] Reranker (cross-encoder local) em
  `backend/src/nowgo_saude/assistant/retrieval/reranker.py`.
- [ ] **T030** Grafo LangGraph: input → intent guard → injection guard →
  clinical guard pré → retrieval → generate (LLM) → clinical guard pós →
  output filter → citation, em
  `backend/src/nowgo_saude/assistant/graphs/chat_graph.py`
  (reusa guards da feature 003).
- [ ] **T031** Mensagens amigáveis padrão (sem leakage) em
  `backend/src/nowgo_saude/assistant/replies.py`.
- [ ] **T032** Endpoints REST + SSE em
  `backend/src/nowgo_saude/assistant/api/`
  (depende de T026–T030).
- [ ] **T033** [P] Componentes frontend `ChatPanel`,
  `Message`, `Citations`, `SafetyBadge` em
  `frontend/app/(dashboard)/assistant/components/`.
- [ ] **T034** [P] Cliente de stream (SSE) e parser de chunks em
  `frontend/app/(dashboard)/assistant/lib/chat-stream.ts`.
- [ ] **T035** Página `assistant/page.tsx` orquestrando layout,
  histórico e envio (depende de T033–T034).

## Phase 3.5: Integration

- [ ] **T036** Wire egress_guard nas chamadas Grok via
  `backend/src/nowgo_saude/assistant/llm_client.py`.
- [ ] **T037** Wire OpenTelemetry gen-ai em
  `backend/src/nowgo_saude/assistant/observability.py`
  (atributos: ai.model, ai.provider, ai.confidence, guard.decisions,
  citation.ids).
- [ ] **T038** Auditoria por mensagem (prompt, resposta, fontes,
  guards) em
  `backend/src/nowgo_saude/assistant/audit_hooks.py`.
- [ ] **T039** Rate limit (por usuário/sessão; escalação) em
  `backend/src/nowgo_saude/assistant/rate_limit.py`.
- [ ] **T040** RBAC pós-retrieval (defesa em profundidade) em
  `backend/src/nowgo_saude/assistant/retrieval/rbac_post_filter.py`.

## Phase 3.6: Polish

- [ ] **T041** [P] Suite de avaliação automatizada (eval set) que roda
  em CI, medindo NFR-002 (FP intent ≤ 3%) e NFR-003 (block PI ≥ 95%) em
  `backend/tests/eval/test_eval_suite.py`.
- [ ] **T042** Validação de NFR-001 (latência p95) em
  `backend/tests/performance/test_assistant_latency.py`.
- [ ] **T043** [P] Auditoria a11y do chat em
  `frontend/tests/a11y/assistant.spec.ts`.
- [ ] **T044** [P] Atualizar `quickstart.md`.
- [ ] **T045** Post-Design Constitution Check em plan.md.

## Dependencies

- T011–T025 (tests + golden + adversarial) DEVEM falhar antes de T026+.
- T026 antes de T027 e T032.
- T028–T029 antes de T030 (grafo).
- T030 antes de T032.
- T033–T034 antes de T035.
- T036 antes de qualquer chamada Grok em produção.
- Phase 3.5 após Phase 3.4. Phase 3.6 ao final.

## Validation Checklist

- [ ] Cada cenário de aceitação tem teste (T014–T019).
- [ ] Cada edge case tem teste (T020–T023).
- [ ] System prompt coberto por golden test (T024).
- [ ] Adversariais cobrem ≥ 95% (T020 + dataset).
- [ ] RBAC verificado em retrieval e em pós-filtro (T028, T040).
- [ ] Auditoria por mensagem (T038).
- [ ] Sem leakage do system prompt em mensagens de bloqueio (T031).
