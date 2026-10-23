# Reference Repository Inventory and Rebuild vs. Reuse Boundary

**Target Platform:** Gayatri Cloud / Gayatri Web  
**Reference Source:** `Gayatri AI - Godess of Knowledge` (`https://github.com/Gayatri-Education/Gayatri`)  
**Document Status:** P00 Discovery Deliverable & Architecture Guide  
**Date:** 24 October 2026  
**License Notice:** Reference repository is under MIT License (DBERT Internship Program, Batch Aug–Oct 2026). Code and algorithmic concepts may be reused under MIT compliance.

---

## 1. Executive Summary

A comprehensive, read-only discovery inspection of the reference repository `Gayatri AI - Godess of Knowledge` was executed from `c:\Users\user\Desktop\gayatri\Gayatri AI - Godess of Knowledge`. 

The reference repository represents an advanced, local-first adaptive tutoring desktop application and sync server built in Python 3.12 with extensive pedagogical, assessment, and knowledge-management engines. It contains a high volume of domain-tested logic in `central_platform/` along with 70+ test suites (`test_phase01`–`test_phase13` and `test_qa_phase01`–`test_qa_phase13`).

The Gayatri Cloud platform is a **fresh cloud-first web implementation**. We strictly follow the architectural boundary:
1. **Reuse Domain Logic & Algorithms:** Port proven pedagogical algorithms, state transitions, validation rules, RAG chunking, and evaluation rubrics after compatibility review.
2. **Rebuild Web & Cloud Layers:** Cleanly implement modern responsive web portals (Next.js / React / TypeScript), cloud multi-tenancy (PostgreSQL + `pgvector`), cloud storage (AWS S3), server-side AI gateway with tenant quotas, and role-based access control.
3. **Discard Desktop-Specific Components:** Discard PySide6/PyQt UI files, local SQLite concurrency locks, and local desktop packaging scripts.

---

## 2. Reference Repository Capability Inventory

| Reference Module | Key Files | Existing Capabilities | Gayatri Cloud Status | Rebuild vs. Reuse Strategy |
|---|---|---|---|---|
| `central_platform/teacher` | `instruction.py`, `copilot.py`, `intervention.py`, `portal.py`, `views.py` | 5-tier instruction cascade (Org $\to$ Course $\to$ Class $\to$ Student $\to$ Session), temporal validity, priority enforcement (1–5), safety validation, teacher copilot briefings | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE & PORT**: Extract core instruction cascade and policy engine into cloud service; build new Web UI for Teacher Portal. |
| `central_platform/slr` | `service.py`, `models.py`, `record.py` | Authoritative Student Learning Record (SLR); canonical student mastery state; spaced repetition tracking; event aggregation; immutability rules | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE & PORT**: Port SLR state calculation algorithms and domain dataclasses; adapt storage backend from SQLite/direct DB to PostgreSQL RDS with async ORM. |
| `central_platform/ai` | `gateway.py`, `adapters.py`, `model_router.py`, `context_builder.py`, `policy_engine.py`, `response_validator.py` | Multi-provider adapters (OpenAI, Gemini, Anthropic, OpenRouter, Local GGUF, Mock), automated failover, context building, model routing, safety sanitization | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE ARCHITECTURE & REBUILD ADAPTERS**: Reuse provider interface contracts and prompt templates; rebuild gateway with cloud-scale tenant BYOK vault, rate limiting, and SSE streaming. |
| `central_platform/rag` | `service.py`, `parsers.py`, `cleaner.py`, `golden.py`, `security.py` | Multi-format parsers (PDF, DOCX, Markdown, Text, HTML, JSON), smart sentence-aware chunking, security sanitizer (anti-injection), cosine vector retrieval | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE CORE ALGORITHMS & REBUILD STORAGE**: Port chunkers, cleaners, and parser logic; replace local FAISS/Chroma storage with PostgreSQL `pgvector` and AWS S3 raw document storage. |
| `central_platform/assessment` | `service.py`, `grading.py`, `rubrics.py`, `sanitizer.py`, `models.py`, `adaptive.py` | Bloom's taxonomy rubric calculation, multi-format question parsing, AI-assisted grading with deterministic fallback, anti-leakage sanitization | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE & PORT**: Port grading rubrics, schema definitions, and validation logic into cloud assessment microservice/module. |
| `central_platform/courses` & `curriculum` | `service.py`, `models.py`, `tree.py` | Course-independent hierarchy, concept graphs, prerequisite mapping, learning objectives | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE & ADAPT**: Reuse concept graph and dependency traversal models; adapt data layer to PostgreSQL relational schema. |
| `central_platform/auth` & `rbac` | `service.py`, `jwt.py`, `password.py`, `roles.py` | JWT token issuance, Argon2/Bcrypt password hashing, role-based authorization | `PARTIAL` | **REBUILD FOR CLOUD**: The reference handles single-org desktop/server sync. Gayatri Cloud requires a global identity model (1 user $\to$ personal account + $N$ organization memberships) with Row-Level Security. |
| `central_platform/db.py` | `db.py` (186 KB) | Monolithic database layer supporting SQLite and basic PostgreSQL | `PARTIAL / MONOLITHIC` | **REBUILD**: Split into modular SQLAlchemy 2.0 / Alembic models with PostgreSQL connection pooling, migration scripts, and tenant isolation predicates. |
| `central_platform/payments` & `fees` | `service.py`, `webhook.py`, `razorpay.py` | Razorpay checkout session creation, HMAC-SHA256 webhook signature verification | `IMPLEMENTED_AND_TESTED` (in reference) | **REUSE LOGIC & EXPAND**: Port Razorpay HMAC verification and webhook idempotent processing; expand for Stripe / multi-currency if needed. |
| `central_platform/ui` & `app/` | `*.py` (PySide6 / PyQt GUI components) | Desktop student tutor interface, window management, desktop audio/video | `NOT_IN_SCOPE FOR WEB` | **DISCARD & REBUILD CLEAN**: Do not port any PyQt/PySide code. Build clean, accessible, responsive React/Next.js web applications. |

