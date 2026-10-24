# Changelog — Gayatri Cloud/Web

All notable project changes should be recorded here. This file starts as a planning baseline; it must not imply code has been implemented.

## [P13] — Teacher and Academic-Administration Portal — 2026-10-24

### Added
- Backend Models & Schema in `backend/app/db/models/teacher.py`:
  - `TeacherIntervention`: Flags struggling learners with severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), diagnosed root causes, teacher acknowledgement timestamps, and resolution notes.
  - `ClassAnnouncement`: Posts course announcements and notices to class offerings.
- Teacher Domain Service in `backend/app/domain/teacher/service.py`:
  - `TeacherService`: Class rosters with mastery calculations and active misconception counts; enrollment/unenrollment lifecycle; 5-tier instruction cascade management (`ORG`, `COURSE`, `CLASS`, `STUDENT`, `SESSION`) with priority sorting; class analytics aggregating mastery distributions across 5 buckets (Novice, Developing, Competent, Proficient, Master), hardest concepts ranking, and misconception clusters; intervention queue with teacher acknowledgement tracking; and evidence-grounded AI copilot briefings with uncertainty notes and teacher confirmation gates.
- REST API Endpoints in `backend/app/api/v1/teacher.py`:
  - 12 endpoints covering rosters, student enrollment/unenrollment, class analytics, intervention queue and acknowledgement, copilot briefings, 5-tier instruction directives, and announcements with strict tenant isolation.
- Frontend Teacher Types & API Client:
  - `frontend/src/lib/types/teacher.ts`: TypeScript contracts for `RosterStudent`, `ClassAnalytics`, `InterventionItem`, `CopilotBriefing`, `TeacherInstructionItem`, `ClassAnnouncementItem`.
  - `frontend/src/lib/api-client.ts`: 12 typed methods for teacher capabilities.
- Frontend Reusable Components in `frontend/src/components/teacher/`:
  - `RosterTable.tsx`: Searchable class roster, student enrollment/unenrollment actions, mastery progress bars, active misconception badges.
  - `InstructionEditor.tsx`: 5-tier cascade directive editor with priority slider (1-5), active directives listing, and deactivation.
  - `AnalyticsCharts.tsx`: Mastery distribution breakdown, hardest concepts ranked by difficulty, and cohort misconception clusters.
  - `InterventionQueue.tsx`: Severity-coded queue with acknowledge and resolve workflows.
  - `TeacherCopilotCard.tsx`: Data-grounded AI copilot briefing card with confidence score, uncertainty note, and one-click recommended action triggers.
- Next.js 14 App Router Pages:
  - `/teacher/dashboard`: Primary teacher workspace with offering selector, copilot briefing card, and intervention queue preview.
  - `/teacher/roster`: Full roster view and enrollment management.
  - `/teacher/instructions`: 5-tier directive cascade manager.
  - `/teacher/analytics`: Cohort learning analytics and misconception clusters.
  - `/teacher/assessments`: Assessment oversight, audit log, and manual score overrides.
  - `Navbar.tsx`: Integrated role-aware shortcut to Teacher Portal for teachers and academic administrators.
- Automated Test Suite:
  - `backend/tests/test_teacher.py`: 7 tests passing covering roster lifecycle, cross-tenant isolation, analytics calculation, intervention acknowledgement, copilot briefing grounding, instruction cascade, and announcements.
  - `frontend/tests/teacher-portal.test.ts`: 9 vitest tests passing covering client contracts, tenant headers, 403 boundary rejection, instruction tiers, analytics processing, intervention workflow, and copilot grounding.
  - All 82 backend pytest tests and 23 frontend vitest tests passing; Next.js production build compiling 15/15 routes cleanly.

## [P12] — Student Portal (Next.js Web UI) — 2026-10-24

### Added
- Frontend Type Architecture in `frontend/src/lib/types/`:
  - `auth.ts`, `course.ts`, `tutoring.ts`, `assessment.ts`, `mastery.ts`, `ai.ts`: Complete TypeScript interface models mapped to backend schemas.
