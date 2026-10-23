# Gayatri Cloud — Phase-by-Phase Development Plan

**Document type:** Master implementation plan and execution contract for a local AI coding agent  
**Product:** Gayatri Cloud / Gayatri Web  
**Status:** Planning baseline; owner decisions marked as pending must not be silently converted into approved requirements  
**Version:** 1.0  
**Date:** 24 October 2026  
**Execution model:** One bounded phase at a time; `/plan` → implement → test → debug → regression test → checkpoint → advance only when GREEN

---

## 0. Purpose and operating contract

This document directs a local AI coding agent (for example, Gemini in a local IDE/CLI) to develop a cloud-first web version of Gayatri. It is deliberately organized into small, gated phases so that work can be resumed after context loss without depending on a long conversation history.

This file is the **master phase plan**. Companion documents such as the agent rules, decision log, progress tracker, architecture specification, data model, traceability matrix, test strategy and deployment runbook will be created separately. The agent must use those companion documents when available. It must not invent a missing document's contents and must not claim that a decision is approved merely because it appears in this plan as a recommendation.

### 0.1 Non-negotiable execution rules

1. **Never implement multiple phases in one undifferentiated task.** Work only on the active phase and its explicitly approved dependencies.
2. **Start every phase with `/plan`.** If the active environment has a `/plan` command, invoke it. If it does not, produce the same structured plan in the phase log before editing code.
3. **Inspect before editing.** Read this master plan, the progress tracker, the decision log, current-state checkpoint and the active phase's requirements. Inspect the relevant repository code and tests. Do not rely on memory of previous chats.
4. **Use evidence, not repository claims.** The existing Gayatri repository and its documentation describe expected behavior, but the agent must inspect implementation and tests before labeling a feature “implemented” or “working”.
5. **Plan → code → test → debug → retest.** No phase is GREEN while any required test fails, is skipped without an approved reason, or has an unexplained warning that affects the phase.
6. **Run the smallest relevant tests first, then regression tests.** Fix failures; do not weaken, delete or bypass tests merely to obtain a green run.
7. **No silent failures.** Failures must have a stable error category, a user-safe message, useful redacted diagnostics, a retryability decision where applicable, and a trace/correlation identifier.
8. **Do not guess.** Record uncertainty as `OPEN` or `PROVISIONAL` in the decision log. Ask the owner when a decision is blocking, security-sensitive, expensive, destructive, or changes user data semantics. Reversible local development may proceed under a clearly documented provisional choice.
9. **Do not deploy or spend money without authorization.** Local development, local test services and infrastructure plans are allowed. Do not create AWS resources, call paid APIs in bulk, run model-training jobs, configure a paid payment gateway, or deploy publicly unless explicitly authorized.
10. **No real secrets in the repository.** Never commit API keys, credentials, private student data, production exports, or `.env` files containing secrets. Use test credentials or mocks.
11. **Protect source history.** Treat `https://github.com/Gayatri-Education/Gayatri` as a functional/reference source. Do not rewrite or delete it while working on the new web product. Repository placement for the new implementation is still subject to owner confirmation; until then, work in a separate local project directory/branch and avoid destructive changes.
12. **Update checkpoint documents at the end of every work session.** Record exactly what changed, what was tested, test outcomes, open defects, the next action and the files that must be reread after context loss.
13. **Stop at phase boundaries.** Once the active phase is GREEN, update progress and stop. Do not automatically begin the next phase in the same uncontrolled task.
14. **No scope inflation.** A useful enhancement that is not a requirement must be logged as a proposal, not slipped into the active phase.
15. **No fake verification.** Do not claim a test, security check, AWS configuration, provider connection, migration, benchmark or user journey passed unless its execution evidence exists.

### 0.2 Required phase cycle

For every phase, repeat this cycle:

**A. `/plan`**
- Read the current master plan and companion control documents.
- Confirm the active phase ID and its prerequisites.
- Inspect relevant files, dependency versions, tests and existing behavior.
- List intended files to add/change, expected behavior, risks, test commands, data migration concerns and acceptance criteria.
- Identify all assumptions and link each one to a decision-log entry.
- Do not begin coding until the plan is scoped and the phase's blockers are resolved or explicitly approved as provisional.

**B. Implement**
- Make the smallest complete change that satisfies the phase.
- Keep modules focused and interfaces documented.
- Add/adjust tests alongside the behavior, not as an afterthought.
- Add structured errors, logs and security checks on failure paths.
- Keep unrelated formatting refactors out of the diff.

**C. Test**
- Run formatting/lint/type checks relevant to the changed area.
- Run the phase's unit tests.
- Run integration tests that exercise persistence, API boundaries or external adapters affected by the phase.
- Run the current regression suite appropriate to the scope.
- Record exact commands and exit codes/results.

**D. Debug and retest**
- For any failure, identify the root cause before editing.
- Fix implementation defects rather than deleting assertions or reducing test coverage.
- Repeat targeted tests after each fix, then rerun the required regression suite.
- If a test cannot run because an external service is unavailable, use a deterministic mock for ordinary CI tests and record the separate integration test as `BLOCKED`—not `PASS`.

**E. Verify and checkpoint**
- Review the diff for secrets, privacy leaks, tenant-boundary bugs, accidental scope changes and migrations that lose data.
- Confirm every acceptance criterion has evidence.
- Update progress, decisions, traceability, test evidence and current-state summary.
- Mark the phase `GREEN` only when its gate is met. A human approval gate stays `AWAITING_OWNER` until approval is recorded.
- Stop and report phase status, tests run, unresolved decisions, known defects and the next exact step.

### 0.3 Phase status vocabulary

Use only these statuses in progress tracking:

- `NOT_STARTED` — no work begun.
- `PLANNED` — scope and test plan written; no implementation committed.
- `IN_PROGRESS` — implementation underway.
- `TESTING` — implementation complete enough for its test pass.
- `DEBUGGING` — one or more required checks failed and are being fixed.
- `BLOCKED` — cannot proceed without an external dependency, owner decision or unavailable environment.
- `GREEN` — phase acceptance criteria pass and evidence is recorded.
- `AWAITING_OWNER` — technically prepared, but an owner decision/approval is required.
- `DEFERRED` — intentionally postponed with reason and impact recorded.

Do not use `DONE` without the more precise `GREEN` or `AWAITING_OWNER` status.

### 0.4 Context-loss and resume protocol

When Gemini or another local agent loses context, the first task is **state reconstruction, not coding**:

1. Re-read this file from the beginning through the active phase.
2. Read the companion documents listed in Section 3, starting with the current-state checkpoint and progress tracker.
3. Read the last completed phase's summary and the active phase's log.
4. Check the Git status and recent diff; never assume files are unchanged.
5. Run a lightweight repository/status check appropriate to the project.
6. State in the private plan what phase is active, what is GREEN, what is failing, and what single action comes next.
7. Resume at the first unfinished step. Do not redo completed work without a reason, and do not advance based solely on conversation memory.

Keep each agent work packet small enough to fit comfortably into the available context. Prefer one phase per agent session. If a phase would touch too many unrelated components, split it into numbered subphases (for example `P06a`, `P06b`) and update this plan before coding. Each checkpoint must be concise and durable; long reasoning belongs in the relevant design document, not the resume note.

---

## 1. Product goal and scope

### 1.1 Product goal

Build Gayatri as a **cloud-first, course-independent adaptive education platform** accessible through a responsive web application. Individuals may learn independently and may also join schools or organizations. The same account may have multiple organization memberships with different role assignments. Students, teachers, parents/guardians, course/academic administrators, organization administrators and platform super administrators receive views and permissions appropriate to their relationships and scope.

The tutor must support multiple subjects and curricula from uploaded and approved learning materials. It must combine retrieval-augmented generation (RAG), configurable teaching approaches, course/teacher instructions, assessment and a validated learning-state engine. It is not just a generic chatbot.

### 1.2 Agreed product behaviors