---

## 3. Rebuild vs. Reuse Boundary Matrix

```mermaid
flowchart TD
    subgraph REFERENCE_REPO ["Reference Repository: Gayatri-Education/Gayatri"]
        RefPyQt["PySide6 Desktop UI & Local Sync"]
        RefDomain["Domain Logic & Algorithms\n(Teacher Cascade, SLR, Assessment, RAG Chunker)"]
        RefAdapters["AI Providers & Prompt Templates"]
        RefDB["Monolithic SQLite/Postgres db.py"]
    end

    subgraph GAYATRI_CLOUD ["Gayatri Cloud Architecture"]
        WebUI["Modern Web Frontends (Next.js / React / Tailwind)\n(Student, Teacher, Parent, Admin Portals)"]
        CloudCore["Cloud Domain Services (FastAPI / Python)\n- 5-Tier Instruction Cascade\n- SLR & Mastery Engine\n- Bloom Assessment Evaluator\n- Ingestion & RAG Sanitizer"]
        CloudGateway["Cloud AI Gateway\n- BYOK Vault & Multi-Tenant Routing\n- SSE Streaming & Provider Fallback"]
        CloudStorage["Cloud Data Tier\n- RDS PostgreSQL + pgvector\n- S3 Asset & Archive Store"]
    end

    RefPyQt -->|DISCARD| DiscardBox["Discard (Desktop specific)"]
    RefDomain -->|PORT & ADAPT| CloudCore
    RefAdapters -->|REFACTOR & HARDEN| CloudGateway
    RefDB -->|REBUILD WITH ALEMBIC| CloudStorage
    WebUI -->|API Calls (HTTPS / WSS)| CloudCore
```

### Detailed Boundary Decisions:

1. **Frontend / UI Layer:**
   - **Decision:** 100% clean rebuild.
   - **Rationale:** The reference repo desktop UI is tightly bound to Qt event loops and desktop widgets. Gayatri Cloud requires responsive web portals accessible on desktop browsers, tablets, and mobile phones, supporting internationalization (8 languages) and institutional multi-tenancy.

