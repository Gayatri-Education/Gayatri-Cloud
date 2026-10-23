# Gayatri Cloud — Supporting Documents Pack

**Purpose:** Companion control and design documents for `GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`.
**Status:** Initial baseline. Open decisions remain open; this pack does not imply owner approval.
**Prepared:** 24 October 2026

## How to install this pack locally

1. Extract this archive into the root of the new Gayatri Cloud/Web project directory.
2. Place `GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` in that same root directory. The master plan is intentionally not duplicated in this archive.
3. Keep `AGENTS.md`, `CHANGELOG.md` and `docs/` at the paths shown in this pack. Do not rename control files after work begins without recording a change.
4. Before any implementation, open `AGENTS.md`, the master plan, `docs/agent/CURRENT_STATE.md`, `docs/agent/PROGRESS.md`, and `docs/agent/DECISION_LOG.md`.
5. Begin at P00 (repository discovery and decision freeze). This pack is not an instruction to start coding immediately.

## Document index

| Path | Purpose | Update rule |
|---|---|---|
| `AGENTS.md` | Permanent local AI-agent rules and context-resume protocol | Read before every task; change only through an explicit documented update |
| `CHANGELOG.md` | Human-readable record of completed changes | Update on each GREEN phase or meaningful release event |
| `docs/agent/PROGRESS.md` | Phase status ledger and next-action pointer | Update at the end of every session and phase |
| `docs/agent/CURRENT_STATE.md` | Short durable hand-off checkpoint | Update before stopping, especially after context loss or a failed run |
| `docs/agent/DECISION_LOG.md` | Approved, provisional and open decisions | Update whenever a decision is discussed, proposed, approved or superseded |
| `docs/agent/REQUIREMENTS_TRACEABILITY.md` | Requirements mapped to phases, implementation evidence and tests | Update with requirement, phase or test changes |
| `docs/agent/PHASE_LOG_TEMPLATE.md` | Standard work log for every phase/subphase | Copy for every phase; never overwrite old phase logs |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Component boundaries, data flows and trust boundaries | Update when architecture changes; owner approval for material changes |
| `docs/architecture/ADR-001-WEB-STACK-SELECTION.md` | Architecture Decision Record: Web framework, backend, and testing stack selection | Immutable once approved |
| `docs/architecture/REFERENCE_INVENTORY_AND_REUSE_BOUNDARY.md` | Reference repository inventory, capabilities, and rebuild vs. reuse boundary | Update when reference capabilities or reuse boundaries evolve |
| `docs/architecture/DATA_MODEL.md` | Logical entities, relationships, tenant scope and retention notes | Update before or with schema changes |
| `docs/security/SECURITY_AND_PRIVACY.md` | Threat model, roles, secrets, student/minor data, privacy controls | Update with any security/privacy change |
| `docs/ai/PROVIDER_AND_MODEL_ROUTING.md` | Provider abstraction, model catalog and tutor model selection | Update with AI gateway/routing changes |
| `docs/data/EVENT_AND_TRAINING_PIPELINE.md` | Event capture, archival, eligibility and dataset provenance | Update with event schema or training changes |
| `docs/testing/TEST_STRATEGY.md` | Test layers, test data, regression and GREEN gates | Update as test commands and coverage become known |
| `docs/operations/LOCAL_DEVELOPMENT.md` | Local environment and safe development boundaries | Update once stack and commands are confirmed in P01 |
| `docs/operations/DEPLOYMENT_AND_RECOVERY.md` | Proposed AWS layout, release, backup/restore and incident handling | Update before deployment and after verified operational changes |

## State vocabulary

Use these values consistently: `NOT_STARTED`, `PLANNED`, `IN_PROGRESS`, `TESTING`, `DEBUGGING`, `BLOCKED`, `GREEN`, `AWAITING_OWNER`, and `DEFERRED`. Do not use a generic `DONE` state.

## Important status distinction

The plan is a **requirements and execution baseline**, not evidence that any capability exists. The initial implementation repository may be empty or contain a scaffold. The agent must discover actual files and test output before recording implementation claims. All open decisions in `DECISION_LOG.md` remain open until an explicit owner decision is written there.
