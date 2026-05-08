# Feature Specification: Citizen Telemetry Ingestion

**Feature Branch:** `001-citizen-telemetry-ingestion`
**Created:** 2026-05-08
**Status:** Draft
**Input:** PRD §4.1 (Citizen Operational Intelligence), §5 (Functional
Requirements), §6 (Non-Functional Requirements).

---

## ⚡ Quick Guidelines

- ✅ Foca no QUE precisa ser ingerido e POR QUE.
- ❌ Não define HOW (sem stack, schemas, código).
- 🔒 Constituição checada antes do SUCCESS.

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

Como gestor de saúde do GDF, preciso que toda manifestação pública sobre
saúde no Distrito Federal — registros de ouvidoria (OuvidorSUS),
reclamações em canais oficiais e posts públicos em X/Twitter relacionados
à saúde no DF — seja ingerida automaticamente pela plataforma, anonimizada
e disponibilizada como telemetria operacional estruturada, para que a IA
possa detectar gargalos antes que escalem.

### Acceptance Scenarios

1. **Given** um cidadão registra reclamação no OuvidorSUS sobre fila em
   UPA específica, **When** o pipeline de ingestão executa, **Then** o
   evento aparece na base operacional anonimizado, classificado por região
   administrativa e unidade de saúde, em até 5 minutos.
2. **Given** um post público em X/Twitter mencionando hashtags de saúde no
   DF, **When** o coletor identifica relevância, **Then** o post é ingerido
   com metadados de fonte, sem qualquer PII de não-cidadãos, marcado como
   "fonte pública externa".
3. **Given** uma reclamação contém PII (CPF, nome, telefone, endereço),
   **When** o registro entra no pipeline, **Then** todos os campos PII são
   pseudonimizados ANTES de qualquer persistência analítica ou chamada a LLM.
4. **Given** uma fonte externa fica indisponível, **When** o coletor tenta
   ingestão, **Then** o sistema registra falha, aplica retry com backoff e
   alerta o operador, sem perder eventos já enfileirados.

### Edge Cases

- O que acontece se o OuvidorSUS retornar formato inesperado? Pipeline
  rejeita o registro, registra em DLQ (dead-letter), notifica operador, não
  bloqueia outros eventos.
- O que acontece se um post de X/Twitter tiver conteúdo não relacionado a
  saúde mas usar hashtag de saúde? Filtro de relevância classifica como
  "irrelevante" e descarta antes da persistência analítica.
- O que acontece se a anonimização falhar (PII detectada após o estágio de
  anonimização)? O evento é bloqueado, isolado em quarentena cifrada, e um
  alerta crítico é gerado.
- O que acontece se a API Grok ficar indisponível para enriquecimento?
  Pipeline persiste o evento bruto-anonimizado e marca enriquecimento como
  "pendente" para reprocessamento posterior.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** Sistema MUST ingerir registros de ouvidoria (OuvidorSUS ou
  equivalente do GDF) em tempo quase-real, com janela máxima de 5 minutos
  entre evento de origem e disponibilização na plataforma.
- **FR-002:** Sistema MUST coletar posts públicos em X/Twitter relacionados
  a saúde no DF, usando catálogo configurável de termos, hashtags e contas
  oficiais.
- **FR-003:** Sistema MUST aceitar fontes adicionais (e-mail institucional,
  formulários web, redes sociais oficiais) via interface de coletor
  plugável, sem alteração do núcleo.
- **FR-004:** Sistema MUST detectar e pseudonimizar/anonimizar PII (CPF,
  RG, nome completo, telefone, e-mail, endereço, geolocalização precisa)
  ANTES de qualquer persistência analítica ou envio a LLM.
- **FR-005:** Sistema MUST classificar cada evento por: (a) região
  administrativa do DF, (b) unidade de saúde mencionada (quando
  identificável), (c) tema operacional (fila, infraestrutura, atendimento,
  medicamento, agendamento, outros), (d) sentimento, (e) gravidade.
