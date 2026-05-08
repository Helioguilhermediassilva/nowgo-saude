# Tasks: [FEATURE]

**Input:** Design documents from `specs/[###-feature-name]/`
**Prerequisites:** plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (/tasks command)

1. Load plan.md, data-model.md, contracts/, research.md, quickstart.md.
2. Generate tasks by category (Setup → Tests → Core → Integration → Polish).
3. Apply task rules: tests before implementation; mark [P] for parallel
   when tasks touch independent files; same file = sequential.
4. Number tasks sequentially (T001, T002, ...).
5. Validate: every contract has a test; every entity has a model task;
   every endpoint has implementation.

## Format: `[ID] [P?] Description`

- **[P]:** can run in parallel (different files, no dependencies)
- Always include exact file path in the description.

## Path Conventions

- **Backend:** `backend/src/`, `backend/tests/`
- **Frontend:** `frontend/src/`, `frontend/tests/`
- **Workers:** `workers/src/`, `workers/tests/`
- Adjust per plan.md before generating tasks.

## Phase 3.1: Setup

- [ ] **T001** Create project structure per plan.md.
- [ ] **T002** Initialize dependencies (lockfiles, virtualenv, package manager).
- [ ] **T003** [P] Configure linting, formatting, pre-commit hooks.

## Phase 3.2: Tests First (TDD) — MUST complete before 3.3

- [ ] **T004** [P] Contract test for [endpoint/contract] in `tests/contract/...`
- [ ] **T005** [P] Integration test for [user story] in `tests/integration/...`

## Phase 3.3: Core Implementation (only after tests are failing)

- [ ] **T006** [P] Model [Entity] in `src/models/...`
- [ ] **T007** [P] Service [Service] in `src/services/...`
- [ ] **T008** Endpoint [METHOD /path] in `src/api/...`

## Phase 3.4: Integration

- [ ] **T009** Wire persistence layer.
- [ ] **T010** Wire observability (OpenTelemetry, audit log).
- [ ] **T011** Wire security (auth middleware, rate limit, WAF rules).

## Phase 3.5: Polish

- [ ] **T012** [P] Unit tests for edge cases.
- [ ] **T013** Performance validation against plan.md targets.
- [ ] **T014** [P] Update quickstart.md with verified steps.

## Dependencies

- Tests (T004–T005) BEFORE implementation (T006–T008).
- Models BEFORE services BEFORE endpoints.
- Implementation BEFORE polish.

## Validation Checklist

- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks are truly independent
- [ ] Each task specifies exact file path
- [ ] No two [P] tasks modify the same file