- Core Services & Context:
  - `api-client.ts`: Typed REST client with automatic Bearer token injection, active `X-Organization-Id` tenant isolation header, retry handling, and friendly network failure diagnostics.
  - `stream-client.ts`: Server-Sent Events (SSE) streaming client parsing tokens, citations, and mode changes with `AbortController` cancellation.
  - `AuthContext.tsx`: Manages user authentication, session persistence, and organization context switching (strictly separating personal learning space from school memberships).
- Reusable UI Components in `frontend/src/components/`:
  - `Navbar.tsx`: Global navigation header with active organization context switcher, role badge, and profile logout.
  - `ErrorState.tsx`: Actionable error boundary with explicit recovery triggers (`Try Again`, `Return to Dashboard`, `Manage AI Keys`).
  - `EmptyState.tsx`: Structured empty states with call-to-actions.
  - `LoadingSkeleton.tsx`: Clean animated pulse loaders.
  - `CourseCard.tsx`: Course card with approved version tag (`v1.0`), subject pill, and mastery progress bar.
  - `TutorChat.tsx`: Interactive AI tutor interface supporting real-time streaming, pedagogy mode switching (Socratic/Explain/Practice), source citation pills, helpfulness ratings, and streaming abort/cancel.
  - `AssessmentRunner.tsx`: Full assessment test taker supporting all 6 question types (MCQ, Boolean, Numerical with units and tolerance, Subjective, Coding, Adaptive) with timer countdown, autosave indicator, and idempotent submission confirmation.
  - `AssessmentResultView.tsx`: Comprehensive results display with percentage scores, rubric criteria breakdown, detected misconception alerts, and automated mastery updates.
  - `MasteryRoadmap.tsx`: Visual concept mastery hierarchy with progress bars, stability metrics, active misconception remediation advice, and spaced review schedules.
  - `KeyManager.tsx`: BYOK AI provider connection manager with server-side AES-256-GCM encryption, strictly masked keys (`sk-...4f9b`), and zero client secret exposure.
- Next.js 14 App Router Pages:
  - `/dashboard`: Learner dashboard with enrolled courses, streak tracker, and upcoming assessments.
  - `/courses` & `/courses/[id]`: Course catalog and detailed syllabus with pinned version display.
  - `/tutoring` & `/tutoring/[sessionId]`: Live Socratic tutor chat session.
  - `/assessments` & `/assessments/[id]`: Assessment list and live attempt runner.
  - `/mastery`: Concept knowledge graph and misconception remediation center.
  - `/settings/ai-keys`: BYOK key manager and DEC-011 training consent governance.
- Verification & Test Suite in `frontend/tests/student-portal.test.ts`:
  - 11 unit and component tests verifying token injection, tenant isolation, SSE chunk parsing, client cancellation, assessment scoring, masked BYOK credentials, and mastery calculations.
  - 14/14 total vitest tests passing; Next.js production build compiling 10/10 routes.

## [P11] — Event Capture, Archive and Training Dataset Pipeline — 2026-10-24

### Added
- Canonical Event Schema & Envelope in `backend/app/domain/events/envelope.py`:
  - `EventEnvelopeBuilder`: formats events with event UUID, UTC timestamp, schema version, actor context, tenant scope, session/course references, sensitivity classification (`PUBLIC`, `INTERNAL`, `PROTECTED`, `RESTRICTED`), and JSON payload.
  - Covers all 8 event categories: `IDENTITY`, `COURSE`, `TUTOR`, `LEARNING`, `AI_EXECUTION`, `ADMIN_PRIVACY`, `BILLING`, `OPERATIONS`.
- Transactional Outbox Engine in `backend/app/domain/events/outbox.py`:
  - `OutboxService`: atomic event persistence with business transactions, status transitions (`pending`, `archived`, `failed`, `quarantined`), bounded exponential retry handling, and automatic poison-event isolation at `max_retries=3`.
- Immutable Archive Batching Service in `backend/app/domain/events/archiver.py`:
  - `ArchiveService`: aggregates pending outbox events into immutable archive batches, computes SHA-256 cryptographic checksums, uploads manifests and payloads to object storage (`archives/events/...`), updates outbox statuses to `archived`, and supports idempotent retry.
