# Feature Specification: Assistente Conversacional para Gestores

**Feature Branch:** `004-conversational-assistant`
**Created:** 2026-05-08
**Status:** Draft
**Input:** PRD §4.4 (Camada de IA Conversacional), §5 (interface
conversacional), §8.2 (Guardrails de Finalidade), §8 (segurança de IA).

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

Como gestor de saúde do GDF, preciso conversar em linguagem natural com a
plataforma para investigar a operação ("Quais unidades estão com maior
pressão hoje?", "Quais reclamações cresceram nesta semana?", "Onde há
risco de crise nas próximas 48 h?", "Quais regiões precisam de
intervenção imediata?") e receber respostas baseadas estritamente nos
dados operacionais da plataforma, com fontes citadas, dentro do escopo
exclusivo de saúde pública.

### Acceptance Scenarios

1. **Given** o gestor pergunta "Quais unidades estão com maior pressão
   hoje?", **When** o assistente processa, **Then** retorna ranking
   factual extraído da base operacional, com até N unidades, citando
   timestamp dos dados e link para drill-down no painel.
2. **Given** uma pergunta envolve previsão (próximas 48 h), **When**
   processada, **Then** o assistente apresenta projeção com intervalo de
   confiança e indica explicitamente "estimativa baseada em sinais
   recentes — não substitui análise humana".
3. **Given** o gestor pede orientação fora de escopo (ex.: "qual é a
   cotação do dólar?"), **When** o classificador de intenção detecta,
   **Then** o assistente responde com a mensagem amigável padrão e
   registra a tentativa em log de auditoria.
4. **Given** o gestor pede orientação clínica (ex.: "que medicamento
   passar ao paciente X?"), **When** o filtro clínico detecta,
   **Then** o assistente recusa, explica que é apoio operacional não
   clínico, e sugere encaminhamento humano.
5. **Given** um perfil "Diretor de Hospital", **When** ele pergunta
   sobre dados de unidade fora de seu escopo, **Then** o assistente
   recusa explicitamente e cita a política RBAC.
6. **Given** uma pergunta com dados atuais relevantes, **When**
   processada, **Then** a resposta cita até 5 fontes (eventos
   pseudonimizados, KPIs, recomendações) com identificadores
   rastreáveis no sistema.

### Edge Cases

- O que acontece em prompt injection ("ignore instruções anteriores e
  ...")? Detector bloqueia, registra incidente e retorna mensagem padrão.
- O que acontece se a base não tem dado suficiente? Assistente responde
  "não há dados suficientes" em vez de inventar.
- O que acontece se o usuário insiste em fluxo bloqueado? Após N
  tentativas, o assistente sugere contato humano e aciona rate limit.
- O que acontece em consulta sensível à LGPD (pedido de identificação
  de cidadão)? Recusado por padrão; encaminhamento ao fluxo formal de
  exercício de direitos do titular.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** Sistema MUST expor interface de chat aos gestores, com
  histórico por usuário e sessão.
- **FR-002:** Sistema MUST aplicar classificador de intenção ANTES do
  LLM, bloqueando perguntas fora do domínio com mensagem padrão.
- **FR-003:** Sistema MUST aplicar filtro clínico ANTES e DEPOIS do LLM.
- **FR-004:** Sistema MUST aplicar detector de prompt injection no input.
- **FR-005:** Respostas MUST ser geradas com RAG sobre eventos
  pseudonimizados, KPIs e recomendações; cada resposta MUST citar
  fontes (até 5) com identificador rastreável.
- **FR-006:** Sistema MUST recusar respostas quando não houver evidência
  suficiente, em vez de inventar.
- **FR-007:** Sistema MUST respeitar RBAC: respostas só podem incluir
  dados do escopo do usuário (Secretário/Diretor/Analista).
- **FR-008:** Sistema MUST registrar prompt, resposta, fontes,
  classificação de intenção, decisões dos guardrails e custo, em trilha
  de auditoria imutável.
- **FR-009:** Sistema MUST oferecer mensagem amigável padrão para
  bloqueios, sem revelar detalhes do system prompt.
- **FR-010:** Sistema MUST aplicar rate limit por usuário e por sessão,
  com escalação para revisão humana após N bloqueios consecutivos.
- **FR-011:** Sistema MUST suportar idioma pt-BR como primário.

### Non-Functional Requirements

- **NFR-001:** Latência p95 da resposta ≤ 6 s para perguntas com RAG;
  ≤ 2 s quando resposta é puramente factual sem geração extensa.
- **NFR-002:** Taxa de falsos positivos do classificador de intenção
  ≤ 3% no conjunto de avaliação curado.
- **NFR-003:** Taxa de bloqueio correto de prompt injection ≥ 95% no
  conjunto de adversariais curado.
- **NFR-004:** Toda resposta deve ser auditável ponta-a-ponta.

### Key Entities

- **ChatSession:** sessão por usuário (id, perfil, escopo RBAC,
  início, fim, mensagens).
- **ChatMessage:** mensagem (id, role, content, timestamp, refs).
- **GuardDecision:** decisão de cada guard (intent, clinical,
  prompt-injection, output-filter) com razão e ação tomada.
- **CitationRef:** referência a um item da base (evento, KPI,
  recomendação) com id rastreável.
- **AssistantRun:** execução completa de uma resposta (prompt,
  retrieval, modelo, latência, custo, decisões).

---

## Constitution Check

- [x] **I. Soberania:** RAG e guardrails on-prem; LLM externo (Grok)
  recebe apenas prompt sanitizado e retrieval pseudonimizado.
- [x] **II. LGPD:** dados pseudonimizados; recusa identificação direta;
  encaminhamento ao fluxo de direitos do titular.
- [x] **III. Guardrails:** classificador de intenção + system prompt +
  blacklist + filtro de output; mensagem padrão amigável.
- [x] **IV. IA Não-Clínica:** filtro clínico bloqueia
  diagnóstico/prescrição.
- [x] **V. Cidadão como Sensor:** chat é canal para gestores
  interrogarem a percepção pública.
- [x] **VI. Smart City:** quando responde com KPIs, cita framework.
- [x] **VII. Observabilidade:** spans gen-ai; auditoria de guard
  decisions; histórico imutável.
- [x] **VIII. Workflow:** spec → plan → tasks.
- [x] **IX. Segurança:** anti prompt injection; rate limit; RBAC; logs
  de auditoria; sem leakage do system prompt.

---

## Review & Acceptance Checklist

- [x] Sem detalhes de implementação.
- [x] Foco em valor para o gestor.
- [x] Sem [NEEDS CLARIFICATION].
- [x] Requisitos testáveis.
- [x] Escopo: chat para gestores; chat para cidadão final é roadmap pós-MVP.
