# Implementation Plan: [FEATURE]

**Branch:** `[###-feature-name]` | **Date:** [DATE] | **Spec:** [link]
**Input:** Feature specification from `specs/[###-feature-name]/spec.md`

## Execution Flow (/plan command scope)

1. Load feature spec from Input path.
2. Fill Technical Context (resolve any NEEDS CLARIFICATION first).
3. Run Constitution Check (block if any violation lacks justification in
   Complexity Tracking).
4. Execute Phase 0 → research.md.
5. Execute Phase 1 → data-model.md, contracts/, quickstart.md.
6. Re-evaluate Constitution Check (post-design).
7. Plan Phase 2 → describe task generation approach (do NOT create tasks.md
   here; that is handled by /tasks).
8. STOP — ready for /tasks command.

## Summary

[Brief description from spec + primary technical approach.]

## Technical Context

- **Language/Runtime:** [e.g., Python 3.12, Node 20]
- **Primary Frameworks:** [e.g., FastAPI, Next.js 14, LangGraph]
- **Storage:** [e.g., PostgreSQL 16, pgvector, MinIO]
- **LLM Provider:** [e.g., Grok via xAI API (MVP) → NVIDIA NIM on-prem (post-MVP)]
- **Auth:** [e.g., JWT stub (MVP) with OIDC adapter interface]
- **Testing:** [e.g., pytest, Playwright, Vitest]
- **Target Deployment:** [NowGo AI Platform on-premise / Docker Compose dev]
- **Performance Goals:** [e.g., p95 < 300ms for queries; ingestion ≥ 100 ev/s]
- **Constraints:** [LGPD, on-prem, air-gap-ready]

## Constitution Check

[Restate from spec + any new findings; if violations, document in
Complexity Tracking with justification.]

## Project Structure

### Documentation (this feature)

specs/[###-feature]/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
  tasks.md  (created by /tasks)

### Source Code (repository root)

[Describe target directories, e.g.:]
backend/
  src/<module>/
  tests/
frontend/
  src/<module>/
  tests/

## Phase 0: Research

Output: research.md — resolved unknowns, technology decisions with
rationale, alternatives considered.

## Phase 1: Design & Contracts

Outputs:
- data-model.md (entities, fields, relationships, validation rules)
- contracts/ (OpenAPI/GraphQL/event schemas)
- quickstart.md (end-to-end smoke test scenario)
- contract tests (failing) ready for /tasks to schedule

## Phase 2: Task Planning Approach

[Describe how /tasks will derive tasks from contracts, data model and
quickstart. DO NOT enumerate tasks here.]

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|

## Progress Tracking

- [ ] Phase 0: Research complete
- [ ] Phase 1: Design complete
- [ ] Phase 2: Task planning approach described
- [ ] Initial Constitution Check passed
- [ ] Post-Design Constitution Check passed
- [ ] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented
