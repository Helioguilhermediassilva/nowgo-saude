# Research: Citizen Telemetry Ingestion (Feature 001)

**Phase:** 0 (research) | **Date:** 2026-05-08 | **Status:** Initial draft

Esta pesquisa resolve as 6 lacunas identificadas no `plan.md` antes de
projetar contratos e modelos. Cada item segue o template
**Decision / Rationale / Alternatives considered**.

---

## 1. Catálogo de fontes acessíveis no MVP

**Decision.** O MVP aceita 3 classes de fonte plugáveis via `Source`:

| Fonte | Tipo | Acesso MVP | Acesso Produção |
|-------|------|------------|------------------|
| OuvidorSUS DF | API REST oficial | Mock fixture (JSON Schema) | API SES-DF (token via Vault) |
| X / Twitter (via Grok) | LLM live-search | `GrokSourceAdapter` com query catálogo | Mesmo adapter, com quota de produção |
| Web Form interno | HTTP POST autenticado | Endpoint `/api/v1/intake` (T037) | Mesmo endpoint atrás de OIDC |

**Rationale.** Reduz dependência de credenciais externas para MVP; mantém o
mesmo contrato `Source` para a transição produção. O e-mail IMAP fica fora
do MVP por exigir caixa institucional dedicada e classificação anti-spam.

**Alternatives considered.**
- Scraping direto do portal OuvidorSUS — rejeitado: contraria política de
  uso e gera ruído de classificação.
- Twitter API v2 oficial — rejeitado para MVP: custo alto da tier
  Enterprise; Grok cobre a query semântica e cumpre §I (Soberania) por
  ser o único egress externo controlado.

---

## 2. Coleta X/Twitter via Grok

**Decision.** Usar `xAI Live Search` exposto pela API Grok com perfil
`region:DF`, `lang:pt-BR`, janela móvel de 24 h, quota de 5 req/min e
catálogo de termos versionado em `infra/config/grok_search_terms.yaml`.
Toda chamada passa por `egress_guard` e é registrada em `AuditEntry`.

**Rationale.** O adapter `GrokSourceAdapter` implementa `LLMProvider` +
`SourceAdapter`, mantendo um único ponto de saída externa. A janela de 24 h
e a quota controlada limitam custo e exposição.

**Alternatives considered.**
- Polling fixo a cada 30 s — rejeitado: estoura quota e gera duplicatas.
- Usar Grok somente para classificação, coletando X por outra via —
  rejeitado: aumenta superfície de egress e quebra §I.

---

## 3. Detecção de PII em pt-BR

**Decision.** Microsoft **Presidio Analyzer** com:

- Recognizers padrão (PERSON, EMAIL, PHONE_NUMBER, LOCATION).
- Recognizers customizados pt-BR para CPF, CNPJ, RG, CNS (Cartão Nacional
  de Saúde) e CEP, baseados em regex + checksum.
- Modelo NLP: `spaCy pt_core_news_lg` carregado uma vez por worker.

`presidio_anonymizer` aplica `replace` para nomes (token) e `hash` (HMAC) para
identificadores estruturados, conforme política do item 4.

**Rationale.** Presidio já é validado para cenários LGPD-similares (GDPR);
extensível, com plugin de recognizer customizado por entidade brasileira.

**Alternatives considered.**
- spaCy + regex próprias — rejeitado: reinvenção; manter Presidio como
  dependência canônica reduz dívida.
- LLM-based PII detection (Grok) — rejeitado: violaria §II (PII nunca
  pode sair do perímetro antes da pseudonimização).

---

## 4. Esquema de pseudonimização

**Decision.** **HMAC-SHA256** com chave por categoria armazenada em Vault
HashiCorp (futuro) — em dev, em variável `PII_HMAC_KEY_<CATEGORY>` carregada
de `.env`. Formato do token: `pii:<categoria>:<base64url(hmac[:16])>`.