- **FR-006:** Sistema MUST manter relação reversível pseudônimo↔identidade
  apenas em vault cifrado e segregado, com acesso auditado e justificável
  (ex.: cumprimento de direito de titular sob LGPD).
- **FR-007:** Sistema MUST persistir trilha de auditoria imutável de cada
  evento ingerido, incluindo origem, timestamp, transformações aplicadas e
  versão do pipeline.
- **FR-008:** Sistema MUST suportar retenção configurável por categoria de
  dado, com expurgo automático ao fim do período.
- **FR-009:** Usuários autorizados MUST conseguir consultar volumes,
  taxas de erro e latência do pipeline em painel operacional.
- **FR-010:** Sistema MUST rejeitar e isolar eventos cuja anonimização
  falhe em qualquer estágio do pipeline, gerando alerta crítico.

### Non-Functional Requirements

- **NFR-001:** Latência ponta-a-ponta (origem → disponível para análise)
  p95 ≤ 5 min.
- **NFR-002:** Capacidade mínima de 100 eventos/segundo sustentados, com
  burst de 1.000 eventos/segundo por até 10 minutos.
- **NFR-003:** Disponibilidade ≥ 99.5% mensal para o pipeline (MVP).
- **NFR-004:** Conformidade LGPD: bases legais Art. 7º III (políticas
  públicas) e Art. 11 II "a" (tutela da saúde) declaradas em metadado.
- **NFR-005:** Rastreabilidade: para todo insight derivado, é possível
  recuperar a lista de eventos-fonte (com pseudônimos) que o produziram.

### Key Entities

- **TelemetryEvent:** unidade atômica de telemetria. Atributos relevantes:
  fonte, timestamp de origem, timestamp de ingestão, conteúdo
  anonimizado, classificação (região, unidade, tema, sentimento,
  gravidade), pseudônimo do titular (quando aplicável), versão do
  pipeline.
- **Source:** descritor de fonte (OuvidorSUS, X/Twitter, e-mail,
  formulário). Atributos: tipo, credenciais (referenciadas no Vault),
  política de coleta, status operacional.
- **PIIVault:** repositório segregado da relação pseudônimo↔identidade.
  Acesso restrito a fluxos de exercício de direitos do titular.
- **PipelineRun:** execução de um lote de coleta. Atributos: início, fim,
  volumes, erros, eventos quarentenados.

---

## Constitution Check

- [x] **I. Soberania:** ingestão e anonimização rodam on-prem na NowGo AI
  Platform; apenas dados públicos (X/Twitter) e payloads pós-anonimização
  podem trafegar para a API Grok externa.
- [x] **II. LGPD by Design:** anonimização ANTES de persistência
  analítica; vault segregado para relação reversível; retenção configurável.
- [x] **III. Guardrails de Finalidade:** filtro de relevância restringe ao
  domínio saúde pública; eventos fora de escopo são descartados.
- [x] **IV. IA Não-Clínica:** ingestão não emite diagnóstico; classificação
  é operacional (fila, infraestrutura, atendimento), nunca clínica.
- [x] **V. Cidadão como Sensor:** percepção pública é a matéria-prima.
- [x] **VI. Smart City Standards:** classificação por região e tema é
  mapeável a ISO 37120 (15.x — saúde) e IMD Smart City Index (percepção).
- [x] **VII. Observabilidade:** trilha de auditoria, métricas de pipeline,
  tracing por evento.
- [x] **VIII. AI-Amplified Workflow:** spec → plan → tasks aplicado.
- [x] **IX. Segurança:** PII tratada como dado sensível; vault cifrado;
  RBAC para acesso reversivo; sanitização de input antes de LLM externo.

---

## Review & Acceptance Checklist

- [x] Sem detalhes de implementação (linguagem, framework, schema concreto).
- [x] Foco em valor para o gestor de saúde.
- [x] Sem marcadores [NEEDS CLARIFICATION] pendentes.
- [x] Requisitos testáveis e mensuráveis.
- [x] Escopo delimitado: apenas ingestão e classificação inicial; análise
  avançada e dashboards são features separadas (002, 003, 004).
