# Feature Specification: Command Center Dashboard (Painel Saúde)

**Feature Branch:** `002-command-center-dashboard`
**Created:** 2026-05-08
**Status:** Draft
**Input:** PRD §4.2 (Painel Saúde / Command Center), §5 (visualização e
alertas), §6 (NFR), §3 (benchmarking Smart City).

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

Como Secretário de Saúde do GDF (ou Diretor de Hospital, ou Analista),
preciso de um painel executivo único que mostre, em tempo quase-real, o
estado operacional da rede de saúde do DF — pressão por unidade,
gargalos de fila, regiões em escalada de queixas, indicadores Smart City
— para decidir intervenções operacionais antes que se transformem em crise.

### Acceptance Scenarios

1. **Given** novos eventos chegam ao pipeline (feature 001), **When** o
   gestor abre o Painel Saúde, **Then** o mapa de calor de pressão por
   região administrativa reflete os últimos 15 minutos com defasagem
   máxima de 60 segundos.
2. **Given** uma unidade de saúde apresenta crescimento atípico de
   reclamações sobre fila, **When** o painel renderiza, **Then** essa
   unidade aparece destacada como "atenção crítica" com indicador visual
   distinto e link para detalhamento.
3. **Given** o gestor clica em uma região no mapa, **When** o detalhamento
   é aberto, **Then** ele vê: top 5 temas operacionais, evolução das
   últimas 7 dias, lista de unidades afetadas, KPIs ISO 37120 §15
   correspondentes.
4. **Given** o gestor configura um alerta para "queixas de fila acima de
   X em uma RA", **When** o limiar é atingido, **Then** o sistema emite
   notificação (push/e-mail) e registra na trilha de alertas.
5. **Given** um perfil "Diretor de Hospital", **When** ele acessa o
   painel, **Then** vê apenas dados da(s) unidade(s) sob sua governança.

### Edge Cases

- O que acontece se o pipeline (feature 001) está degradado? O painel
  exibe banner de "dados defasados" com timestamp da última atualização
  bem-sucedida, em vez de números enganosos.
- O que acontece se uma região não tem eventos no período? Heatmap
  exibe "sem dados" em vez de zero (que seria interpretado como "tudo
  bem").
- O que acontece com unidades não georreferenciadas? Aparecem em lista
  separada, sinalizadas para complementação cadastral.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** Sistema MUST exibir mapa de calor de pressão operacional
  por região administrativa do DF, atualizado a cada ≤ 60 segundos.
- **FR-002:** Sistema MUST exibir lista priorizada de unidades de saúde em
  estado "atenção crítica", com critério configurável (limiar absoluto,
  desvio sobre média histórica, taxa de crescimento).
- **FR-003:** Sistema MUST exibir KPIs operacionais mapeáveis a ISO 37120
  §15 (saúde), ITU-T Y.4900 e IMD Smart City Index (percepção do residente).
- **FR-004:** Usuários MUST poder fazer drill-down de região → unidade →
  evento individual (anonimizado), respeitando RBAC.
- **FR-005:** Usuários MUST poder configurar alertas baseados em regras
  declarativas (limiar, anomalia, escalada) com notificação por canal
  (in-app, e-mail, e, no roadmap, SMS/push).
- **FR-006:** Sistema MUST permitir exportação de relatórios diários e
  semanais em PDF e CSV, preservando atribuição RBAC.
- **FR-007:** Painel MUST suportar pelo menos 3 perfis (Secretário,
  Diretor de Hospital, Analista) com escopos de dados distintos.
- **FR-008:** Sistema MUST exibir banner de degradação quando o pipeline
  de ingestão estiver com latência acima do limiar configurado.
- **FR-009:** Cada KPI exibido MUST ter, em tooltip, sua referência ao
  framework Smart City (ISO/ITU/IMD) e a fonte do dado.

### Non-Functional Requirements

- **NFR-001:** Tempo de carga inicial do painel p95 ≤ 2 s; atualização
  incremental p95 ≤ 500 ms.
- **NFR-002:** Suporte a 200 usuários concorrentes no MVP.
- **NFR-003:** Acessibilidade WCAG 2.1 AA mínima.
- **NFR-004:** Responsivo desktop-first; tablet como segundo target.
- **NFR-005:** Toda visualização deve declarar fonte e timestamp.

### Key Entities

- **DashboardView:** definição de um painel (composição de widgets,
  filtros, escopo RBAC).
- **Widget:** mapa de calor, lista de atenção crítica, série temporal,
  KPI card, distribuição por tema.
- **AlertRule:** regra declarativa do usuário (escopo, limiar, canais).
- **AlertEvent:** disparo de uma regra (timestamp, regra, payload,
  notificações geradas).
- **KPIDefinition:** metadado do KPI (nome, fórmula, unidade, framework
  de referência, fonte).

---

## Constitution Check

- [x] **I. Soberania:** painel renderiza sobre API local; nenhum dado
  trafega para LLM externo nesta feature.
- [x] **II. LGPD:** drill-down até evento exibe apenas pseudônimos; acesso
  a vault não é exposto ao painel.
- [x] **III. Guardrails:** painel não tem entrada de IA aberta; consome
  somente dados estruturados.
- [x] **IV. IA Não-Clínica:** indicadores são operacionais.
- [x] **V. Cidadão como Sensor:** percepção pública ocupa o topo do painel.
- [x] **VI. Smart City Standards:** todo KPI declara framework de
  referência em metadado.
- [x] **VII. Observabilidade:** métricas de uso do painel emitidas via OTel.
- [x] **VIII. Workflow:** spec → plan → tasks.
- [x] **IX. Segurança:** RBAC por perfil; auditoria de cada acesso e
  exportação.

---

## Review & Acceptance Checklist

- [x] Sem detalhes de implementação.
- [x] Foco em valor para o gestor.
- [x] Sem [NEEDS CLARIFICATION] pendentes.
- [x] Requisitos testáveis.
- [x] Escopo: visualização e alertas; análise autônoma é da feature 003.
