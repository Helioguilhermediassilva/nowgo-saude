# Feature Specification: AI Workers Autônomos

**Feature Branch:** `003-ai-workers-autonomous`
**Created:** 2026-05-08
**Status:** Draft
**Input:** PRD §4.3 (AI Workers), §5 (alertas e relatórios), §8 (segurança
de IA), §10 (mesa redonda — IA operacional).

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

Como Secretário de Saúde, preciso de agentes de IA rodando 24/7 que
analisem continuamente a telemetria cidadã (feature 001) e:
detectem anomalias antes que escalem, classifiquem prioridade de
intervenção, gerem resumos executivos diários e proponham recomendações
operacionais — sempre com human-in-the-loop antes de qualquer ação que
afete operação real.

### Acceptance Scenarios

1. **Given** a chegada contínua de eventos pelo pipeline, **When** o
   AI Worker de detecção de anomalias executa em janela rolante de
   60 minutos, **Then** ele identifica desvios estatisticamente
   significativos por unidade/região e cria um `AnomalySignal` com
   evidências rastreáveis.
2. **Given** um `AnomalySignal` de gravidade alta, **When** o worker
   de recomendação avalia, **Then** produz uma `Recommendation`
   com ação proposta, justificativa, fontes e nível de confiança, e
   encaminha para fila de revisão humana.
3. **Given** o início de um novo dia útil às 07:00, **When** o worker de
   resumo executivo executa, **Then** entrega ao Secretário um `DailyBrief`
   com top sinais, recomendações pendentes e variação dos KPIs Smart City.
4. **Given** um gestor revisa uma `Recommendation`, **When** aprova,
   rejeita ou edita, **Then** a decisão é registrada na trilha de
   auditoria e usada como sinal de feedback para o worker.
5. **Given** o worker de classificação encontra evento ambíguo, **When**
   confidence está abaixo do limiar, **Then** o evento é encaminhado para
   triagem humana em vez de classificado automaticamente.

### Edge Cases

- O que acontece se o LLM externo (Grok) ficar indisponível? Workers
  fazem failover para fila de retry e degradam para modos heurísticos
  (regras + estatística), sinalizando "modo degradado" no `DailyBrief`.
- O que acontece se um worker gerar volume excessivo de recomendações?
  Sistema aplica throttling e exige revisão humana antes de publicar
  acima do limiar configurado.
- O que acontece se o evento contiver pedido implícito de orientação
  clínica? Worker descarta saída clínica, gera apenas
  recomendação operacional e marca para encaminhamento humano.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** Sistema MUST executar workers especializados, no mínimo:
  classificação fina, detecção de anomalias, recomendação operacional,
  resumo executivo diário.
- **FR-002:** Cada worker MUST registrar entradas, saídas, prompt
  efetivo, modelo/versão, latência e custo (quando aplicável).
- **FR-003:** Toda `Recommendation` MUST passar por fluxo
  human-in-the-loop antes de gerar qualquer ação operacional externa.
- **FR-004:** Workers MUST consumir apenas dados pós-anonimização da
  feature 001.
- **FR-005:** Workers MUST aplicar guardrails de finalidade (escopo
  saúde pública), recusando saídas fora de domínio ou clínicas.
- **FR-006:** Sistema MUST permitir configuração por gestor de janelas,
  limiares e canais de alerta dos workers.
- **FR-007:** Sistema MUST suportar plugabilidade de modelos via
  `LLMProvider` (Grok no MVP; NVIDIA NIM/Ollama on-prem no roadmap).
- **FR-008:** Sistema MUST manter explicabilidade mínima: cada saída
  carrega lista de eventos-fonte, regras aplicadas e confidence.
- **FR-009:** Sistema MUST detectar e bloquear tentativas de prompt
  injection nos textos de origem antes do envio ao LLM.
- **FR-010:** Workers MUST emitir spans OpenTelemetry com atributos
  `ai.model`, `ai.confidence`, `ai.provider`,
  `source.event_ids`.

### Non-Functional Requirements

- **NFR-001:** Latência p95 do worker de anomalia ≤ 5 min após chegada
  do evento; resumo diário entregue até 07:30.
- **NFR-002:** Custo médio por evento processado (LLM externo)
  monitorado e alertado se exceder limiar.
- **NFR-003:** Cobertura de testes ≥ 85% para lógica não-IA e ≥ 70% para
  prompts (golden tests).
- **NFR-004:** Disponibilidade ≥ 99.5% mensal; degradação graciosa
  obrigatória quando LLM externo falha.

### Key Entities

- **AnomalySignal:** desvio detectado (escopo, métrica, baseline,
  desvio, evidências, severidade).
- **Recommendation:** ação proposta (escopo, justificativa, evidências,
  confidence, status do human-in-the-loop).
- **DailyBrief:** documento executivo (data, top sinais, KPIs, status
  de operação).
- **WorkerRun:** execução de worker (timestamp, entradas, saídas,
  modelo, latência, custo).
- **HumanDecision:** registro de decisão humana sobre recomendação.

---

## Constitution Check

- [x] **I. Soberania:** workers rodam on-prem; Grok é chamada apenas com
  payload anonimizado, atrás do `egress_guard`.
- [x] **II. LGPD:** consumo apenas de dados pós-anonimização.
- [x] **III. Guardrails:** classificador de intenção + system prompt
  hardcoded + filtragem de output.
- [x] **IV. IA Não-Clínica:** workers proibidos de emitir
  diagnóstico/prescrição; fallback para encaminhamento humano.
- [x] **V. Cidadão como Sensor:** anomalias derivam da percepção pública.
- [x] **VI. Smart City:** DailyBrief inclui variação de KPIs Smart City.
- [x] **VII. Observabilidade:** spans OTel padronizados; auditoria.
- [x] **VIII. Workflow:** spec → plan → tasks.
- [x] **IX. Segurança:** detecção de prompt injection; rate limit;
  sanitização de output; HITL obrigatório.

---

## Review & Acceptance Checklist

- [x] Sem detalhes de implementação.
- [x] Foco em valor operacional ao gestor.
- [x] Sem [NEEDS CLARIFICATION].
- [x] Requisitos testáveis.
- [x] Escopo: workers de análise; chat conversacional é a feature 004.