| Categoria | Origem | Token exemplo |
|-----------|--------|---------------|
| `cpf` | CPF detectado | `pii:cpf:R3vH2K...` |
| `cns` | Cartão Nacional Saúde | `pii:cns:9aT4Lp...` |
| `name` | Nome completo | `pii:name:m7bY8w...` |
| `email` | E-mail | `pii:email:Qz4Nu1...` |
| `phone` | Telefone | `pii:phone:k2sJ9o...` |
| `address` | Endereço | `pii:addr:1pX3v7...` |

`PIIVaultRecord` guarda **o valor cifrado original** (AES-GCM) com
`token` como chave única, para reidentificação controlada (acesso RBAC
exclusivo a roles `lgpd_officer`/`audit_admin`, sempre logado em
`AuditEntry`).

**Rationale.** HMAC garante determinismo (mesmo CPF → mesmo token),
permitindo agregações analíticas sem reverter PII; segregação em schema
`pii_vault` com criptografia em repouso satisfaz §II e §IX.

**Alternatives considered.**
- SHA-256 puro (sem chave) — rejeitado: vulnerável a rainbow tables sobre
  espaço pequeno (CPF tem 10⁸ valores válidos).
- Tokenização aleatória sem reversibilidade — rejeitado: SES-DF exige
  reidentificação para fluxos de ouvidoria que retornam ao cidadão.

---

## 5. Política de retenção

**Decision.** Retenção por classe, configurável via `Source.retention_policy`:

| Classe | Retenção evento operacional | Retenção PIIVault | Retenção payload bruto MinIO |
|--------|------------------------------|-------------------|------------------------------|
| `ouvidoria_oficial` | 5 anos | 5 anos (LGPD Art. 16 II) | 30 dias |
| `social_publica` | 18 meses | N/A (sem PII por construção) | 90 dias |
| `formulario_interno` | 5 anos | 5 anos | 30 dias |

Job Celery `retention_sweep` roda diariamente, expira eventos e move
`PIIVaultRecord` para "right-to-be-forgotten" sob solicitação registrada em
`AuditEntry`.

**Rationale.** 5 anos cobre prazo de ações administrativas SUS e LGPD;
18 meses para social pública alinha com prazo de ações de imagem.

**Alternatives considered.**
- Retenção uniforme de 5 anos — rejeitado: viola minimização (§II).
- Sem retenção (apenas streaming) — rejeitado: inviabiliza auditoria e
  reprocessamento.

---

## 6. Mapeamento ISO 37120 §15 (saúde)

**Decision.** `TelemetryEvent.iso_37120` carrega array de indicadores:

| Indicador ISO | Atributo derivado |
|----------------|-------------------|
| 15.1 Average life expectancy | (agregado, não no evento) |
| 15.2 Under-5 mortality rate | (agregado) |
| 15.3 In-patient hospital beds per 100k | `unit.beds_per_100k` (joined) |
| 15.4 Physicians per 100k | `unit.physicians_per_100k` (joined) |
| 15.5 Suicide rate | (agregado) |
| 15.6 Public expenditure on health | (agregado) |
| 15.7 (37122) Wait time non-elective surgery | `event.attributes.wait_time_hours` |
| 15.8 (37122) Wait time elective surgery | `event.attributes.wait_time_hours` |

`event.iso_37122` reservado para **ISO 37122** (Smart Cities), com tag
`SC.health.access` quando a fonte for cidadã (X/Twitter, ouvidoria).

**Rationale.** §VI (Smart City) exige declaração explícita do framework
em metadados; manter o array permite múltiplos enquadramentos e auditoria.

**Alternatives considered.**
- Mapear no consumidor (feature 002) — rejeitado: viola §VI
  (declaração na origem) e dificulta auditoria.

---

## Open questions (a resolver em design)

- Vault HashiCorp on-prem ou KMS NVIDIA NIM? → decisão na Phase 1 do
  feature 003.
- Modelo NLP pt-BR `pt_core_news_lg` (~600 MB): empacotar na imagem de
  worker ou baixar em init? → empacotar para air-gap-ready.

---

## References

- LGPD Lei 13.709/2018 Arts. 7º III, 11 II "a", 16 II.
- ISO 37120:2018 §15 City service indicators — Health.
- ISO 37122:2019 Smart City indicators §15.
- Microsoft Presidio v2.2 docs.
- xAI Grok API reference (live search v1).
