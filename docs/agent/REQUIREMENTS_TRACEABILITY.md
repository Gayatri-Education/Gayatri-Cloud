# Requirements Traceability Matrix — Gayatri Cloud

**Purpose:** Every important requirement must map to a delivery phase and verifiable test or acceptance evidence. This initial mapping is planned scope, not implementation proof.

## Requirement index

| ID | Requirement | Phase(s) | Verification expected | State |
|---|---|---|---|---|
| RQ-001 | Personal and organization users use the same global account | P02, P03, P04 | Identity/membership integration tests | Verified (`backend/tests/test_auth.py`, `backend/tests/test_organizations.py`) |
| RQ-002 | One account can hold multiple organization memberships with context-specific roles | P02, P04 | Membership, switching and isolation tests | Verified (`backend/tests/test_organizations.py`) |
| RQ-003 | Teacher + parent allowed; student + teacher prohibited | P04, P18 | Role compatibility matrix tests | Verified (`backend/tests/test_organizations.py:test_role_incompatibility_enforcement`) |
| RQ-004 | Invitation, membership request, approval and optional verified-domain flows | P04, P15 | Workflow tests for valid/expired/revoked invitations | Verified for invitation lifecycle (`backend/tests/test_organizations.py:test_invitation_lifecycle_and_acceptance`) |
| RQ-005 | Tenant boundaries on all records, file operations, RAG and analytics | P02, P04, P06, P18, P20 | Cross-tenant negative tests on every interface | Verified at query and API layer (`backend/tests/test_repositories.py`, `backend/tests/test_organizations.py:test_cross_tenant_access_denied`) |
| RQ-006 | Role-aware student/teacher/parent/admin portals | P12–P15 | Portal journey E2E tests | Planned |
| RQ-007 | Course-independent curriculum/course-version model | P02, P05, P06, P09 | Multiple unrelated course fixtures | Verified course & immutable version lifecycle (`backend/tests/test_courses.py:test_course_creation_and_version_lifecycle`) |
| RQ-008 | Upload PDF, scanned PDF, DOCX/PPTX/text, images, web sources, Q&A and lecture/video material | P05, P06 | Ingestion fixture tests; OCR/transcription dependencies isolated | Verified storage upload, MIME sniff validation & traversal guards (`backend/tests/test_courses.py`) |
| RQ-009 | Course-scoped RAG, approved source provenance and version pinning | P06, P09 | Retrieval relevance, authorization and citation tests | Verified hybrid RAG with citations, version-pinning and tenant negative isolation (`backend/tests/test_rag.py`) |
| RQ-010 | Tutor teaching style configurable (Socratic, explain-first, practice-first, custom) | P09, P12, P13 | Method behavior/evaluation tests | Planned |
| RQ-011 | Teacher instruction hierarchy applies correctly | P09, P13 | Precedence/conflict/expiry tests | Planned; hierarchy details must be documented |
| RQ-012 | Learning state changes follow validated deterministic rules | P09, P10 | State invariant and adversarial tests | Planned |
| RQ-013 | Assessment types: MCQ, numerical, subjective, coding, adaptive and timed exams | P10, P12, P13 | Per-type grading and authorization tests | Planned |
| RQ-014 | Server-side provider calls; no provider secrets in browser | P07, P18 | Browser bundle/network inspection and secret scanning | Planned |
| RQ-015 | Connect personal and organization API credentials | P07, P15 | Key ownership/isolation/revocation tests | Planned; precedence open |
| RQ-016 | Native provider adapters and custom OpenAI-compatible endpoint | P07 | Contract tests and provider mocks | Planned |
| RQ-017 | Model discovery handles provider catalogue/access/capability differences | P07 | Adapter contract tests; no assumption all providers support list API | Planned |
| RQ-018 | Automatic and manual model selection | P08 | Routing policy unit/integration tests | Planned |
| RQ-019 | Quality-first tutoring benchmark gates model promotion | P08, P20 | Fixed benchmark and promotion gate | Planned; promotion policy open |
| RQ-020 | Provider failure fallback visible to user, with policy control | P07, P08, P19 | Timeout/quota/invalid key/fallback tests | Planned |
| RQ-021 | Complete chat/session/product events captured reliably | P11, P19 | Replay, deduplication, outage and archive reconciliation tests | Planned |
| RQ-022 | Raw event storage separated from technical operational logs | P11, P18 | Access-control and log-redaction tests | Planned |
| RQ-023 | Event-to-training dataset requires eligibility checks, provenance and quality validation | P11, P18 | Deny-by-default governance tests and dataset lineage checks | Blocked by DEC-011/012 for real data |
| RQ-024 | Canonical learning state, assessment and session changes are recoverable | P02, P09–P11, P19 | Transaction/compensation/failure injection tests | Transaction rollback verified (`backend/tests/test_database.py`) |
| RQ-025 | Parent view uses school policy; no universal raw transcript exposure | P14, P18 | Privacy tier matrix tests | Planned |
| RQ-026 | Teacher transcript access limited to assigned learners and audit logged | P13, P18 | Access-control and audit tests | Planned |
| RQ-027 | Data ownership/export/deletion support with retention-aware workflow | P02, P15, P18 | Export, deletion propagation and retention tests | Planned; periods open |
| RQ-028 | Fee/accounting features and subscriptions | P16 | Invoice, payment, reconciliation and entitlement tests | Planned; payment provider open |
| RQ-029 | Eight UI languages | P17 | Translation key completeness and language journey tests | Planned |
| RQ-030 | Offline reading of previously cached course content | P17 | Network-loss/cache/sync tests | Planned |
| RQ-031 | Observability with redacted diagnostics, correlation IDs and no swallowed failures | P01, P19 | Error contract/log correlation tests | Verified for P01 baseline (`backend/tests/test_health.py`) |
| RQ-032 | Single EC2 pilot deployment and recovery procedures | P21 | Deployment smoke test, restore exercise and runbook review | Planned |
| RQ-033 | 50–250 concurrent-user target validated by load test | P20 | Repeatable load test with service-level measures recorded | Planned; infrastructure sizing provisional |
| RQ-034 | No public deployment or paid resource creation without owner authorization | All | Agent process review and evidence | Verified for P00-P01 (local mocks only) |
| RQ-035 | No silent test weakening; phase GREEN requires evidence | All | Phase log and CI review | Verified for P00-P01 (all tests executed and passing) |
| RQ-036 | Admin config: users, organizations, courses, AI policy, privacy, fees, analytics and branding | P15, P16 | Admin permission and workflow E2E tests | Planned |
| RQ-037 | Emails/password verification, privileged MFA, session/device controls, recovery | P03, P18 | Auth/abuse/recovery tests | Verified for P03 baseline (`backend/tests/test_auth.py`) |
| RQ-038 | Responsive browser UI for desktop and mobile | P12–P17, P20 | Responsive/accessibility checks | Planned |
| RQ-039 | Feature-complete scope cannot be silently reduced | All | Traceability review at each phase and release | Always applicable |

## Traceability rules

1. Every phase acceptance criterion must cite one or more requirement IDs or a logged decision ID.
2. Every security-critical requirement needs positive and negative tests.
3. When requirements change, update this matrix, the decision log, master plan/phase scope if needed, and tests in the same change set.
4. If a requirement is deferred, blocked or rejected, record owner authorization and impacts; do not delete the row.
5. `Planned` means no implementation proof. Update to `Verified` only with links to a test, artifact, commit or phase log containing actual evidence.
