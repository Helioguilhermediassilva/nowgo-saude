# Data Model: Citizen Telemetry Ingestion (Feature 001)

**Phase:** 1 (design) | **Date:** 2026-05-08

Modelos SQLAlchemy distribuídos nos schemas `telemetry`, `audit` e
`pii_vault`. Tabelas seguem convenção snake_case; chaves primárias
UUIDv7 (time-ordered) salvo onde indicado.

## Diagrama lógico

```
Source 1───* TelemetryEvent *───1 PIIVaultRecord (opcional, via tokens)
              │
              └───* PipelineRun (associação N:N por pipeline_run_events)
TelemetryEvent 1───* AuditEntry (append-only)
```

---

## 1. `telemetry.sources`

| Campo | Tipo | Constraints |
|-------|------|-------------|
| `id` | uuid | PK |
| `slug` | text | UNIQUE NOT NULL (ex.: `ouvidor_sus_df`, `grok_x_search`) |
| `kind` | text | CHECK IN (`ouvidoria_oficial`,`social_publica`,`formulario_interno`) |
| `display_name` | text | NOT NULL |
| `enabled` | bool | DEFAULT true |
| `config` | jsonb | NOT NULL (catalog terms, endpoint, schedule) |
| `retention_policy` | jsonb | NOT NULL (ver research §5) |
| `iso_37120_default` | jsonb | array de indicadores aplicáveis |
| `created_at` | timestamptz | DEFAULT now() |
| `updated_at` | timestamptz | DEFAULT now() ON UPDATE |

Índices: `idx_sources_kind`, `idx_sources_enabled`.

---

## 2. `telemetry.telemetry_events`

Evento canônico publicado para features 002/003/004.

| Campo | Tipo | Constraints |
|-------|------|-------------|
| `id` | uuid | PK (UUIDv7) |
| `source_id` | uuid | FK telemetry.sources.id |
| `external_id` | text | NULL; UNIQUE(source_id, external_id) |
| `received_at` | timestamptz | NOT NULL DEFAULT now() |
| `occurred_at` | timestamptz | NULL (origem da fonte) |
| `region_code` | text | DF region IBGE (ex.: `5300108`) |
| `unit_code` | text | NULL; FK opcional p/ `dashboard.units` |
| `topic` | text | classifier output (ex.: `acesso_consulta`) |
| `subtopic` | text | NULL |
| `sentiment` | smallint | -2..+2 |
| `severity` | smallint | 0..3 |
| `confidence` | numeric(4,3) | 0.000..1.000 |
| `text_anonymized` | text | NOT NULL (pós-anonimização) |
| `pii_tokens` | jsonb | DEFAULT `[]` (tokens `pii:cat:hash`) |
| `attributes` | jsonb | DEFAULT `{}` (livre) |
| `iso_37120` | jsonb | DEFAULT `[]` |
| `iso_37122` | jsonb | DEFAULT `[]` |
| `embedding` | vector(1024) | NULL (preenchido em fase RAG) |
| `status` | text | CHECK IN (`classified`,`quarantined`,`reprocessing`) |
| `created_at` | timestamptz | DEFAULT now() |
| `updated_at` | timestamptz | DEFAULT now() |

Índices:

- `idx_events_source_received` ON (source_id, received_at DESC)
- `idx_events_topic_received` ON (topic, received_at DESC)
- `idx_events_region` ON (region_code)
- `idx_events_status` ON (status) WHERE status <> `classified`
- `idx_events_embedding` USING ivfflat (embedding vector_cosine_ops) WITH (lists=100)
- `idx_events_attributes_gin` USING gin (attributes jsonb_path_ops)

Constraints adicionais: `text_anonymized` não pode conter padrões PII;
falhas vão para `quarantined`.

---

## 3. `pii_vault.pii_vault_records`

Schema separado, RBAC restrito.

| Campo | Tipo | Constraints |
|-------|------|-------------|
| `token` | text | PK (`pii:<cat>:<hash>`) |
| `category` | text | CHECK IN (`cpf`,`cns`,`name`,`email`,`phone`,`address`) |
| `value_ciphertext` | bytea | NOT NULL (AES-GCM) |
| `value_iv` | bytea | NOT NULL |
| `key_version` | smallint | NOT NULL |
| `first_seen_at` | timestamptz | DEFAULT now() |
| `last_seen_at` | timestamptz | DEFAULT now() |
| `usage_count` | bigint | DEFAULT 1 |
| `expires_at` | timestamptz | NULL (per Source.retention_policy) |

Índices: `idx_pii_category`, `idx_pii_expires_at`.

Acesso somente a roles `lgpd_officer`, `audit_admin`; toda leitura
emite `AuditEntry` com `action=pii.reidentify`.

---

## 4. `telemetry.pipeline_runs`

| Campo | Tipo | Constraints |
|-------|------|-------------|
| `id` | uuid | PK |
| `source_id` | uuid | FK telemetry.sources.id |
| `started_at` | timestamptz | DEFAULT now() |
| `finished_at` | timestamptz | NULL |
| `status` | text | CHECK IN (`running`,`succeeded`,`partial`,`failed`) |
| `events_collected` | int | DEFAULT 0 |
| `events_quarantined` | int | DEFAULT 0 |
| `error_summary` | text | NULL |
| `metrics` | jsonb | DEFAULT `{}` (latency p50/p95, retries) |

Índice: `idx_pipeline_runs_source_started` ON (source_id, started_at DESC).

Tabela auxiliar `telemetry.pipeline_run_events(pipeline_run_id, event_id)`
com PK composta para rastrear N:N.

---

## 5. `audit.audit_entries`

Append-only (sem UPDATE/DELETE; trigger garante).

| Campo | Tipo | Constraints |
|-------|------|-------------|
| `id` | uuid | PK |
| `at` | timestamptz | DEFAULT now() |
| `actor_id` | text | NOT NULL (user id, system, worker name) |
| `actor_role` | text | NULL |
| `action` | text | NOT NULL (`event.classify`, `pii.reidentify`, `egress.grok`) |
| `target_kind` | text | NOT NULL (`event`, `pii_record`, `source`) |
| `target_id` | text | NOT NULL |
| `payload_hash` | text | sha256 do payload (sem dados em claro) |
| `metadata` | jsonb | DEFAULT `{}` |
| `prev_hash` | text | hash do registro anterior (cadeia) |

Índices: `idx_audit_at`, `idx_audit_target`, `idx_audit_actor`.

Trigger `audit_immutable` rejeita UPDATE/DELETE; cadeia hash é
recomputada em `retention_sweep` para detectar tampering.

---

## State transitions (`TelemetryEvent.status`)

```
ingested -> anonymized -> classified
                       \-> quarantined  (anonimização falhou)
classified -> reprocessing -> classified  (operador disparou /events:reprocess)
```

`quarantined` exige laudo manual via API admin e gera alerta.

---

## Validation rules (resumo, derivadas de FR-001..FR-013)

- FR-002: `text_anonymized` é o único campo textual exposto a downstream.
- FR-003: `confidence < 0.6` ⇒ `severity` rebaixado e flag
  `low_confidence` em `attributes`.
- FR-008: cada egress externo (Grok) gera `AuditEntry` com
  `action=egress.grok`.
- FR-013: tentativa de gravar PII no schema `telemetry` falha por trigger
  (recognizer Presidio executado server-side antes do INSERT).
