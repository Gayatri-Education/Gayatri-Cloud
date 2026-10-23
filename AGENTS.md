# AGENTS.md — Gayatri Cloud Local AI Agent Contract

## 1. Mission

Build the Gayatri Cloud/Web product according to `GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` and the companion documents in `docs/`. The platform is a cloud-first, course-independent adaptive education system for independent learners and institutions, with student, teacher, parent/guardian, course/academic-admin, organization-admin and platform-super-admin capabilities.

The existing `https://github.com/Gayatri-Education/Gayatri` repository is a functional reference, not proof that a feature works and not permission to edit or destroy that source. The web app is a fresh implementation. Reuse behavior/contracts only after inspection, compatibility review, licensing review and tests.

## 2. Required task order

For every phase and every resumed work packet:

1. Read the master phase plan through the active phase.
2. Read this file, `docs/agent/CURRENT_STATE.md`, `docs/agent/PROGRESS.md`, `docs/agent/DECISION_LOG.md`, and the relevant design/test documents.
3. Inspect repository status and recent diff. Never rely solely on conversation memory.
4. Invoke `/plan` if available. If not available, write the equivalent plan into the phase log before editing.
5. Identify the smallest scope that meets the active phase's acceptance criteria. List proposed files, risks, assumptions, commands and stop conditions.
6. Resolve blockers. Record unresolved choices in the decision log as `OPEN`; do not silently assume an answer.
7. Implement only the approved active phase. Add tests alongside behavior.
8. Run targeted tests first; debug failures at root cause; rerun targeted tests; then run the required regression checks.
9. Review diff, secrets, tenant isolation, privacy exposure, migrations and error handling.
10. Update the phase log, progress tracker, current-state checkpoint, traceability matrix and changelog as applicable.
11. Mark `GREEN` only when all required acceptance criteria have evidence and all required tests pass. If owner approval is required, use `AWAITING_OWNER` instead.
12. Stop. Report the phase result and the exact next action. Do not start the next phase automatically.

## 3. Status values

Use only: `NOT_STARTED`, `PLANNED`, `IN_PROGRESS`, `TESTING`, `DEBUGGING`, `BLOCKED`, `GREEN`, `AWAITING_OWNER`, `DEFERRED`.
A skipped or unrun test is not a pass. A command that did not execute is not evidence. An external integration blocked by missing credentials may be `BLOCKED`, while deterministic mock-based tests can still pass.

## 4. Non-negotiable rules

- Never code multiple unbounded phases in one task.
- Never remove, weaken, skip or rewrite a failing test merely to get a green result. If an existing test is incorrect, document proof and obtain approval for the change.
- Never claim that a feature, benchmark, API call, deployment, migration, security review or user journey passed without concrete execution evidence.
- Never commit real API keys, passwords, private certificates, production data, personal student data or a populated secrets file. Use example names and test fixtures.
- Never send prompts, responses, retrieved documents or learning records to a provider unless the provider, key scope, privacy policy and applicable consent/authorization permit it.
- Never use real student conversations for general-model training while the training-eligibility decision is open.
- Never enable cross-tenant access based solely on email-domain matching. A domain match is not an administrator role or proof of course entitlement.
- Never let the browser receive provider secrets. AI-provider calls are server-side.
- Never allow a student to act as a teacher in conflict with the explicit owner rule. Teacher + parent is permitted. Other cross-role compatibility must follow a recorded approved decision.
- Never allow one organization to retrieve another organization's records by changing IDs, URLs, request bodies, search filters or file references.
- Never store only files in S3 and assume transactional database behavior exists. The proposed RDS PostgreSQL + S3 architecture is recommended but requires owner approval before paid provisioning.
- Do not provision AWS resources, enable live payments, run paid bulk API tests, execute a paid training job or deploy publicly without explicit authorization.
- Do not run destructive schema/data migrations unless backups, rollback strategy and approval requirements are satisfied.
- Avoid unrelated refactors and unrequested features. Record enhancements as proposals.
- Do not mark a phase GREEN while required acceptance criteria are missing, required checks fail, or a security/privacy issue remains unexplained.

## 5. Decision discipline

Each nontrivial assumption must cite a decision ID from `DECISION_LOG.md`. Allowed labels:
- `OWNER_CONFIRMED`: explicit user decision.
- `RECOMMENDED_PENDING_APPROVAL`: suggested design, not yet approved.
- `OPEN`: must not be treated as settled.
- `APPROVED`: owner decision captured with date and rationale.
- `SUPERSEDED`: replaced by a newer decision ID; preserve history.

A reversible, local-only implementation may use an explicitly recorded provisional interface or mock. A privacy-sensitive, destructive, costly or architecture-locking choice must stop for owner approval.

## 6. Gemini context-window and resume protocol

When the conversation/context is lost, do not begin by asking the user to repeat prior decisions and do not begin by coding. Reconstruct state from files:

1. Read `GAYATRI_CLOUD_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md`.
2. Read this `AGENTS.md`.
3. Read `docs/agent/CURRENT_STATE.md` and `docs/agent/PROGRESS.md`.
4. Read `docs/agent/DECISION_LOG.md` entries referenced by the active phase.
5. Read the active phase log, applicable architecture/security/data/test documents and latest test evidence.
6. Inspect `git status`, recent commits and the diff since the last green checkpoint.
7. Verify the last claimed test state with available logs; do not presume the checkpoint is accurate if repository state conflicts.
8. State internally (or in the phase log) the active phase, latest verified GREEN phase, current failing/broken behavior, unresolved blockers and one next action.
9. Resume the first incomplete step. Never repeat completed work without a reason. Never advance on memory alone.

Keep a phase small enough for the active context. If too large, propose a clearly bounded subphase (`P06a`, `P06b`) and update the master plan/progress/traceability before starting that subphase. Keep `CURRENT_STATE.md` brief and durable; put details in phase logs and technical documents.

## 7. Failure and diagnostic requirements

User-facing errors must be helpful and safe. Technical logs should have structured categories, request/correlation IDs, timestamps, component, retryability and redacted diagnostics. Do not log raw secrets or unnecessarily duplicate sensitive prompts. Failures must not be swallowed. Retried actions must be idempotent where possible. A failed operation must not partially update learning state or assessment records without an explicitly designed transaction/compensation strategy.

## 8. Quality and test gates

Use this cycle exactly: `/plan` → implement → targeted test → debug → targeted retest → regression test → diff/security review → checkpoint. Add integration and end-to-end tests at the relevant phases. A phase must have:
- recorded acceptance criteria;
- exact test commands and outcomes;
- known limitations and blocked tests;
- updated traceability;
- no unexplained failure;
- a status of `GREEN` or `AWAITING_OWNER` with rationale.

## 9. Required checkpoint contents

At minimum, update `CURRENT_STATE.md` with: date/time and timezone, active phase, last GREEN phase, branch/commit if available, files changed, tests actually run, outcome, open blockers/decisions, known defect IDs, and exactly one next action. Update `PROGRESS.md` with phase state and criteria counts. Preserve full test output in a phase log or test-artifact location when feasible.

## 10. Communication format at phase closeout

Report: status, scope delivered, files changed, tests executed (exact names/commands and outcomes), unresolved issues, decision IDs needing owner input, migration/security notes, and next action. Do not claim a complete product when only one phase passed. No phase advancement without a GREEN gate and stop point.
