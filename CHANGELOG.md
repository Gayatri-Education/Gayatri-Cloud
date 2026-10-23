# Changelog — Gayatri Cloud/Web

All notable project changes should be recorded here. This file starts as a planning baseline; it must not imply code has been implemented.

## [P02] — Persistence, Schema and Migrations — 2026-10-24

### Added
- Complete SQLAlchemy 2.0 async declarative schema across 6 core domains:
  - Identity: `UserAccount`, `AuthIdentity`, `SessionDevice`
  - Organization: `Organization`, `OrganizationDomain`, `Membership`, `RoleAssignment`, `Invitation`, `GuardianRelationship`
  - Academic & Content: `Course`, `CourseVersion`, `CourseOffering`, `ClassGroup`, `CourseEnrollment`, `TeachingAssignment`, `TeacherInstruction`, `ContentSource`, `ContentChunk`
  - Tutoring & Assessment: `TutorSession`, `ConversationTurn`, `Assessment`, `AssessmentAttempt`, `AssessmentResponse`, `LearningEvent`, `CanonicalLearningState`, `MisconceptionRecord`
  - AI & Usage: `ProviderConnection`, `ProviderModelSnapshot`, `ModelPolicy`, `AIExecutionUsage`
  - Events & Outbox: `ApplicationEvent`, `EventOutbox`
- Asynchronous database engine and session factory with connection pooling and dialect compatibility (`backend/app/db/session.py`).
- Tenant-scoped repository base (`BaseTenantRepository`) enforcing organization-boundary predicates on all queries and mutations.
- Synthetic seed fixtures (`seed_synthetic_tenants`) for reproducible, isolated test environments.
- Alembic migration environment and baseline migration script (`backend/alembic/versions/001_initial_schema.py`).
- Test suites verifying table constraints, soft-delete lifecycle, transaction rollback safety, and cross-tenant isolation.

### Verification
- Phase: `P02` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (16 passed in 5.17s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 25 files).
- Zero secrets committed.

## [P01] — Local Project Foundation and CI — 2026-10-24

### Added
- Git repository initialized on `main` branch with origin `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.
- Monorepo structure with `backend/` (FastAPI / Python 3.12) and `frontend/` (Next.js / TypeScript / Tailwind CSS).
- ADR-001 recording full web stack and architectural choices (`docs/architecture/ADR-001-WEB-STACK-SELECTION.md`).
- Application entrypoint in `backend/app/main.py` with `/health` and `/ready` probes, `X-Request-ID` correlation middleware, process timing, and OWASP defensive security headers.
- Configuration module in `backend/app/core/config.py` with Pydantic Settings, secret masking, and environment validation.
- Safe environment template in `.env.example` with placeholders for DB, S3, JWT, and AI providers.
- Test suites in `backend/tests/` verifying health contracts, correlation IDs, security headers, and configuration parsing.
- Next.js frontend scaffold in `frontend/` with landing page, typed API client, and Vitest suite.
- GitHub Actions CI workflow in `.github/workflows/ci.yml` testing backend, frontend, and repository security integrity.
- Local developer runbook updated in `docs/operations/LOCAL_DEVELOPMENT.md`.

### Verification
- Phase: `P01` — status: `GREEN`
- Acceptance criteria: 9/9 passed.
- Tests: `python -m pytest backend/tests -v` (8 passed in 0.30s).
- Linter: `ruff check` and `ruff format --check` (100% clean).
- Zero secrets committed.

## [P00] — Repository Discovery and Decision Freeze — 2026-10-24

### Added
- Completed discovery of reference repository `Gayatri AI - Godess of Knowledge` (`Gayatri-Education/Gayatri`).
- Created `docs/architecture/REFERENCE_INVENTORY_AND_REUSE_BOUNDARY.md` mapping all 37 service modules, 70+ test suites, and defining domain reuse vs. web rebuild boundaries.
- Created `gayatri_cloud_agent_goal.md` autonomous execution plan for all 21 phases with strict quality gates, full repo audit requirements, and git push instructions.
- Decision approvals recorded in `docs/agent/DECISION_LOG.md`: DEC-001 (RDS PostgreSQL + S3), DEC-002 (Gayatri-Education/Gayatri-Cloud remote), DEC-003 (Next.js/React + FastAPI web stack), DEC-011 (Deny-by-default training data governance).

### Verification
- Phase: `P00` — status: `GREEN`
- Acceptance criteria: 5/5 passed with verified evidence in `docs/agent/phase-logs/P00.md`.
- No application code written in P00.

## [Unreleased] — Planning baseline — 2026-10-24

### Added
- Master phase-by-phase development contract (maintained separately as `GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`).
- Companion documents for agent execution, resumability, requirements traceability, architecture, data, AI routing, event/training governance, testing and operations.
- Explicit decision tracking so recommendations are not mistaken for approved requirements.

### Not implemented
- No application code is represented by this entry.
- No AWS infrastructure has been provisioned.
- No AI provider has been connected and no model has been trained.

## Entry template

### Added
- ...
### Changed
- ...
### Fixed
- ...
### Security / privacy
- ...
### Verification
- Phase: `Pxx` — status: `GREEN` / `AWAITING_OWNER`
- Tests run and results: ...
- Evidence: phase log/test artifacts/commit ...