2. **Core Domain Algorithms:**
   - **Decision:** 80% direct port and adaptation, 20% refactoring.
   - **Rationale:** The mathematical models for mastery tracking, spaced repetition intervals, the 5-tier teacher instruction cascade, and assessment sanitization are robust and accompanied by verified regression tests. Extracting them as pure domain modules preserves proven educational behavior while decoupling from desktop dependencies.

3. **Data & Storage Layer:**
   - **Decision:** 100% clean schema rebuild with Alembic migrations.
   - **Rationale:** The reference `db.py` is a 186 KB monolithic file designed originally around SQLite with conditional PostgreSQL branches. Gayatri Cloud requires a first-class, strictly isolated multi-tenant schema with PostgreSQL row-level isolation, `pgvector` indexing, and S3 file/archive management.

4. **AI Gateway & Context Assembly:**
   - **Decision:** 60% port, 40% cloud hardening.
   - **Rationale:** Prompt templates, safety guards, and provider adapter signatures (OpenAI, Gemini, Anthropic, OpenRouter) can be reused. We must add tenant-level API key encryption (AES-GCM / KMS), per-tenant token usage quotas, and streaming response delivery.

---

## 4. Test Suite Inventory and Reuse Strategy

The reference repository includes an extensive suite of test files in `tests/`:
- `test_phase01_auth_identity_remediation.py`
- `test_phase03_postgresql_data_layer.py`
- `test_phase03_rbac_tenant_isolation.py`
- `test_phase04_ai_gateway_remediation.py`
- `test_phase06_authoritative_slr.py`
- `test_phase06_scoped_rag_authorization.py`
- `test_phase07_teacher_instruction_hierarchy.py`
- `test_phase07_tutor_continuity_remediation.py`
- `test_phase08_course_tool_registry.py`
- `test_qa_phase01` through `test_qa_phase13`

### Porting Strategy for Gayatri Cloud Tests:
1. **Preserve Test Vectors:** Extract domain test vectors (e.g. instruction priority overrides, SLR mastery calculation progressions, Bloom taxonomy rubric validations).
2. **Decouple Test Fixtures:** Replace SQLite memory fixtures with PostgreSQL container/test database fixtures and mocked S3 object stores.
3. **Add Cloud-Specific Test Suites:** Add explicit multi-tenant cross-org leakage tests, concurrent token quota exhaustion tests, and browser E2E tests (Playwright).

---

## 5. Traceability to Master Plan Phases

| Master Plan Phase | Target Cloud Capability | Reusable Component from Reference |
|---|---|---|
| **P01–P02** | Foundation, Auth & Tenancy | Auth token specs, Argon2 hashing; global identity model is new. |
| **P03** | Course & Curriculum Engine | `central_platform/courses` & `curriculum` domain structures. |
| **P04** | RAG Pipeline & Ingestion | `central_platform/rag/parsers.py`, `cleaner.py`, `security.py`. |
| **P05** | Student Learning Record (SLR) | `central_platform/slr/service.py` mastery update logic. |
| **P06** | AI Gateway & Provider Routing | `central_platform/ai/adapters.py`, prompt formats, fallback logic. |
| **P07** | Adaptive Tutoring Engine | `central_platform/tutor/orchestrator.py` Socratic guidance rules. |
| **P08** | Teacher Instruction Cascade | `central_platform/teacher/instruction.py` 5-tier resolution. |
| **P09** | Assessment & Evaluation | `central_platform/assessment/rubrics.py` & `grading.py`. |
| **P10–P16** | Web Portals (Student, Teacher, Parent, Admin) | Clean rebuild (React/Next.js); API contracts informed by reference endpoints. |
| **P17** | Events & Interaction Archival | Event schemas from `central_platform/events/`. |
| **P18** | Payments & Fees | Razorpay webhook verification from `central_platform/payments/`. |

---

## 6. Verification and Boundary Invariants

1. **No Direct Import of Legacy UI:** Never import PyQt, PySide, or desktop windowing packages.
2. **Server-Side Only AI Keys:** AI provider keys must never be returned to web frontends.
3. **No Blind Code Migration:** Every reused algorithm must be accompanied by new or ported unit tests that execute cleanly in the Gayatri Cloud test environment.
4. **Zero Code Rule in P00:** This inventory document completes the discovery requirements without modifying any application code.