- Operational Telemetry Plane in `backend/app/domain/events/telemetry.py`:
  - `OperationalTelemetry`: enforces strict plane separation; redacts student conversational prompts, answers, and sensitive payload attributes while recording structured diagnostic logs and correlation IDs.
- Deny-by-Default Training Governance & Export Pipeline in `backend/app/domain/events/training.py`:
  - `TrainingPipelineService`: enforces DEC-011 training policy, initializing all events as `NOT_REVIEWED` and requiring explicit learner consent + institution authorization before promotion to `ELIGIBLE`.
  - `PIIRedactor`: scrubs email addresses, phone numbers, and IPv4 addresses from training data.
  - Controlled dataset exporter: reproducible train/validation/test splits (80/10/10) with course- and learner-level contamination prevention.
  - Strict human approval gating: training engine blocks dataset access unless explicitly authorized by an administrator (`is_approved=True`).
- Event Management REST API in `backend/app/api/v1/events.py`:
  - `POST /api/v1/events/outbox/process`: Trigger transactional batch archival.
  - `GET /api/v1/events/outbox/status`: Retrieve queue metrics, pending count, and quarantine statistics.
  - `GET /api/v1/events/archive/batches`: Query archived storage manifests.
  - `POST /api/v1/events/training/eligibility`: Evaluate or update training eligibility for an event.
  - `POST /api/v1/events/training/export`: Export an eligible training dataset version.
  - `POST /api/v1/events/training/datasets/{dataset_id}/approve`: Human approval sign-off gate.
  - `GET /api/v1/events/training/datasets`: List dataset exports and approval status.
- Verification & Test Suite in `backend/tests/test_events.py`:
  - 7 targeted tests covering canonical envelope creation, transactional outbox & retries, archiver batching & checksums, telemetry redaction, deny-by-default training governance, split reproducibility, and approval gates.
  - Regression suite passes with 75/75 tests in 17.23s.

## [P10] — Assessment, Evaluation and Grading — 2026-10-24

### Added
- Anti-Answer-Leakage Sanitizer in `backend/app/domain/assessment/sanitizer.py`:
  - `AssessmentSanitizer`: strips answer keys, correct option indices, rubrics, solutions, and internal teacher notes from student examination payloads.
  - Recursive `verify_no_leakage` auditing ensuring zero unearned answer exposure.
- Deterministic Evaluation Engine in `backend/app/domain/assessment/deterministic.py`:
  - `DeterministicGrader`:
    - `grade_mcq`: exact matching, letter wrapper patterns (`(b)`, `Option C`, `[d]`), numeric option indices.
    - `grade_boolean`: normalized boolean truth value evaluation (`true`, `yes`, `1`, `0`, `false`).
    - `grade_numerical`: extracts magnitude excluding unit exponents (`^2`, `m2`), evaluates relative tolerance (±2%), verifies required units, rejects NaN/Infinity injection.
- Multi-Criterion Rubric Engine in `backend/app/domain/assessment/rubrics.py`:
  - `RubricEngine`: multi-criterion scoring, level descriptors, Bloom's taxonomy calculation, and standard rubric presets.
- Domain Evaluators in `backend/app/domain/assessment/evaluators.py`:
  - `SubjectiveEvaluator`: evaluates open responses against rubrics, detects misconception patterns (e.g. `MISCON_HEAT_WORK`), and outputs calibrated confidence scores.
  - `CodingEvaluator`: verifies Python syntax AST and evaluates execution against structured test cases in a sandbox.
  - `AdaptiveEngine`: dynamic difficulty progression (advancing on success, scaffolding on failure).
- Assessment Coordination Service in `backend/app/domain/assessment/service.py`:
  - Assessment authoring & publishing by authorized staff.
  - Sanitized retrieval for enrolled students.
  - Attempt initiation with timer limits, draft autosave/resume, and deadline verification.
  - Idempotent submission preventing duplicate score commits.
  - Automated canonical mastery progression via `CanonicalMasteryService.record_evidence` logging `LearningEvent` audit trails.
  - Teacher manual score override and comment adjustment.