- Individuals and institutions are both target customers.
- A person has one global account and may have a personal learning space plus memberships in multiple organizations.
- Registration includes self-service and invitation/approval paths; exact join policies must be configurable and documented.
- A teacher may also be a parent/guardian. A person must not have both student and teacher roles under the user's explicit global restriction. Other role combinations require a recorded policy decision.
- Platform-wide super-admin privileges are distinct from organization-admin and course/academic-admin privileges.
- Organization data is tenant-scoped. Organization membership must not silently transfer ownership of a person's personal records.
- Cloud persistence is required for conversations/session data, learning state, assessments, teacher instructions, reports, billing/financial records and audit/event records.
- S3 is required for object/file storage. **RDS PostgreSQL plus S3 is the recommended database baseline**, pending recorded owner approval before production infrastructure is provisioned.
- AI providers are connected through the server-side gateway. The platform should support native providers and compatible custom endpoints.
- Each individual may add their own API provider where policy permits; institutions may also configure provider credentials for their members. API credentials must never be exposed to browser code.
- Users have an automatic model-selection mode and a manual provider/model selector, subject to organization policy.
- The model router should favor educational quality, grounding, context handling, multilingual ability and privacy constraints. “Newest” is a discovery preference, not permission to bypass evaluation or model allowlists.
- The general tutor should use approved course RAG first and may supplement it with model knowledge, clearly distinguishing source-grounded claims from general knowledge.
- Tutoring method is configurable: for example Socratic questioning, direct explanation, practice-first and teacher-defined methods.
- AI evaluations inform learning progression, but progression must go through explicit validation and defined learning rules. A raw model response must not mutate learning state without the platform's validation/commit checks.
- Full tutoring interactions and significant application events must be logged for audit, reliability and potential model training. **Capture permission and training eligibility are separate concepts.**
- The first release targets any grade, subject or curriculum, eight UI languages, responsive desktop/mobile web, and offline reading of previously cached lessons/material. Full offline AI inference is not required for the web version.
- The launch scope includes student, teacher, parent, organization-admin, course-admin and super-admin functions; assessments; institution fee management; freemium platform entitlements; notifications/communication; analytics; data export/deletion workflows; and model/provider administration.
- The initial deployment may be a limited pilot on a single EC2 instance; estimated launch traffic is 100–1,000 registered users and 50–250 concurrent users. These are sizing inputs, not proof of capacity. Load-test results determine readiness.
- Build in phases but preserve the agreed full feature scope. Do not remove a feature silently to make an early milestone appear complete.

### 1.3 Reference repository

