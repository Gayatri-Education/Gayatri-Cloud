# Changelog — Gayatri Cloud/Web

All notable project changes should be recorded here. This file starts as a planning baseline; it must not imply code has been implemented.

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