- Assessment REST API in `backend/app/api/v1/assessments.py`:
  - `POST /api/v1/assessments`
  - `GET /api/v1/assessments/{assessment_id}`
  - `POST /api/v1/assessments/{assessment_id}/publish`
  - `POST /api/v1/assessments/{assessment_id}/attempts`
  - `GET /api/v1/assessments/attempts/{attempt_id}`
  - `PUT /api/v1/assessments/attempts/{attempt_id}/autosave`
  - `POST /api/v1/assessments/attempts/{attempt_id}/submit`
  - `POST /api/v1/assessments/attempts/{attempt_id}/override`
  - Strict tenant boundary isolation preventing cross-organization attempt inspection.
- Comprehensive test suite in `backend/tests/test_assessments.py` verifying all 6 assessment types, anti-leakage protection, timed exam autosave/resume, idempotency, canonical mastery progression, teacher manual override, and cross-tenant isolation.

### Verification
- Phase: `P10` — status: `GREEN`
- Acceptance criteria: 10/10 passed.
- Tests: `Push-Location backend; python -m pytest; Pop-Location` (68 passed in 11.69s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 69 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P09] — Tutor Orchestration and Adaptive Learning Engine — 2026-10-24

### Added
- Teacher Instruction Cascade Engine in `backend/app/domain/tutoring/pedagogy.py`:
  - 5-tier instruction hierarchy: `SESSION (5) > STUDENT (4) > CLASS (3) > COURSE (2) > ORG (1)`.
  - Deterministic precedence sorting by tier rank, priority, and creation time.
  - Active expiry filtering (`expires_at <= now()`).
- Configurable Pedagogical Modes in `backend/app/domain/tutoring/pedagogy.py`:
  - `socratic`: guided questions, active scaffolding, prohibited from blurting direct answers.
  - `explain_first`: direct conceptual clarity with analogies, followed by a check question.
  - `practice_first`: scenario/problem-driven coaching.
  - `custom`: teacher directive driven.
  - Untrusted curriculum RAG context injection enclosed strictly in `<document_chunk>` XML tags to guard against prompt injection.
- Deterministic Mastery State Machine in `backend/app/domain/tutoring/mastery.py`:
  - Prohibits LLMs from unilaterally altering student mastery states.
  - Updates `CanonicalLearningState` via validated evidence events: increases mastery via stability formula `min(1.0, current + 0.20 * stability)`, decreases mastery on errors (`-0.15`).
  - Append-only `LearningEvent` audit trail logging.
  - Misconception diagnosis in `MisconceptionRecord` with automatic remediation tracking upon reaching threshold mastery >= 0.70.
- Tutor Orchestrator Service in `backend/app/domain/tutoring/service.py`:
  - Verifies student course enrollment before session initiation.
  - Orchestrates multi-turn dialogue, integrates hybrid course-scoped RAG chunks, applies teacher instructions, calls `AIGateway` with model routing, and persists monotonic `ConversationTurn` history.
- Tutoring REST API in `backend/app/api/v1/tutoring.py`:
  - `POST /api/v1/tutoring/sessions`
  - `GET /api/v1/tutoring/sessions/{id}`
  - `POST /api/v1/tutoring/sessions/{id}/turns`
  - `GET /api/v1/tutoring/sessions/{id}/mastery`
  - `POST /api/v1/tutoring/instructions`
  - `GET /api/v1/tutoring/instructions`
- Comprehensive test suite in `backend/tests/test_tutoring.py` verifying multi-turn dialogue, teacher instruction cascade precedence/expiry, pedagogy modes, deterministic mastery updates, misconception logging, and tenant/student isolation.

### Verification
- Phase: `P09` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `Push-Location backend; python -m pytest; Pop-Location` (60 passed in 11.70s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 60 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P08] — Tutoring Benchmark, Model Eligibility and Routing — 2026-10-24