Use `https://github.com/Gayatri-Education/Gayatri` as the functional reference, not as a guarantee that every documented feature works. Inspect at least the following before setting corresponding acceptance tests:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/SECURITY_MODEL.md`
- `docs/PRIVACY_CONTRACT.md`
- `docs/DEPLOYMENT.md`
- `docs/security/RBAC_POLICY_V4.md`
- `central_platform/ai/`
- `central_platform/tutor/`
- `central_platform/rag/`
- `central_platform/courses/`
- `central_platform/learning/`
- `central_platform/assessment/`
- `central_platform/teacher/`
- `central_platform/auth/`
- `central_platform/recovery/`
- relevant migrations and tests

Preserve useful, proven domain behavior and contracts where applicable, but **do not migrate the PySide6 desktop UI into the web application**. Treat this as a fresh web implementation; reuse only code that can be safely licensed, isolated, tested and adapted. Document every substantial reuse/rebuild decision.

---

## 2. Decisions and assumptions: no silent defaults

The following list separates known requirements from decisions not yet confirmed. The agent must update the companion decision log when it is created and must not describe a provisional item as approved.

### 2.1 Confirmed constraints

- Hosting target: AWS EC2.
- Object storage: S3.
- User account model: personal accounts plus organization memberships.
- Provider API calls: server-side.
- Both personal and institutional API-provider connections are in scope.
- Existing Gayatri is the feature reference; the web application is a rebuild.
- Full prompt/response logging is requested.
- Training-data use must be designed into the data pipeline.
- User data deletion should support self-service requests, with reviewed exceptions where retention is required.
- Authentication includes email/password with verification, multi-factor authentication for privileged users, session/device controls, and age/guardian-aware approval capabilities. Any extra social login or institutional SSO must be an explicit addition rather than assumed.
- Parent visibility is institution-policy-controlled. Parents should have progress, summaries, assessment information, time/activity visibility, communication and finance access as authorized; raw full transcripts are not enabled for parents by default.
- Teachers can review records for students they are authorized to teach, with audit logging.
- An institution must not access another tenant's records.

### 2.2 Decisions requiring an ADR and/or owner approval

1. **Database approval:** RDS PostgreSQL + S3 is the recommended baseline. Record approval before provisioning paid AWS resources. Use PostgreSQL-compatible development/test configuration locally where practical.
2. **Repository destination:** recommended separate web/cloud repository or project directory. Until confirmed, leave the source repository unchanged.
3. **Frontend framework and deployment packaging:** inspect existing project and propose a supported stack in an ADR. Do not assume the desktop UI technology is appropriate for web.
4. **Role compatibility beyond the confirmed teacher+parent and student-vs-teacher rule:** define student+parent and admin+teacher combinations explicitly.
5. **Organization joining:** support invitation, membership request/approval and verified-domain flows as configurable capabilities; confirm which are enabled by default and which need manual approval.
6. **Authentication methods:** email/password with verification and required privileged-user MFA are the baseline. Google/Microsoft sign-in, SSO and phone/email OTP remain unapproved until requested.
7. **Provider-key precedence:** define priority between personal and organization keys, who pays for each call, and whether students/minors may supply their own keys. Default proposal: organization's provider policies restrict eligibility; users may choose among permitted keys; show who pays.
8. **Model ranking:** cost/latency tradeoffs and model pinning are not finalized. Default proposal: quality-first routing subject to task capabilities, privacy/allowlist constraints and configured cost/latency ceilings; task-aware choice with an optional session pin.
9. **Model promotion:** new models must pass a task-specific benchmark and configured approval checks before they are eligible for default automatic production routing.
10. **Usage limits conflict:** provider quota/billing is the selected usage authority, while administrators also want model allowlists/cost ceilings. Clarify whether Gayatri may enforce application-level request/token budgets. Until then, do not advertise a Gayatri-enforced quota; expose provider quota errors and policy warnings and avoid requests disallowed by model/cost policy.
11. **Training eligibility:** event capture is required, but whether general-model training can use institution-authorized data only, individual opt-in data, or both remains a blocking governance decision before real student data is used for model training.
12. **Retention periods:** define period and purge policy per category (raw conversation, security/audit log, financial record, source document, training candidate, approved dataset). Do not assume indefinite retention.
13. **Transcript review:** preserve authorized teacher access with audit trails. Decide whether organization administrators may review raw transcripts and under what reason/policy.
14. **Payment provider:** design an adapter interface; do not activate live Razorpay/UPI or another provider until the provider and merchant/settlement requirements are approved.
15. **Launch mode:** current inputs describe a limited initial pilot but also a feature-complete scope. Treat feature completeness and public launch as separate: pilot can gate access, while public release requires production-readiness approval.
16. **Budget, deadline, domain and monthly AWS cost ceiling:** currently open; do not fabricate dates or cost commitments.
17. **Optional inputs:** CSV/XLSX ingestion is not confirmed. Confirm before implementing it as a release requirement. File types explicitly in scope include PDF/scanned PDF, DOCX/PPTX/text, images, approved web sources, Q&A content and video/lecture material.

### 2.3 What the agent may do while a decision is open

- Continue reversible local work that does not lock in the unresolved policy.
- Create an abstraction or interface so a future decision does not require a rewrite.
- Use deterministic mocks and test fixtures instead of live cloud/provider accounts.
- Build schema fields that can express the possible policies, while keeping unsafe/undecided behavior disabled.
- Record a concrete proposal with tradeoffs and wait at the relevant gate before enabling the behavior.

The agent may **not** use real student data in model training, provision paid cloud resources, enable silent cross-tenant/domain access, hard-code a provider as universally best, or perform destructive migrations while a relevant decision is unresolved.

---

## 3. Companion documents required for resumability

These documents will be prepared separately from this master plan. Once present, the agent must keep them consistent with implementation. Names can be adjusted once at project initialization, but must then remain stable.

| Document | Purpose | Update trigger |
|---|---|---|
| `AGENTS.md` or `AI_AGENT_RULES.md` | Permanent coding-agent contract and `/plan` workflow | Only when rules change; always read before work |
| `docs/agent/PROGRESS.md` | Phase status, completion percentage based on acceptance checks, blockers and next action | At every phase/session boundary |
| `docs/agent/CURRENT_STATE.md` | Short resume checkpoint: active phase, branch, latest green commit, failing tests, exact next step | At every session boundary and after major failure |
| `docs/agent/DECISION_LOG.md` | Approved/provisional/open architecture and product decisions with IDs and rationale | Whenever a decision is discussed or changed |
| `docs/agent/REQUIREMENTS_TRACEABILITY.md` | Requirement IDs mapped to phases, implementation locations and tests | Every requirement/test/phase change |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | Components, trust boundaries, data flow, deployment and dependency diagram | Architecture changes |
| `docs/architecture/DATA_MODEL.md` | Entities, relationships, tenant ownership, retention and migrations | Schema changes |
| `docs/security/SECURITY_AND_PRIVACY.md` | Threat model, RBAC, tenant isolation, key handling, minors, consent, retention and deletion | Security/privacy changes |
| `docs/ai/PROVIDER_AND_MODEL_ROUTING.md` | Provider adapters, model catalog, discovery, benchmarks, ranking, fallback and key ownership | AI gateway/routing changes |
| `docs/data/EVENT_AND_TRAINING_PIPELINE.md` | Event schema, reliable ingestion, archiving, eligibility, dataset provenance and training gates | Event/ML pipeline changes |
| `docs/testing/TEST_STRATEGY.md` | Test layers, commands, coverage priorities, test data and release gates | Test approach changes |
| `docs/operations/LOCAL_DEVELOPMENT.md` | Reproducible local setup and service dependencies | Local environment changes |
| `docs/operations/DEPLOYMENT_AND_RECOVERY.md` | EC2/RDS/S3 deployment, secrets, backups, restore, rollback and incident steps | Deployment/operations changes |
| `docs/agent/PHASE_LOG_TEMPLATE.md` | Standard phase plan, execution evidence and closeout structure | At initialization; use for every phase |
| `CHANGELOG.md` | Human-readable completed changes | Each GREEN phase/release milestone |

If these documents are not yet available, the agent may perform Phase 0 discovery only. It must not invent a replacement set that conflicts with the separate supporting-document generation step.

---

## 4. Dependency order and release gates

The implementation sequence is deliberately ordered by dependency, even though many user-visible features are intended for the first release.

| Phase | Name | Main dependency | Required result |
|---|---|---|---|
| P00 | Repository discovery and decision freeze | None | Evidence-backed scope, decisions and baseline |
| P01 | Local project foundation | P00 | Reproducible build/test environment and CI |
| P02 | Persistence, schema and migrations | P01 | PostgreSQL schema, migration discipline and S3 boundary |
| P03 | Authentication and account lifecycle | P02 | Secure identity, sessions and recovery |
| P04 | Organization, membership and RBAC | P03 | Tenant-safe account/membership model |
| P05 | Object storage and course lifecycle | P02–P04 | Upload/storage abstraction and versioned courses |
| P06 | Content ingestion and RAG | P05 | Scoped, version-pinned retrieval |
| P07 | AI provider gateway and credentials | P02–P04 | Secure provider abstraction and model discovery |
| P08 | Model evaluation and routing | P06–P07 | Benchmark-driven routing and safe fallback |
| P09 | Tutor orchestration and adaptive learning | P04, P06, P08 | Validated tutoring lifecycle and learning state |
| P10 | Assessment engine | P04, P06, P09 | Secure assessments and evidence-based evaluation |
| P11 | Event collection and training-data pipeline | P02, P07–P10 | Reconstructable event trail; training remains gated |
| P12 | Student web portal | P03–P11 | End-to-end learner workflows |
| P13 | Teacher and academic-administration portal | P04–P12 | Course/class control, analytics and intervention |
| P14 | Parent and guardian portal | P04, P11–P13 | Verified relationships and privacy-filtered view |
| P15 | Super-admin and organization-admin portal | P04, P07, P11–P14 | Tenant/platform administration and controls |
| P16 | Billing, entitlements and institutional fees | P02–P04, P15 | Subscription/fee workflows with gateway abstraction |
| P17 | Localization, accessibility and offline reading | P12–P16 | Eight UI languages and cached reading |
| P18 | Security, privacy and deletion hardening | All preceding phases | Cross-cutting security tests and lifecycle guarantees |
| P19 | Observability, resilience and recovery | All preceding phases | Actionable diagnostics, backups and recovery drills |
| P20 | Integrated verification and load testing | P01–P19 | End-to-end and capacity evidence |
| P21 | Release packaging and deployment readiness | P20 | Repeatable deployment and owner release gate |

Dependencies are logical, not a license to implement future-phase features early. If a phase discovers a prerequisite defect, fix it in its owning phase or document a narrowly scoped dependency fix before continuing.

---

## 5. Detailed phase specifications

Each phase below has an objective, work scope, tests and an explicit GREEN gate. If a phase is too large for one context window, divide its tasks into subphases without mixing acceptance criteria. Keep unrelated portals and infrastructure out of the same coding session.

### P00 — Repository discovery and decision freeze

**Objective:** Establish verified ground truth before implementation.

**Work:**
1. Inspect the source repository structure, major service boundaries, architectural docs, data-model docs, security policy and tests listed in Section 1.3.
2. Classify every relevant capability as `IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_UNVERIFIED`, `PARTIAL`, `DOCUMENTED_ONLY`, `MISSING` or `NOT_IN_SCOPE`. Cite file paths and test evidence for every meaningful claim.
3. Create a requirement inventory covering identity, organization membership, RBAC, course lifecycle, content processing, RAG, AI routing, tutoring, mastery, assessment, event logging, training, portals, fees, privacy, language support, offline reading and operations.
4. Produce a migration/rebuild map: what is reusable as domain logic, what is only a reference, what needs a new web implementation and what must be removed from scope.
5. List architecture choices for owner approval: frontend framework, database approval, repository destination, login methods, role compatibility, provider-key priority, training eligibility, retention, payment gateway, budget, deployment target and domain.
6. Identify licensing, dependencies, provider adapters and any test or documentation contradictions before copying code.
7. Do not change product code in this phase except harmless inspection tooling approved in the plan.

**Tests/evidence:**
- Repository inventory is reproducible.
- Claims about existing behavior link to implementation and tests, not README text alone.
- Open decisions have an ID, owner, impact and latest safe point for decision.

**GREEN gate:** Owner-facing discovery report and decision list are complete; no high-impact ambiguity is hidden. Any decision that is not needed for local scaffolding is explicitly marked for its later phase gate.

### P01 — Local project foundation and CI

**Objective:** Create a reproducible local development baseline without deploying anything.

**Work:**
1. Confirm the new project directory/repository decision. If unresolved, develop only in a separate local directory/branch and leave the reference repository untouched.
2. Propose and record the frontend, backend, package managers, runtime versions, test framework and build tooling in an ADR. Prefer proven technology compatible with the existing domain logic, but do not assume the desktop UI can be reused as a browser UI.
3. Define app boundaries: frontend, API, domain/application services, persistence interfaces, provider adapters, file storage, background workers and tests.
4. Add dependency lockfiles, formatting/lint/type-checking, test configuration, CI workflow, `.gitignore`, environment-variable example file containing placeholders only and concise local setup instructions.
5. Add `/health` and readiness contracts for local application dependencies, with no secret or internal topology leakage.
6. Establish local deterministic test services: PostgreSQL-compatible database and object-storage/provider fakes or containers as appropriate. Avoid requiring live paid APIs for ordinary tests.
7. Establish migration/test commands and reproducible seed fixtures with synthetic users and courses.

**Tests:** clean setup from documented instructions; lint/type checks; smoke build; minimal API and frontend tests; CI succeeds on a clean checkout.

**GREEN gate:** A new developer can follow the local instructions from a clean clone and run the required checks without manually discovering hidden setup steps. No live AWS credentials or model-provider keys are necessary for normal CI.

### P02 — Persistence, schema and migrations

**Objective:** Define authoritative data storage and migration safety.

**Recommended baseline:** PostgreSQL for transactional records and S3 for object data; production use of RDS is pending owner approval. Use local PostgreSQL for relational integration tests wherever possible.

**Work:**
1. Design and document entities/relations for accounts, identities, organization/tenant records, verified domains, invitations, membership requests, membership/role assignments, guardian links, courses, versions, offerings, classes, enrollments, sources, documents, source chunks/reference metadata, provider connection metadata, model catalog, routing configuration, tutoring sessions/turns/messages, learning events/state, assessments/submissions, invoices/payments, consent/retention policies, audit events and durable event outbox.
2. Use explicit IDs and tenant/owner fields where required. Define uniqueness constraints, foreign keys, lifecycle statuses, timestamps and soft-delete semantics.
3. Keep large binary content and archive objects out of relational tables; store secure object references and metadata.
4. Separate transactional records, immutable/auditable event records and large raw content. Define how a session is reconstructed across these stores.
5. Use versioned forward migrations and a documented rollback/recovery strategy. Do not edit a migration already applied to a shared environment; create a new migration instead.
6. Add repository/data-access interfaces and transaction boundaries. Do not place raw SQL in UI components.
7. Assess PostgreSQL `pgvector` for the initial RAG path. Confirm extension compatibility before making it a required production dependency. Do not create a second database product without measured need.
8. Define index strategy for user/org scoping, time-based events, sessions, course/source version and retrieval paths. Avoid premature optimization unsupported by query plans.

**Tests:** migration up from empty database; migration upgrade from prior schema; constraints and foreign keys; tenant scoping through repository functions; transaction rollback; idempotency and timestamp behavior; backup/restore test fixture where feasible.

**GREEN gate:** Schema is documented; migrations are deterministic and repeatable; no sensitive values are stored in plaintext; transaction boundaries are covered by tests; storage responsibilities are explicit.

### P03 — Authentication and account lifecycle

**Objective:** Secure sign-up, sign-in, session and recovery workflows.

**Work:**
1. Implement the approved baseline sign-in methods. Current confirmed baseline includes email/password, email verification, MFA for privileged users, session/device management and account approval/guardian-aware capabilities. Do not silently add social sign-in, OTP or institutional SSO.
2. Implement password hashing using a reputable contemporary password-hashing scheme through a maintained library; never write custom cryptographic algorithms.
3. Implement email verification, password reset, rate limiting, lockout/abuse controls, session rotation/revocation and secure logout.
4. Require MFA for platform and organization privileged accounts according to the approved policy. Protect recovery paths to the same standard as login paths.
5. Keep identity separate from organization memberships and application roles.
6. Use secure, HttpOnly/SameSite cookies or another documented session mechanism appropriate to the approved architecture. Avoid browser local storage for long-lived privileged tokens unless a reviewed design establishes why it is safe.
7. Support account suspension, deletion request creation and admin-reviewed retention exceptions.
8. Use synthetic mailer/OTP adapters in tests; do not send real messages from automated test runs.

**Tests:** invalid credentials; verified/unverified email flows; reset tokens expired/replayed; session revocation; MFA challenge and recovery; brute-force rate limits; user enumeration resistance; account suspended; authorization after logout; CSRF/session protections as applicable.

**GREEN gate:** Authentication state is enforced server-side; every sensitive action requires valid identity/context; session revocation is effective; all recovery and privileged-login paths pass tests.

### P04 — Organizations, memberships, roles and tenant isolation

**Objective:** Support personal accounts and organization-managed membership without account duplication or cross-tenant leakage.

**Work:**
1. Implement one global account with a personal scope and zero or more organization memberships.
2. Model an organization membership as a relationship with status, role assignments, timestamps, invitation/request provenance and policy version; never encode organization membership only in the email address.
3. Implement invited membership, user-requested membership and verified-domain enrollment as configurable capabilities. If the owner has not approved the default workflow, build the data/API structure and keep unresolved modes disabled or explicitly provisional.
4. Require separate approval for privileged roles. Verified email domain alone must never grant teacher, course-admin, organization-admin or super-admin privileges.
5. Implement organization domain verification and safe handling of personal email accounts invited into an organization.
6. Enforce global rule: a person cannot be both student and teacher. Permit teacher+parent as confirmed. Gate other combinations—such as student+parent and administrator+teacher—on the decision log.
7. Implement platform super-admin, organization-admin, course/academic-admin, teacher, student and parent roles with a permission matrix. Scope org admins to their organization; teachers to assigned classes/courses; parents to verified children; students to their own records.
8. Use server-side policy checks for every API operation, object fetch, export, file access, search/RAG retrieval and background job. Hiding UI controls is not authorization.
9. Support switching active organization context and clearly identify the active context in the UI/API request. Do not let a stale context leak into another tenant.
10. Keep personal learning history separate from organization-owned learning records by default. Add explicit authorized sharing/import pathways later if approved.

**Tests:** cross-tenant negative matrix; access with valid ID but wrong tenant (IDOR); invitation expiry/revocation; verified-domain edge cases; pending/rejected membership; role incompatibility; multi-organization switching; privilege escalation; parent cannot inspect unrelated children; background worker tenant enforcement.

**GREEN gate:** All tenant-isolation tests pass at API, service and persistence boundaries. Every user/org relationship and role is auditable. No role assignment relies solely on the email domain or client-provided role fields.

### P05 — File storage abstraction and course lifecycle

**Objective:** Build safe object storage and generic course/version management.

**Work:**
1. Implement an object-storage interface. Use an S3 adapter for production design and deterministic local/test adapter for development; do not hard-code bucket paths throughout the application.
2. Private object storage by default. Generate short-lived authorized download/upload URLs only where justified; validate authorization before issuing them. Block public bucket access and prevent client-supplied arbitrary object keys.
3. Model generic `Course`, immutable `CourseVersion`, `CourseOffering`, `Class/Group`, `Enrollment`, `CourseSource` and publication/approval lifecycle.
4. Implement draft → review → approved/published → archived transitions with permissions and audit events.
5. Support explicit course visibility and organization ownership. A private course must not become public by default.
6. Upload path: request authorization → size/type limits → quarantine/staging → content validation/malware check where available → processing state → approval/publish.
7. Support explicitly selected types: PDF and scanned PDF, DOCX/PPTX/text, images, approved URLs/web sources, curated Q&A content and video/lecture materials. CSV/XLSX support stays pending until confirmed.
8. Store checksums, MIME type, file size, source URI where applicable, uploader, tenant, course version, ingestion status and retention classification.
9. Design resumable/retryable processing statuses; never mark an upload successful while extraction/indexing failed silently.

**Tests:** MIME spoofing, oversized file, path traversal, unsafe URL, unauthorized cross-tenant download, version pinning, deletion reference integrity, corrupt upload, interrupted upload, draft publication permissions and retry behavior.

**GREEN gate:** Files are private and scoped, course versions are immutable/versioned, and failed ingestion is visible and recoverable.

### P06 — Content ingestion, indexing and course-scoped RAG

**Objective:** Make uploaded curriculum useful to the tutor without source leakage between courses or tenants.

**Work:**
1. Implement independent processors for each approved source format. Use maintained parsing libraries and isolate expensive/untrusted file processing from the request thread.
2. For scanned PDFs and images, determine the OCR strategy in an ADR. Preserve extraction confidence and route low-quality outputs for retry or review rather than treating garbled text as authoritative.
3. For video/lecture sources, process supplied transcripts or approved transcription output. Do not assume a paid transcription provider; hide provider choice behind an adapter.
4. Split text with page/section/source metadata and stable chunk IDs. Preserve formulas, headings, image references, tables and citations as far as the format and selected tooling allow.
5. Use hybrid retrieval (semantic/vector plus lexical/BM25-style matching or an equivalent measured design). Keep embedding provider choice configurable and version indexes by embedding model and course version.
6. Pin each course's published version and make retrieval filters require tenant, course, course version and any required class/remediation scope.
7. Implement source citations and retrieval traces visible to permitted users; never fabricate a citation when the retrieved source lacks the claimed evidence.
8. Treat retrieved content as untrusted input. It must not override system, teacher or authorization instructions. Defend against prompt injection in document content and URLs.
9. Provide index rebuild, source replacement, unpublish and deletion flows. Handle stale chunks and embeddings deterministically.
10. Evaluate RAG quality across exact-term/formula queries, multilingual questions, irrelevant questions, no-answer cases, conflicting documents, prompt injections and cross-course isolation.

**Tests:** source coverage and citation correctness; no-answer handling; version-pinned retrieval; cross-tenant/cross-course leakage; stale-index invalidation; malformed OCR; indexing retries; poisoned instructions in documents; embedding-version mismatch.

**GREEN gate:** RAG answers are grounded in authorized material when the material exists, uncertainty is explicit when evidence is missing, and no unauthorized document can be retrieved.

### P07 — AI provider gateway, API credentials and model discovery

**Objective:** Create a secure, provider-independent server-side layer for every AI call.

**Work:**
1. Define one internal provider adapter contract for validation, model discovery, capability metadata, chat/generation, streaming, cancellation, usage metadata, timeout, error normalization and health status.
2. Implement adapters for the chosen launch providers: OpenAI, Google Gemini, Anthropic Claude, Grok/xAI, OpenRouter and a configurable custom/OpenAI-compatible endpoint. Provider-specific features must be represented as capabilities, not assumed universal behavior.
3. Support individual API credentials and organization-level credentials. Store only encrypted credential material or managed secret references; never return key material to the frontend after submission.
4. Implement connect/test/revoke/rotate flows. Test keys without exposing them in logs; redact authorization headers, provider request bodies containing secrets and error strings that echo credentials.
5. For custom endpoints, restrict protocols; reject unsafe/private/internal address ranges and redirect behavior; enforce network egress controls where available. Avoid SSRF through user-controlled base URLs.
6. Discover model lists when available. When not available, allow a documented manual model ID and capability declaration verified through a safe test request. Catalog entries must track source, discovery time, provider, context capabilities, modalities, tool/structured-output support where known, lifecycle/status and user access validation.
7. Do not treat catalogue presence as proof that a key can invoke a model. Distinguish `DISCOVERED`, `ACCESS_CHECKED`, `CAPABILITY_CHECKED`, `ELIGIBLE` and `DISABLED` states.
8. Standardize timeouts, retry budgets, rate-limit detection, transient/permanent errors, token/usage metadata and correlation IDs. Avoid blind retries that duplicate paid operations.
9. Add provider mocks for deterministic tests and cost-free ordinary CI.

**Tests:** valid/invalid/revoked key; secret never returned; secret redaction; model list unavailable; inaccessible model; rate limit; timeout; malformed provider response; provider-specific streaming; unsafe custom URL; retry/idempotency; concurrent key updates.

**GREEN gate:** No provider calls bypass the gateway, secrets remain server-side, adapters conform to the shared contract and provider failures are explicit.

### P08 — Tutoring benchmark, model eligibility and routing

**Objective:** Select a model based on task suitability and measured tutoring performance rather than release date alone.

**Work:**
1. Define tutoring task types: grounded explanation, Socratic hint, misconception diagnosis, assessment feedback, numerical reasoning, structured evaluation, multilingual response, teacher copilot and other approved tasks.
2. Create a versioned, curated benchmark with answer/rubric references, curriculum context, language, expected behavior and scoring method. Use authorized/synthetic material during initial development.
3. Define quality dimensions: factual correctness, teaching behavior, source grounding, adherence to teacher/institution instructions, age appropriateness, refusal/safety, multilingual ability, latency and cost information where available.
4. Benchmark only models the user/organization is authorized to use. A failed or unmeasured model must not silently become the production default.
5. Implement a routing policy with hard eligibility filters (user access, provider/org allowlist, privacy, capability, context limit, budget/cost ceiling policy) and a configurable ranking of eligible candidates.
6. Default proposal: quality-first, then use cost/latency ceilings and task requirements as constraints. Owner approval is needed before finalizing cost/latency tradeoffs.
7. Support auto-selection and explicit manual override. Record selection reason without logging unnecessary sensitive prompt content.
8. Support optional session model pinning if approved. If task-aware switching is enabled, disclose meaningful model/provider switches and keep tutoring policy consistent across them.
9. Apply fallback only among eligible providers/models and within the user's and organization's selected policy. Do not send data to another provider after a failure unless policy/consent allows it.
10. Expose model catalog age/staleness, benchmark version and approval status to administrators.

**Tests:** deterministic router rankings; latest-but-unapproved model excluded; provider/tenant/model allowlists; insufficient context; unavailable capability; privacy-restricted fallback; pinned-session behavior; no eligible model; benchmark regression threshold.

**GREEN gate:** Model choice is explainable, deterministic given catalog/policy/evidence, observable and constrained by permissions. No claim of “best” is made without benchmark evidence.

### P09 — Tutor orchestration and adaptive learning engine

**Objective:** Implement the product's core pedagogical turn lifecycle across subjects.

**Work:**
1. Define a typed tutor-turn contract independent of the web framework and individual provider.
2. Implement explicit phases for authentication/enrollment checks, state retrieval, intent/concept resolution, injection guard, teacher instruction resolution, scoped RAG, tool capability selection, context construction, teaching-action selection, model inference, approved tool execution, response validation, answer-leakage assessment, state-delta computation, commit/rollback and event creation. Reuse the 16-step source design where appropriate after code validation, but document any change.
3. Keep course/subject knowledge data-driven. Do not hard-code one chemistry/math curriculum into core routing or progression services.
4. Support configurable tutoring strategies: Socratic, explain-first, practice-first and explicitly defined custom modes. Validate that teacher/org instructions cannot override authorization, privacy or safety rules.
5. Separate candidate model output from authoritative learning state. Evaluate the candidate using deterministic rules and explicit evaluators; stage changes and commit only after required validations pass.
6. Preserve course/version-specific learner state, concept prerequisites, evidence, misconceptions, spaced review schedules, attempted hints and learning events.
7. Add cancellation, timeout, retries, failure recovery, idempotency and rollback rules. A failed AI call must not be recorded as a completed successful teaching step or mutate mastery accidentally.
8. Ensure assessment anti-leakage and student-help policy can vary by task. Never leak answers from a protected exam because the model ignored instructions.
9. Support streaming responses where the chosen frontend/API protocol needs it, while keeping the final result/event consistent with streamed output and cancellation status.

**Tests:** full happy-path turn; every step failure injection; rollback; duplicate request; wrong student/course; expired enrollment; teacher instruction priority; RAG unavailable; unsafe retrieved content; provider switch; model refusal; invalid grading output; no direct mastery mutation; protected-answer leakage; cross-session context contamination.

**GREEN gate:** A turn is auditable from request to validated response and commit decision. No uncaught/silent failure or unvalidated learning-state mutation is accepted.

### P10 — Assessment, evaluation and grading

**Objective:** Support objective and subjective assessment without confusing model feedback with trusted scores.

**Work:**
1. Support MCQs/objective quizzes, numerical and structured responses, descriptive answers, coding tasks, adaptive assessments and timed exams.
2. Model assessment versions, questions/rubrics, deadlines, attempts, submissions, evaluation evidence, scores, feedback, review status and result publication.
3. Keep protected answer keys and grading instructions unavailable to unauthorized users and not embedded in normal student prompts.
4. Implement deterministic scoring for objective question types. For numerical and subjective tasks, use a configured evaluator and rubric, retain evidence/feedback, and apply the required validation or teacher-review policy.
5. Enforce accommodation, attempt-limit, timer, autosave, resume, late submission and exam publication rules where approved.
6. Prevent duplicate submission or score commits. Preserve the difference between provisional AI feedback and finalized marks.
7. Feed assessment evidence into mastery calculations only through the learning engine's defined validation contract.

**Tests:** correct/incorrect/partial scoring; boundary values; time expiry; autosave/reconnect; duplicate submit; answer leakage; unauthorized grading view; rubric version change; AI evaluator failure; manual override/audit; state progression validation.

**GREEN gate:** All assessment types in scope have working creation-to-result journeys; score changes are traceable; protected answers and other students' submissions cannot be accessed.

### P11 — Event capture, archive and training dataset pipeline

**Objective:** Store enough structured history to reconstruct user activity and support future training while keeping training eligibility enforceable.

**Work:**
1. Establish versioned event envelopes with event ID, UTC timestamp, event type/schema version, correlation/trace ID, actor/account context, tenant scope if applicable, session/course references, provenance, outcome and redaction classification.
2. Store critical event/outbox records transactionally with the state they describe. Use a retryable archiver to copy immutable batches/payloads to private S3 prefixes with checksums and manifests.
3. Log full tutoring prompt/response content as requested, but segregate raw interaction content from ordinary operational/security logs. Encrypt it, strictly scope reads, audit access and apply the approved retention rule.
4. Capture model/provider/version, routing reason, tool calls/results, RAG references, tutor lifecycle steps, assessment events, mastery deltas, user feedback, error/fallback and admin changes.
5. Use idempotent consumers and reconciliation reports. Detect missing sequence/event ranges, duplicated writes, failed S3 uploads, corrupt manifests and archive lag.
6. Introduce an eligibility record that is distinct from the event itself: `NOT_REVIEWED`, `ELIGIBLE`, `EXCLUDED`, or `REDACTION_REQUIRED`, with the applicable policy/consent/authorization provenance.
7. Build dataset export as a controlled, reproducible process: filter authorized records → redact/de-identify → validate quality and provenance → create split/version/manifests → record exclusions → require human approval before use in training.
8. Keep raw events immutable except governed correction/tombstone metadata. Do not edit an event silently; represent corrections and deletions with auditable events and execute underlying deletion/retention tasks as required.
9. Provide synthetic event fixtures for tests and local demos.
10. Do not start model training on real user data until the data-use policy, retention and applicable permissions are approved.

**Tests:** outbox atomicity; retry after worker crash; idempotent archive; missing/duplicate detection; checksums; tenant access controls; raw payload redaction in operational logs; consent/policy changes; excluded event not exported; deletion/retention propagation; reproducible dataset manifest; no training command accepts an unapproved dataset.

**GREEN gate:** Critical interaction history is reconstructable, archive failures are visible and recoverable, and the training export enforces eligibility rather than assuming all logged events may be used.

### P12 — Student portal

**Objective:** Deliver the complete learner workflow over the browser API.

**Work:**
1. Build learner onboarding, personal learning space, available/enrolled course list, course overview and approved course-version display.
2. Build tutor chat/streaming UI with explicit model/provider status where useful, source citations, selected tutoring mode, retry/cancel, report issue and helpfulness feedback.
3. Build roadmap/next-action, concepts/mastery, misconceptions, study activity and spaced-review reminders.
4. Implement all assessment journeys supported by P10: attempt, autosave/resume where permitted, submit, feedback, score/result and review.
5. Show which learning space/organization/course is active and avoid accidental mixing of personal and school context.
6. Implement personal provider key connection/manage/revoke views, subject to approved age and org policy. Never expose the stored key after saving.
7. Implement consent/privacy explanations and data access/deletion request status where relevant.
8. Build responsive states for loading, empty results, permission denial, no available model, provider outage, upload processing and network loss. Do not leave dead-end screens or generic spinners without recovery actions.

**Tests:** learner journeys from sign-in through course enrollment, tutoring, assessment and progress update; small/large viewport; API failure states; stale sessions; keyboard use; text overflow in languages; unauthorized course access.

**GREEN gate:** A synthetic learner can complete the core journey end-to-end; every major failure state offers a clear status/recovery action; all state is server-authoritative and persists across sessions/devices.

### P13 — Teacher and academic-administration portal

**Objective:** Provide teacher control over assigned students, content, assessments and interventions.

**Work:**
1. Class roster, student/course enrollment, course source upload and draft/review/publish workflow according to permission.
2. Teacher instruction editor with the source platform's scope cascade (organization → course → class → student → session, or equivalent recorded policy) and deterministic precedence/expiry behavior. Instructions can never override security/privacy gates.
3. Lesson plans, course plans, assignments, rubrics, assessment creation/review and student feedback.
4. Class/student analytics: mastery distribution, progress trends, misconceptions, learning gaps, completed/incomplete activity, intervention queue and authorized session details.
5. Teacher copilot: diagnostic briefings and suggestions must cite data/evidence, state uncertainty, and require teacher confirmation for consequential actions.
6. Alerts/notifications for struggling students, milestones, failed ingestion and intervention status; notification delivery failures must be visible.
7. Teacher communication with students/parents within institution policy.
8. Access only assigned classes/courses unless another authorized role grants a broader scope.

**Tests:** teacher cannot read/edit unrelated classes; instruction priority and expiry; course publish approval; rubric and assessment lifecycle; student intervention acknowledgement; analytics reconciliation; copilot unsupported claim handling; communication authorization; event audit.

**GREEN gate:** Teacher actions affect only the authorized learning scope, instruction precedence is tested, and analytics derive from validated data.

### P14 — Parent/guardian portal

**Objective:** Provide a verified, privacy-filtered view of each linked child's progress and school relationship.

**Work:**
1. Implement guardian request/invite, relationship verification, approval, revocation and handling of multiple guardians/children as permitted by policy.
2. Show authorized progress/mastery, completed work, assessment results/teacher feedback, summarized learning activity/time and recommendations.
3. Provide institution-controlled privacy levels and ensure the parent API returns only data permitted by the applicable policy. Raw transcripts remain unavailable by default unless a later approved policy says otherwise.
4. Include teacher/organization communication and authorized fees/invoices/receipts.
5. Support parent account roles alongside other permitted roles without sharing identities or sessions across unrelated children.
6. Log all access to sensitive child records and every policy override.

**Tests:** parent cannot view unlinked student; revoked guardian relationship is effective immediately; visibility-level matrix; summary-only does not leak raw transcript; financial records restricted correctly; multiple-child switch; audit trail and mobile responsive design.

**GREEN gate:** Parent/guardian journeys work end-to-end and enforce the server-side privacy policy, not just UI hiding.

### P15 — Super-admin and organization-admin portal

**Objective:** Enable safe administration at both platform and organization scope.

**Work:**
1. Organization registration, verification, domain ownership and organization configuration/branding.
2. Manage users, invitations, membership requests, suspensions, role assignments, classes, terms, courses, approvals and organization settings.
3. Provider administration: permitted-provider list, allowed model families/IDs, privacy/capability policies, key ownership/priority and usage/diagnostic dashboards. Do not reveal secret key values.
4. Retention/consent controls, exports, data deletion requests, audit search and access review.
5. Operational dashboards: active users, event/archive lag, course ingestion status, provider errors, model routing stats and cost/usage metadata available from providers.
6. Separate global super-admin functions from organization-admin functions. Platform global actions should be limited to a small privileged role, MFA-protected, reason-coded and audited.
7. Support course/academic admins within the defined organization scope.
8. Implement feature flags/configuration only where they support explicit policy or rollout, not as a substitute for unfinished core functions.

**Tests:** tenant boundary for every admin endpoint; admin role escalation; organization suspension; domain proof; key rotation/revocation; audit immutability/access; global function MFA and reason code; export scope; no secret value display.

**GREEN gate:** A platform admin can operate the platform and an organization admin can operate only their tenant. Every high-impact administrative action is attributable and auditable.

### P16 — Billing, subscriptions, entitlements and institution fees

**Objective:** Support the freemium business model and institution-specific fees without hard-coupling to one payment service.

**Work:**
1. Model plan/package, feature entitlements, subscription status, seat/student count where applicable, usage presentation, invoices, discounts, payment intents, transactions, receipts, reconciliation and refunds/adjustments as required.
2. Separate Gayatri platform subscription charges from third-party AI-provider charges. For BYOK, display the appropriate provider/key owner and do not represent Gayatri as the payer.
3. Include institution fee management and optional individual plans according to the selected business model.
4. Build a payment-gateway adapter and deterministic mock integration. Keep live gateway configuration blocked until provider, pricing, settlement, tax/invoice and refund requirements are approved.
5. Verify webhooks cryptographically using the provider's documented signature scheme; make handlers idempotent; do not trust client redirect/query parameters as proof of payment.
6. Implement payment status reconciliation and visible failure/manual-review states.
7. Keep financial records under approved retention and restricted access; deleting an account must not silently erase records that must legally be retained.

**Tests:** entitlement enforcement; upgrade/downgrade/cancel/renewal; failed and duplicate webhook; invalid signature; duplicate payment event; refund/adjustment; invoice/receipt integrity; tenant boundaries; mock gateway outage; unapproved gateway blocked.

**GREEN gate:** Subscription and fee state is authoritative on the server; duplicate payment signals cannot double-charge/double-credit; gateway-specific behavior remains isolated.

### P17 — Localization, accessibility and offline reading

**Objective:** Complete the selected user experience requirements across eight UI languages and supported device sizes.

**Work:**
1. Establish localization keys and translation catalog workflow; no user-facing strings hard-coded in core components.
2. Support the eight languages specified by the source project, including English/Hindi and the six listed regional languages. Confirm the exact eight from the reference repo; do not invent language names if the source catalog differs.
3. Handle text expansion, font/rendering compatibility, dates/numbers, language switching, fallbacks and incomplete translation detection.
4. Test translated UI labels, errors, forms, assessment display and accessibility names. AI response language selection should remain separate from UI language selection.
5. Implement offline reading for previously downloaded/cached approved lesson/course material. Show timestamp/version and stale status. Offline mode must not pretend that cloud tutor/chat, progress commits or exams have succeeded when they cannot reach the server.
6. Reconnect/sync behavior must be explicit and idempotent. Do not queue high-risk operations such as graded exam submissions or payment actions offline without a defined protocol.
7. Apply keyboard navigation, semantic structure, focus management, sufficient contrast and screen-reader labels.

**Tests:** translation completeness; locale switch; Unicode/regional text; missing key fallback; offline read; stale cache invalidation; reconnect; no false-success for unsynced progress; accessibility automated checks plus manual review of critical paths.

**GREEN gate:** All agreed UI languages are usable for the critical workflows, cached reading is clearly distinguished from live cloud functionality, and localization/accessibility checks pass.

### P18 — Security, privacy, retention and deletion hardening

**Objective:** Apply a cross-cutting security/privacy review to all components before release.

**Work:**
1. Threat-model browser, API, database, S3, custom endpoints, provider keys, RAG documents, model output, event pipeline, training exports, organization admins and privileged operators.
2. Verify authentication, authorization, tenant scoping, CSRF/CORS, request validation, output encoding, injection defense, file safety, rate limiting, secure headers, dependency scanning and secret handling.
3. Verify encryption in transit and at rest; secret key rotation; least-privilege IAM; private S3 access; short-lived access; and database network restrictions.
4. Define and enforce permission checks for provider data transmission. User has accepted sending prompts to a configured provider after connection/disclosure, but organization policy and applicable legal/guardian constraints still apply.
5. Implement privacy/consent ledger, data export, deletion request, soft-delete, permanent deletion/retention exception and verification status. Propagate approved deletions through active tables, S3 objects, search indexes, caches and training candidate stores as the retention policy dictates.
6. Create role/tenant test matrices and test IDOR, privilege escalation, parent access, custom endpoint SSRF, RAG prompt injection, prompt/response log access and training export isolation.
7. Review use of student/minor data and provider terms before any live-data training or public launch. Do not claim regulatory compliance without qualified review.
8. Run dependency and secrets scanners; document residual risks and acceptances.

**Tests:** security regression suite; adversarial tenant tests; authorization on every data access/export path; deletion propagation; key rotation; SSRF cases; malicious uploads; log/telemetry redaction; training eligibility enforcement; dependency/security scans.

**GREEN gate:** No unresolved critical/high severity defect remains without written owner acceptance and mitigation. Privacy/retention/training decisions required for live user data are approved and technically enforced.

### P19 — Observability, reliability and recovery

**Objective:** Make failures diagnosable and recoverable rather than silent.

**Work:**
1. Add structured logs, metrics and traces with request/correlation ID, phase or component, outcome, latency, retryability and sanitized diagnostics. Do not put API keys or unrestricted student text in operational logs.
2. Create operational health/readiness checks for application, database, object storage, background workers, event archive lag and provider gateway.
3. Add alertable metrics for request failures, provider timeouts/rate limits, error rates, archive backlog, indexing failures, failed data deletions, queue lag, database capacity and latency.
4. Define retry/timeouts/circuit-breaking carefully. Use bounded retries with jitter, respect idempotency, and avoid retry storms or duplicate paid calls.
5. Create backup and restore procedures for PostgreSQL and S3 according to versioning/retention decisions. Backups must be encrypted and isolated with least-privilege access.
6. Test restore to a separate environment, migration rollback/recovery and single-EC2 loss. Document remaining downtime risk of the chosen pilot topology.
7. Implement operational runbooks and emergency provider kill switch if approved by the architecture/security review.
8. Make failure recovery outcomes explicit to API clients and UIs, including whether data committed and whether retry is safe.

**Tests:** failure injection for database/S3/provider/worker; queue outage; archive backlog; timeout; restart recovery; duplicate retry; backup restore; alert simulation; sanitized logs; readiness behavior when dependencies are unavailable.

**GREEN gate:** The team can detect critical failures, identify affected requests, restore from backup in a test environment and explain data-commit status after a failure.

### P20 — Integrated verification, end-to-end and load testing

**Objective:** Verify that the full platform behaves as one system at the planned pilot scale.

**Work:**
1. Build end-to-end journey tests across registration → organization membership → course enrollment → upload/index/publish → AI model connection → tutoring → assessment → mastery update → teacher analytics → parent view → billing/export/deletion.
2. Test personal-only account journeys and multi-organization account switching.
3. Run negative journey tests: wrong tenant; unverified member; revoked key; no model available; model timeout; bad RAG retrieval; event archive outage; revoked guardian; expired subscription; rejected payment webhook; deletion request with retention exception.
4. Validate the eight languages and responsive layouts for the main journeys.
5. Load test representative mixed traffic up to the projected 50–250 concurrent users, including login, course retrieval, tutor requests, event writes and background ingestion. Separately measure external model latency; do not conflate provider latency with application capacity.
6. Observe CPU, memory, database connections/IO, S3 request patterns, queue lag, error rates and p95/p99 latency. Record environment size, test scripts, data volume, results and bottlenecks.
7. Verify cost/latency behavior for AI selection using mocks or capped test requests; do not run large paid benchmark sweeps without authorization.
8. Fix failures in their owning phase, rerun focused tests and repeat the integrated suite.

**Tests:** all required unit/integration/E2E suites; cross-tenant negative suites; migration tests; accessibility/localization checks; load and soak tests appropriate to pilot; restore drill; security scan.

**GREEN gate:** All release-critical journeys pass, no unexplained data divergence exists, projected pilot concurrency is supported by actual measurements, and residual risks have an owner and written disposition.

### P21 — Release packaging and deployment readiness

**Objective:** Produce a repeatable, reviewable deployment—not an unverified “works on my machine” launch.

**Work:**
1. Prepare immutable version/build identifiers, locked dependencies, database migration plan and rollback strategy.
2. Prepare deployment configuration via infrastructure-as-code or documented repeatable provisioning, using secret references/managed identity where available. Do not commit credentials or use broad permanent IAM credentials.
3. Verify EC2 network exposure, TLS/HTTPS, domain/DNS plan, reverse proxy, application service manager, health checks, log rotation, database security groups and S3 block-public-access configuration.
4. Provision RDS/S3/EC2 only after the owner approves the architecture, cost estimate and AWS environment. Do not use real student data in staging unless approved and protected.
5. Run migrations, synthetic smoke tests and provider test calls with approved test credentials. Verify error status and emergency disable path.
6. Verify encrypted backups, restore procedure, operations contact, incident response, data retention, user-facing terms/privacy/consent copy and support channels.
7. Run a release checklist, known-issues register, dependency/security report and owner acceptance review.
8. Public release requires an explicit owner release decision. A pilot may be invite-gated and single-instance if the owner accepts the documented availability risk.

**Tests/evidence:** deployment from a clean build; smoke tests; migration forward/rollback proof in staging; TLS/headers; authorization tests against deployed environment; private S3 check; backup restore; monitoring/alert check; all release-gate reports.

**GREEN gate:** Technical release checks pass and the owner has approved unresolved costs, data-use policies, retention, domain, payment setup and the deployment exposure level. Without owner approval, status is `AWAITING_OWNER`, not `GREEN` for public launch.

---

## 6. Definition of GREEN

A phase is GREEN only when every applicable item below is true:

1. The phase plan and any changed assumptions are documented.
2. Each acceptance criterion maps to implementation and/or a test.
3. Code formatting/lint/type checks pass for the changed scope.
4. Targeted unit tests pass.
5. Relevant integration tests pass.
6. Required regression tests pass.
7. Failure paths and negative authorization tests pass where applicable.
8. No secrets, real student data, unnecessary generated files or unrelated edits appear in the diff.
9. Documentation, API contracts, schemas and migrations match the implementation.
10. No failed test is hidden behind `xfail`, skip, weakened assertions or swallowed exceptions without an explicit approved reason.
11. Test evidence is recorded with command, result and relevant environment details.
12. Progress and current-state checkpoint are updated.
13. All acceptance blockers are resolved. External-service tests may remain separately `BLOCKED` only if deterministic mocks cover CI and the phase's scope does not claim the external integration itself was verified.
14. Any required owner decision is recorded. If owner approval is missing, mark `AWAITING_OWNER` even if local code is green.

A passing test suite is necessary, but not sufficient. The agent must also check whether tests actually exercise the intended user and tenant boundaries.

---

## 7. Test and debug protocol

### 7.1 Required test layers

- **Unit:** pure logic such as role compatibility, routing score, course-version resolution, rubric score, mastery calculation and policy decisions.
- **Contract:** provider adapters, public API request/response shapes, error codes and storage interfaces.
- **Integration:** database transactions, migrations, object storage, event outbox, worker idempotency, retrieval filters and auth.
- **Security/negative:** IDOR, cross-tenant reads, role escalation, key leakage, unsafe custom endpoints, prompt injection and deletion/retention bypass.
- **End-to-end:** real user journeys across portals and APIs with synthetic fixtures.
- **Operational:** startup/readiness, service outage, recovery, backup/restore and load/capacity behavior.

### 7.2 When a test fails

1. Save the exact failure output and environment conditions.
2. Determine whether the failure is caused by code, test assumptions, environment, flaky timing or a genuine unresolved requirement.
3. Do not change expected behavior until the requirement owner or decision log supports the change.
4. Write or improve a regression test reproducing a real defect.
5. Implement the smallest fix; rerun the failing test.
6. Run neighboring tests and the phase regression suite.
7. Repeat until green or record a clear blocker with evidence.
8. Never skip a failure merely because it appears unrelated; prove its relation to the active diff or fix it in its owning phase.

### 7.3 External services

Ordinary CI must use deterministic fakes/mocks for paid APIs, mail, payment gateways and AWS operations. Real integration checks must be explicitly enabled, use approved test accounts, have spending caps where available, and record their environment/results separately. Do not use real student records in fixtures.

---

## 8. Progress tracking and resume contract

The companion progress documents will be generated separately. Once present, use the following minimum rules.

### 8.1 One current phase only

At most one phase may be `IN_PROGRESS`, `TESTING` or `DEBUGGING` at a time unless a separately approved work plan explicitly describes parallel work. A phase cannot start until its dependencies are GREEN or a documented dependency exception is approved.

### 8.2 Required phase closeout record

For each phase, record:

- Phase ID and title.
- Current status and date.
- Goal and acceptance criteria.
- Decisions/ADRs referenced.
- Files added/changed/deleted.
- Database migrations and configuration changes.
- Tests run (exact commands), pass/fail counts and result evidence.
- Failures encountered, root causes and fixes.
- Known gaps, risks, skips and blocked external tests.
- Security/privacy review performed.
- Commit/branch identifier when version control is used; do not push or release without permission.
- Next exact action and files to reread.

### 8.3 Context checkpoint format

The short `CURRENT_STATE` checkpoint must answer these in under a page where possible:

1. What is the active phase?
2. Which phases are GREEN?
3. What is the current Git branch/commit and working-tree state?
4. What was the last exact test run and result?
5. What is currently failing or blocked?
6. What decisions are awaiting the owner?
7. What is the next single action?
8. Which files must the next agent read first?

Long implementation details belong in phase logs, architecture or test documents. Do not turn the checkpoint into a transcript of all prior reasoning.

### 8.4 Progress calculation

Do not infer progress from lines of code, files created, prompts completed or time spent. Calculate a phase's progress from its acceptance criteria/subtasks:

- 0%: not started.
- Intermediate percentage: completed, evidenced subtasks divided by total defined subtasks.
- 100%: only after all GREEN-gate checks pass; if owner approval remains, show `AWAITING_OWNER` instead of claiming fully complete.

A phase with failing tests is not GREEN even if most of its code is written.

---

## 9. Scope protection and change management

- If a new requirement appears, add it to the requirements inventory with an ID and owner; assess which phases, data model, security, tests and release scope it affects.
- If an existing requirement must change, record the reason and approval in the decision log before implementing the change.
- When a schema/API change affects a later phase, update the contract and dependent-phase notes before continuing.
- Avoid premature service splitting. Start with well-separated modules and a single deployable application unless load, isolation or operational evidence justifies a separate worker/service.
- Do not add a new database, queue, cache, vector service or orchestration framework without an ADR covering need, cost, failure modes, operational burden and migration path.
- Do not remove features to improve a test metric. A missing feature must remain visibly `MISSING` or `BLOCKED` in traceability until implemented or explicitly descoped by the owner.
- Do not claim legal, privacy, accessibility, curriculum or AI quality compliance without a test/evidence basis and appropriate review.

---

## 10. Final release acceptance checklist

The product cannot be considered release-ready until all applicable requirements below are verified:

### Identity and organizations
- [ ] One global account can use a personal learning space and multiple permitted organization memberships.
- [ ] Invitation, request/approval and verified-domain paths enforce the approved policy.
- [ ] Teacher+parent is supported; student+teacher conflict is enforced; other combinations follow an approved matrix.
- [ ] Organization, course and platform-admin boundaries pass negative tests.
- [ ] Parent/guardian links are verified and revocation is effective.

### Courses and learning
- [ ] Generic course lifecycle works for an arbitrary subject/curriculum.
- [ ] Source uploads, versioning, review, publish, indexing and removal work end-to-end.
- [ ] RAG is course/version/tenant scoped and provides valid citations.
- [ ] Tutoring modes and teacher instruction precedence are deterministic and tested.
- [ ] Learning state only updates after required validation; failures roll back cleanly.
- [ ] Assessment types and result workflows in scope work from authoring to publication.

### AI providers
- [ ] Each supported provider adapter passes contract tests.
- [ ] Personal/institution key ownership and provider priority are explicit.
- [ ] Custom endpoint security and key redaction are verified.
- [ ] Model discovery, access-checking, benchmark eligibility, manual override and fallback are traceable.
- [ ] Provider outage, quota, timeout and no-eligible-model states are understandable to users.

### Data and training
- [ ] Application records persist across sign-in and device changes.
- [ ] Critical events are durable, reconstructable and archived with integrity checks.
- [ ] Operational logs do not expose secrets or unrestricted student conversations.
- [ ] Training export enforces approved data eligibility, provenance, redaction and dataset versioning.
- [ ] Retention and deletion rules are approved and tested across database, S3, indexes and training candidate data.

### Portals and operations
- [ ] Student, teacher, parent, organization-admin, course-admin and super-admin workflows work.
- [ ] Fee management, platform entitlements and payment adapter tests pass.
- [ ] Eight UI languages are verified for critical flows.
- [ ] Cached offline reading is clear and safe; unsynced operations never falsely appear successful.
- [ ] Backup restore and operational failure recovery have been exercised.
- [ ] Pilot load test demonstrates the target concurrent workload or documents an owner-approved capacity limitation.
- [ ] No unresolved critical/high-risk defects remain without explicit written acceptance.
- [ ] Owner approves domain, budget, retention/training policies, payment gateway and release exposure before public launch.

---

## 11. Completion report format

When the full plan is executed—or when the owner requests a status report—the agent must summarize:

1. **Overall status:** phases GREEN, blocked, deferred and awaiting owner.
2. **Implemented capabilities:** only features with implementation and test evidence.
3. **Verification evidence:** test suites, E2E outcomes, security checks, load metrics and restore drill.
4. **Outstanding defects:** severity, affected requirement, reproduction and owner decision if needed.
5. **Outstanding decisions:** the exact choices needed; do not repeat already approved decisions.
6. **Operational state:** local-only, staging or production; AWS resources created; external providers tested; any cost-incurring services activated.
7. **Next recommended action:** one specific, dependency-aware action.

Do not claim the application is finished merely because P21 is coded. It is complete only when all required phases and release gates are GREEN and the owner has explicitly approved release.

---

## 12. Reference links

- Gayatri reference repository: <https://github.com/Gayatri-Education/Gayatri>
- Existing architecture specification: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/ARCHITECTURE.md>
- Existing data model: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/DATA_MODEL.md>
- Existing security model: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/SECURITY_MODEL.md>
- Existing privacy contract: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/PRIVACY_CONTRACT.md>
- Existing deployment guide: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/DEPLOYMENT.md>
- Existing RBAC policy: <https://github.com/Gayatri-Education/Gayatri/blob/main/docs/security/RBAC_POLICY_V4.md>
- Amazon S3 documentation: <https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html>
- Amazon RDS for PostgreSQL extensions: <https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html>

---

**End of master phase plan.** Supporting control and architecture documents are intentionally left for the next step. No code, infrastructure or repository changes are authorized by this document alone.
