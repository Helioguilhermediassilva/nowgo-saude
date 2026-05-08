# Feature Specification: [FEATURE NAME]

**Feature Branch:** `[###-feature-name]`
**Created:** [DATE]
**Status:** Draft
**Input:** User description: "$ARGUMENTS"

## Execution Flow (main)

1. Parse user description from Input.
2. Extract key concepts (actors, actions, data, constraints).
3. For each unclear aspect, mark `[NEEDS CLARIFICATION: question]`.
4. Fill User Scenarios & Testing.
5. Generate Functional Requirements (each MUST be testable).
6. Identify Key Entities (if data is involved).
7. Run Review Checklist.
8. Return: SUCCESS if spec is ready for planning.

---

## ⚡ Quick Guidelines

- ✅ Focus on WHAT users need and WHY.
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure).
- 👥 Written for business stakeholders, not developers.
- 🔒 Constitution must be checked before SUCCESS (see Constitution Check).

### Section Requirements

- **Mandatory sections:** must be completed for every feature.
- **Optional sections:** include only when relevant.
- When a section does not apply, remove it (do not leave "N/A").

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

[Describe the main user journey in plain language.]

### Acceptance Scenarios

1. **Given** [initial state], **When** [action], **Then** [expected outcome].
2. **Given** [initial state], **When** [action], **Then** [expected outcome].

### Edge Cases

- What happens when [boundary condition]?
- How does the system handle [error scenario]?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001:** System MUST [specific capability, e.g., "ingest ouvidoria
  records via REST API"].
- **FR-002:** System MUST [specific capability].
- **FR-003:** Users MUST be able to [interaction].
- **FR-004:** System MUST [data requirement].
- **FR-005:** System MUST [behavior, e.g., "anonymize PII before any LLM call"].

*Mark unclear requirements as:*

- **FR-006:** System MUST authenticate users via [NEEDS CLARIFICATION: auth
  method — gov.br OIDC, AD-GDF, JWT stub?].

### Non-Functional Requirements *(when applicable)*

- **NFR-001:** [performance, availability, latency target]
- **NFR-002:** [security/compliance, e.g., "LGPD Art. 11 compliant"]
- **NFR-003:** [observability, e.g., "all decisions emit OpenTelemetry span"]

### Key Entities *(include if feature involves data)*

- **[Entity 1]:** [what it represents, key attributes without
  implementation details].
- **[Entity 2]:** [relationships to other entities].

---

## Constitution Check *(mandatory)*

For each applicable principle, declare adherence or justified deviation:

- [ ] **I. Soberania:** [statement on data residency / external API usage]
- [ ] **II. LGPD by Design:** [legal basis, anonymization approach, retention]
- [ ] **III. Guardrails de Finalidade:** [scope restriction approach]
- [ ] **IV. IA Não-Clínica:** [confirms no diagnosis/prescription]
- [ ] **V. Cidadão como Sensor:** [how citizen perception is treated]
- [ ] **VI. Smart City Standards:** [ISO/ITU/IMD mapping if KPIs are exposed]
- [ ] **VII. Observabilidade:** [audit trail, tracing approach]
- [ ] **VIII. AI-Amplified Workflow:** [Spec → Plan → Tasks compliance]
- [ ] **IX. Segurança:** [auth, RBAC, encryption, threat model summary]

---

## Review & Acceptance Checklist

### Content Quality

- [ ] No implementation details (languages, frameworks, APIs).
- [ ] Focused on user value and business needs.
- [ ] Written for non-technical stakeholders.
- [ ] All mandatory sections completed.

### Requirement Completeness

- [ ] No `[NEEDS CLARIFICATION]` markers remain.
- [ ] Requirements are testable and unambiguous.
- [ ] Success criteria are measurable.
- [ ] Scope is clearly bounded.
- [ ] Dependencies and assumptions identified.

---

## Execution Status

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Constitution Check passed
- [ ] Review checklist passed