### Added
- Standardized Tutoring Benchmark Suite `v1.0.0` in `backend/app/domain/benchmarks/benchmark_suite.py`:
  - Curated pedagogical test cases evaluating Socratic scaffolding, conceptual explanation, misconception diagnosis, step-by-step mathematical reasoning, and safety/jailbreak resistance.
  - Rubric expected keywords and forbidden answer-blurting penalties.
- Benchmark Evaluator and Eligibility Gating in `backend/app/domain/benchmarks/evaluator.py`:
  - `BenchmarkEvaluator` computing pedagogical, factual accuracy, safety, and composite scores (0.0 to 100.0).
  - Eligibility threshold gating: enforces minimum composite score >= 75.0 and safety score >= 80.0 before a model is marked eligible for tutoring tasks.
  - Immutable database record persistence in `ModelBenchmarkRun`.
- Quality-First Intelligent Router in `backend/app/domain/ai/router.py`:
  - `IntelligentModelRouter` selecting the highest-scoring benchmarked eligible model matching task requirements.
  - Context window limit verification.
  - Manual model override processing with compatibility checking.
  - Transparent routing justification metadata.
- Version 1 Benchmark & Routing API in `backend/app/api/v1/benchmarks.py`:
  - `POST /api/v1/benchmarks/run`
  - `GET /api/v1/benchmarks/runs`
  - `POST /api/v1/benchmarks/route`
- Comprehensive test suite in `backend/tests/test_benchmarks.py` verifying benchmark suite structure, automated evaluator scoring, eligibility gating, quality-first model selection, and context-limited manual overrides.

### Verification
- Phase: `P08` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (57 passed in 9.35s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 55 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P07] — AI Provider Gateway, API Credentials and Model Discovery — 2026-10-24

### Added
- Authenticated AES-256-GCM Credential Vault in `backend/app/core/security.py`:
  - Symmetric key derivation from application secret key.
  - Random 12-byte nonces for ciphertext non-determinism.
  - Decryption with integrity/tamper detection.
  - Safe key masking (`mask_credential`) and SHA-256 key fingerprinting (`compute_key_fingerprint`) ensuring plaintext keys are never returned or logged.
- Multi-Provider Adapters in `backend/app/domain/ai/adapters.py`:
  - `AIProviderAdapter` ABC with `list_models`, `generate`, and `stream_generate`.
  - Deterministic `MockAIProviderAdapter` for offline zero-cost testing and rate-limit simulation.
  - Native adapters: `OpenAIProviderAdapter`, `AnthropicProviderAdapter`, `GeminiProviderAdapter`, `OpenRouterAdapter`, and `CustomEndpointAdapter` for OpenAI-compatible self-hosted servers.
- Resilient Server-Side AI Gateway in `backend/app/domain/ai/gateway.py`:
  - `AIGateway` managing provider credential resolution (personal BYOK vs institution keys).
  - Policy-driven automated fallback: if primary provider encounters quota/rate-limit exceptions, gateway transparently executes against configured fallback model with audit metadata.
  - Execution audit logging in `AIExecutionUsage`.
  - Asynchronous token stream generator.
- Credential & Model Catalog Domain Services in `backend/app/domain/ai/service.py`:
  - Encrypted registration, retrieval, and deactivation of `ProviderConnection` entities.
  - Model discovery synchronization updating `ProviderModelSnapshot` table.
- Version 1 AI Gateway API in `backend/app/api/v1/ai.py`:
  - `POST /api/v1/ai/connections`
  - `GET /api/v1/ai/connections`
  - `DELETE /api/v1/ai/connections/{connection_id}`
  - `GET /api/v1/ai/models`
  - `POST /api/v1/ai/models/sync`
  - `POST /api/v1/ai/generate`
  - `POST /api/v1/ai/generate/stream` (SSE)
- Comprehensive test suite in `backend/tests/test_ai.py` verifying AES-256-GCM encryption, tamper rejection, zero secret exposure, provider adapter contracts, automatic rate-limit fallback, SSE streaming, and tenant credential isolation.

### Verification
- Phase: `P07` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (53 passed in 10.71s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 50 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P06] — Content Ingestion, Indexing and Course-Scoped RAG — 2026-10-24

