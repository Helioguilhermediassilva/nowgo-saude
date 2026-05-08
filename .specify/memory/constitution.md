# NowGo Saúde — Constitution

**Versão:** 1.0.0
**Ratificada em:** 2026-05-08
**Última emenda:** 2026-05-08

Este documento define os princípios não-negociáveis que governam o desenho,
a implementação e a evolução da plataforma NowGo Saúde. Toda Spec, Plan e
Task derivada deste repositório DEVE ser avaliada contra estes princípios
antes de ser implementada. Violações exigem emenda formal a esta Constitution.

---

## Princípio I — Soberania de Dados (Sovereignty First)

A plataforma é desenhada para operar sobre a infraestrutura proprietária
NowGo AI Platform (edge computing on-premise com NVIDIA RTX 6000 Pro e Intel
Core Ultra). Dados sensíveis de saúde e dados biométricos NÃO podem ser
processados em nuvens públicas de terceiros.

**Exceção MVP transitória:** o MVP utiliza a API Grok (xAI) como provedor de
LLM e como fonte de telemetria pública (X/Twitter) sobre saúde no DF. Esta
exceção é aceita exclusivamente porque:

1. Apenas dados públicos (posts de X/Twitter) ou dados previamente
   anonimizados podem trafegar para a API externa.
2. Toda PII (CPF, nome, endereço, e-mail, telefone) DEVE ser removida ou
   pseudonimizada pelo pipeline de anonimização ANTES de qualquer chamada à
   API externa.
3. O provider de LLM é abstraído por uma interface plugável que permite
   substituição por modelos locais (NVIDIA NIMs, Ollama) sem alteração de
   código de domínio.
4. O roadmap pós-MVP exige migração para LLMs on-premise rodando na NowGo AI
   Platform. Esta migração é condição para expansão nacional.

## Princípio II — LGPD by Design

Toda funcionalidade que toque dados de cidadãos DEVE incluir, no momento da
especificação:

- Identificação explícita de bases legais (LGPD Art. 7º e Art. 11).
- Pipeline de anonimização/pseudonimização aplicado ANTES de qualquer
  processamento por LLM (interno ou externo).
- Política de retenção declarada e mecanismo de expurgo automatizado.
- Trilha de auditoria imutável de acesso e processamento.
- Suporte a direitos do titular (acesso, correção, eliminação, portabilidade).

Dados biométricos (voz, comportamento) são classificados como dados sensíveis
(Art. 11) e seu processamento é proibido na arquitetura externa: tratamento
exclusivamente on-premise no vault biométrico da NowGo AI Platform.

## Princípio III — Guardrails de Finalidade (Purpose-Bound AI)

Toda interface de IA exposta a usuários (gestores, cidadãos, integrações)
DEVE operar sob escopo restrito de saúde pública, gestão de filas, ouvidoria
e atendimento ao cidadão. É obrigatório:

- System prompt com restrição de domínio hardcoded.
- Classificador de intenção rodando ANTES do LLM principal.
- Whitelist de tópicos permitidos e blacklist de tópicos proibidos.
- Resposta amigável padrão para tentativas fora de escopo.
- Logging de todas as tentativas de bypass para auditoria e revisão.
- Múltiplas camadas: filtragem de input, classificação, filtragem de output.

## Princípio IV — IA Não-Clínica

Nenhum agente de IA da plataforma pode emitir diagnóstico, prescrever
medicamentos ou tratamentos, ou substituir o julgamento clínico de um
profissional de saúde. Toda saída da IA é classificada como apoio
administrativo/operacional. Decisões críticas exigem human-in-the-loop
explícito e rastreável.

## Princípio V — Cidadão como Sensor

A percepção pública (reclamações, ouvidoria, manifestações) é tratada como
telemetria operacional de primeira classe e não como dado secundário. A
qualidade do produto é medida pela capacidade de transformar essa telemetria
em ação operacional mensurável (alinhamento ao IMD Smart City Index, que
prioriza percepção do residente).

## Princípio VI — Conformidade com Padrões Smart City

KPIs e indicadores expostos pelo Painel Saúde DEVEM ser mapeáveis a:

- ISO 37120 e ISO 37122 — indicadores de cidades inteligentes.
- ITU-T Y.4900 — KPIs de cidades sustentáveis e inteligentes.
- IMD Smart City Index — percepção do cidadão como métrica primária.

Cada KPI publicado deve declarar, em metadado, sua referência ao framework
internacional aplicável.

## Princípio VII — Observabilidade e Auditabilidade

Toda ação relevante (acesso a dados, decisão de IA, alerta gerado, alteração
de configuração) DEVE produzir:

- Log estruturado com tracing distribuído (OpenTelemetry).
- Registro imutável em trilha de auditoria.
- Métrica exportável (Prometheus) quando aplicável.
- Rastreabilidade da fonte do dado para insights gerados por IA
  (explicabilidade mínima).

## Princípio VIII — Workflow de Engenharia AI-Amplified

O desenvolvimento adota a tríade GitHub Spec Kit + Google Stitch/Open Design
+ Google Antigravity/Augment Code. A consequência prática é:

- Toda feature começa por `/specify` (spec.md sem detalhes técnicos).
- Plan e Tasks só podem ser geradas após Spec ratificada contra esta
  Constitution.
- Implementação ocorre via tasks numeradas, executáveis e testáveis.
- "Vibe coding" sem spec é proibido.

## Princípio IX — Segurança como Pré-Requisito, Não Add-On

Threat modeling (STRIDE) é exigido em toda Plan que toque novos
dados/endpoints. Controles mínimos: OAuth 2.0/OIDC (gov.br/AD-GDF), RBAC,
API Gateway com WAF, criptografia AES-256 at-rest, TLS 1.3 in-transit,
secret management via Vault, sanitização de input/output contra prompt
injection.

**Exceção MVP transitória:** autenticação inicial via JWT stub local, com a
camada OIDC desenhada como interface plugável para substituição sem
alteração de domínio.

---

## Governança

- **Autoridade:** Esta Constitution prevalece sobre quaisquer outras
  diretrizes técnicas do repositório.
- **Emendas:** Requerem PR explícito tocando este arquivo, justificativa
  documentada e aprovação do CEO/CTO.
- **Revisão:** Toda Spec, Plan e Tasks deve incluir uma seção
  "Constitution Check" comprovando aderência aos princípios I–IX.
- **Versionamento:** Semântico (MAJOR.MINOR.PATCH). Mudança em princípio
  existente = MAJOR. Adição de princípio = MINOR. Refinamento textual = PATCH.
