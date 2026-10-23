# System Architecture — Gayatri Cloud/Web

**Status:** Proposed baseline, not yet approved for paid infrastructure provisioning. See `docs/agent/DECISION_LOG.md` (DEC-001 through DEC-015).  
**Scope:** Responsive web platform, server-side AI, institutional/individual identity, adaptive learning, RAG, event capture and training-data preparation.

## 1. Architecture goals

- Support independent users and multiple organizations on one platform.
- Use one global identity per person and separate membership-scoped authorization.
- Keep educational data, provider credentials and organization boundaries explicit.
- Keep the tutoring engine independent of any one LLM vendor, course or UI framework.
- Make learning state authoritative, auditable and transactionally safe.
- Capture complete relevant application/tutoring events for traceability and approved model-improvement workflows.
- Run locally during development, then provision an AWS pilot only after owner authorization.
- Make external dependencies replaceable and testable using contract tests and deterministic mocks.

## 2. Proposed logical components

1. **Web client** — responsive student, teacher, parent/guardian, organization admin and super-admin portals. It holds user session tokens as appropriate but never provider API keys.
2. **Identity and membership service** — authentication, account recovery, invitation acceptance, verified-domain flows, membership status, role assignment, guardian links and session/device management.
3. **Application API** — versioned API boundary, request validation, authorization context, rate controls, idempotency and standardized errors.
4. **Organization/course service** — organizations, academic hierarchy, course offerings, immutable/published course versions, enrollments and instruction scope.
5. **File service** — safe upload, metadata validation, checksum, quarantine, private object storage, retention and signed download/upload workflow.
6. **Ingestion/RAG service** — document parsing, text extraction/OCR where required, chunking, embedding, keyword index, course/version scopes, source citation and index rebuild.
7. **AI gateway** — credential references, provider adapters, model catalogue, capability discovery, routing policy, fallback, usage observation and manual overrides.
8. **Tutor orchestrator** — interaction lifecycle, pedagogy selection, retrieval assembly, instruction cascade, tool execution, response validation and safe recovery.
9. **Learning/assessment service** — validated attempts, rubric evaluation, mastery transitions, spaced review, progression and assessment integrity.
10. **Event service** — durable event append/outbox, correlation IDs, event schema validation, idempotent archival and replay support.
11. **Training data pipeline** — eligibility policy, filtering/de-identification, quality review, data provenance, dataset versioning and model benchmark gates. This pipeline must not train automatically on all captured conversations.
12. **Billing/entitlement service** — freemium entitlements, plan assignment, invoices and provider payment adapter when approved.
13. **Operational services** — health/readiness, metrics, tracing, redacted logs, alerting, backup/restore and incident runbooks.

## 3. Proposed deployment baseline

- **EC2:** web/API application and background worker(s) initially. One instance is acceptable for a limited pilot but is a single point of failure.
- **RDS PostgreSQL:** recommended transactional store for users, memberships, course metadata, learning state, assessments, session/event metadata and billing. Requires owner approval (DEC-001).
- **S3:** private object storage for course files, generated reports, event archives, dataset artifacts and backup/export objects.
- **RAG vector search:** evaluate PostgreSQL `pgvector` first. Add a distinct managed search/vector service only when measured scale, relevance or operational needs justify it.
- **Secrets:** use an appropriate server-side secret-management service or encrypted secret store; do not place secrets in frontend configuration, code or ordinary logs.
- **Network:** restrict database/object-store permissions to service identities; database should not be publicly reachable unless an explicitly reviewed exception exists.
- **Local development:** use local PostgreSQL or a compatible test database plus a local filesystem/S3-compatible adapter or test double. Avoid paid cloud dependencies in unit tests.

No resource sizes, AWS region, availability mode, monthly cost or final engine/version has been approved yet. Record these in an ADR before provisioning.

## 4. Main data flows

### 4.1 Sign-in and organization context

Browser → identity/auth endpoint → account/session → membership list → user selects context → API authorizes each request using the account, active membership, role and tenant scope. Never trust a client-supplied `tenant_id` as authorization proof.

### 4.2 Course ingestion

Authorized user uploads file → validate type/size/content and permission → store source privately → extract content/metadata → scan/quarantine unsafe or failed uploads → create draft course version → chunk/embed/index under organization/course/version namespace → validate retrieval → review/approve/publish → enrollment grants access.

### 4.3 Tutoring request

Validate identity and enrollment → load canonical learner/course state → resolve teaching method and instruction precedence → retrieve authorized, version-pinned evidence → build bounded context → select eligible model → execute provider call → validate pedagogy/source grounding/safety → persist conversation and event → calculate state changes using validated evidence → atomically commit results → return response and provenance metadata.

The final ordering must avoid a response being shown as successfully committed if the corresponding session/mastery update failed. Use transaction/outbox/compensation design and idempotency keys where relevant.

### 4.4 Events and training data

Transactional app operation writes its business update and durable event/outbox record together where possible → event worker archives in idempotent batches to S3 → reconciliation detects gaps → eligibility service checks authorization/consent/policy → preparation filters and de-identifies → quality review and provenance → versioned dataset → benchmark and approval before model change.

## 5. Trust boundaries

- Untrusted browser to API.
- User uploads to parsing/OCR/transcription tools.
- Tenant A to Tenant B boundaries in database, object storage, RAG, analytics and events.
- Application to third-party AI providers.
- Raw student records to training candidate datasets.
- Student/parent/teacher/admin roles and privilege boundaries.
- Development/test data to production data.

Every boundary must have explicit authentication/authorization, validation, minimal data transfer, logging appropriate to sensitivity and negative tests.

## 6. Cross-cutting architecture requirements

- API versioning and schema validation.
- Idempotency for retries of session turns, upload jobs, event archive and payments.
- Correlation IDs end to end.
- No silent exception swallowing.
- Retry policy with exponential backoff and bounded attempts for transient failures; no retries for invalid credentials or policy denial.
- Data migrations must be reversible where practical and safe to restore from backup.
- Provider adapter contract tests and fixture-based regression tests.
- All external calls have timeouts and controlled error messages.
- Secrets and PII are excluded or redacted in ordinary operational logs.
- Backups, restore drills, retention/deletion and training-lineage effects are defined before production.

## 7. Architectural decisions still open

See DEC-001 through DEC-017. In particular: database approval, project repository layout, web stack, role compatibility, organization join defaults, auth integrations, provider-key priority, model ranking/pinning, app-level usage enforcement, training eligibility, retention durations, org-admin transcript access, payment provider, launch readiness, budget/domain and CSV/XLSX ingestion.

## 8. Architecture change procedure

A change affecting tenant boundaries, record ownership, provider routing, learning-state authority, training eligibility, payment processing or deployment costs requires:
1. a decision-log/ADR entry with options and trade-offs;
2. impact analysis against requirements and tests;
3. owner approval if it changes a confirmed requirement or causes cost/security/data implications;
4. updates to this document, data model, traceability and phase plan as applicable;
5. migration and rollback plan where data shape changes.