### Added
- Architectural Decision Record in `docs/architecture/ADR-002-OCR-AND-RAG-STRATEGY.md` establishing hybrid retrieval (lexical BM25 + dense semantic embeddings), OCR confidence routing, and prompt injection defense boundaries.
- Prompt-Injection Defense and Sanitizer in `backend/app/domain/ingestion/sanitizer.py`:
  - `sanitize_document_text` neutralizing LLM control tokens (`<|im_start|>`, `<|endoftext|>`, `[INST]`) and instruction override patterns.
  - `wrap_chunk_for_prompt` encapsulating retrieved text in XML-escaped `<document_chunk>` boundaries with page and section metadata.
- Multi-Format Extractors in `backend/app/domain/ingestion/extractors.py`:
  - `PDFExtractor` extracting page-by-page text streams using `pypdf`.
  - `TextAndMarkdownExtractor` preserving section and markdown header hierarchy.
  - `VTTTranscriptExtractor` parsing timestamped captions and cues into coherent spoken paragraphs.
  - `PluggableOCRExtractor` interface with confidence scoring.
- Chunking Engine in `backend/app/domain/ingestion/chunker.py`:
  - `ContentChunker` with sliding window, natural sentence/paragraph boundary detection, and token estimations.
- Hybrid Retrieval & Citation Engine in `backend/app/domain/rag/retrieval.py`:
  - `MockEmbeddingAdapter` providing deterministic 64-dimensional normalized vectors for fast offline local testing without external API calls.
  - `LexicalMatcher` providing BM25 scoring across chunks.
  - `CourseRAGEngine` executing hybrid scoring ($\alpha \cdot \text{Score}_{\text{sem}} + (1 - \alpha) \cdot \text{Score}_{\text{lex}}$) with mandatory hard filtering on `course_version_id` and `organization_id`.
  - Structured citation generation with source filename, chunk ID, page number, and section provenance.
- Ingestion Domain Service in `backend/app/domain/ingestion/service.py`:
  - Processes uploaded `ContentSource` records into indexed `ContentChunk` records, updating ingestion lifecycle status.
- Version 1 RAG API in `backend/app/api/v1/rag.py`:
  - `POST /api/v1/rag/courses/{course_id}/versions/{version_id}/ingest`
  - `POST /api/v1/rag/courses/{course_id}/versions/{version_id}/query`
- Comprehensive test suite in `backend/tests/test_rag.py` verifying sanitization, multi-format extraction, chunking, deterministic embeddings, BM25 matching, end-to-end ingestion/querying, and cross-tenant retrieval isolation.

### Verification
- Phase: `P06` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (44 passed in 8.21s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 45 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P05] — File Storage Abstraction and Course Lifecycle — 2026-10-24

### Added
- Storage Abstraction Layer in `backend/app/core/storage.py`:
  - `StorageService` abstract base class with local filesystem (`LocalStorageAdapter`) and AWS S3 (`S3StorageAdapter`) implementations.
  - Strict path traversal guards preventing directory escape attacks (`_resolve_safe_path`).
  - Deep MIME type sniffing and magic byte verification protecting against MIME spoofing for PDFs, images, Office documents, and text files.
  - File size bounds enforcement (50MB maximum).
  - Sanitization of user-provided filenames to prevent filesystem corruption.
- Course and Curriculum Lifecycle Service in `backend/app/domain/course.py`:
  - Course creation supporting organization scoping and platform-wide global courses.
  - Snapshot versioning (`CourseVersion`) starting at `v1.0.0` draft.
  - Immutability enforcement: published course versions reject adding, editing, or deleting curriculum sources.
  - Course offering cohort deployment strictly gated on published course versions.
  - Active student enrollment verification requiring valid organization membership and `STUDENT` role.
  - Authorized presigned download URL generator with cross-tenant access denial.
- Version 1 Course Management API in `backend/app/api/v1/courses.py`:
  - `POST /api/v1/courses`
  - `GET /api/v1/courses`
  - `GET /api/v1/courses/{course_id}`
  - `POST /api/v1/courses/{course_id}/versions`
  - `GET /api/v1/courses/{course_id}/versions`
  - `POST /api/v1/courses/{course_id}/versions/{version_id}/publish`
  - `POST /api/v1/courses/{course_id}/versions/{version_id}/sources`
  - `GET /api/v1/courses/{course_id}/versions/{version_id}/sources`
  - `GET /api/v1/courses/{course_id}/versions/{version_id}/sources/{source_id}/download`
  - `POST /api/v1/courses/offerings`
  - `POST /api/v1/courses/offerings/{offering_id}/enroll`
- Full test suite in `backend/tests/test_courses.py` verifying storage adapters, traversal guards, MIME spoofing checks, version immutability, offering rules, and IDOR isolation.

### Verification
- Phase: `P05` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (36 passed in 7.78s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 38 files).
- Frontend: `npm run lint` and `npm run test` (3/3 passing).
- Zero secrets committed.

## [P04] — Organizations, Memberships, Roles and Tenant Isolation — 2026-10-24

### Added
- Multi-Tenant Role-Based Access Control (RBAC) and context dependencies in `backend/app/core/rbac.py`:
  - `TenantContext` data structure tracking resolved user, organization ID, and organization-scoped roles.
  - `resolve_tenant_context` dependency extracting `X-Organization-ID` header, verifying active membership, assigning roles, with Super Admin bypass.
  - `require_roles` dependency factory enforcing granular role permissions.
- Organization Domain Service in `backend/app/domain/organization.py`:
  - Organization provisioning with slug generation and automatic creator `ORG_ADMIN` assignment.
  - Cryptographic invitation workflow with expiry tracking and single-use redemption.
  - Invariant enforcement: strictly prohibits `STUDENT` and `TEACHER` roles on the same account within an organization (DEC-C03), while permitting `TEACHER` + `PARENT`.
  - Guardian-to-student verification and relationship linkage.
- Version 1 Organization Endpoints in `backend/app/api/v1/organizations.py`:
  - `POST /api/v1/organizations`
  - `GET /api/v1/organizations/me`
  - `POST /api/v1/organizations/{organization_id}/invitations`
  - `POST /api/v1/organizations/invitations/accept`
  - `GET /api/v1/organizations/{organization_id}/members`
  - `POST /api/v1/organizations/{organization_id}/guardians`
- Comprehensive integration test suite in `backend/tests/test_organizations.py`:
  - Organization creation and admin role verification.
  - Cross-tenant access isolation (IDOR protection).
  - Invitation creation, expiration, and redemption.
  - Strict role incompatibility enforcement (`STUDENT` vs `TEACHER`).
  - Parent/guardian access boundary validation.

### Verification
- Phase: `P04` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (28 passed in 8.25s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 34 files).
- Zero secrets committed.

## [P03] — Authentication and Account Lifecycle — 2026-10-24

### Added
- Cryptographic security engine in `backend/app/core/security.py`:
  - PBKDF2-HMAC-SHA256 password hashing with random 32-byte salt and constant-time verification.
  - JWT token generation, signature validation, and expiration enforcement for access and refresh tokens.
  - SHA-256 token hashing for secure persistence of session devices in database.
- Authentication Domain Service in `backend/app/domain/auth.py`:
  - User registration with normalized email and password strength validation.
  - Constant-time authentication with user enumeration resistance.
  - Session device creation, refresh token rotation, and replay attack prevention.
  - Session revocation and logout.
  - `get_current_user` FastAPI dependency verifying Bearer token and active account status.
- Version 1 Authentication API in `backend/app/api/v1/auth.py`:
  - `POST /api/v1/auth/register`
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
- Full test suite in `backend/tests/test_auth.py` verifying registration, duplicate prevention, enumeration resistance, token rotation, and revoked session rejection.

### Verification
- Phase: `P03` — status: `GREEN`
- Acceptance criteria: 8/8 passed.
- Tests: `python -m pytest backend/tests -v` (23 passed in 3.48s).
- Linter: `ruff check` and `ruff format --check` (100% clean across 30 files).
- Zero secrets committed.

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
