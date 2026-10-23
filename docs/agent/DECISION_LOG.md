# Decision Log — Gayatri Cloud

**Rule:** Recommendations are not owner decisions. Every entry has an ID and explicit state. Never erase a superseded decision; link the replacement.

## Status meanings

- `OWNER_CONFIRMED`: directly stated by the product owner.
- `RECOMMENDED_PENDING_APPROVAL`: proposed by the planning process, not yet approved.
- `OPEN`: no final decision.
- `APPROVED`: owner explicitly approved the choice; record date/evidence.
- `SUPERSEDED`: replaced by another decision while preserved for history.

## Confirmed product decisions

| ID | Topic | Confirmed choice | State |
|---|---|---|---|
| DEC-C01 | Customer scope | Both individual users and institutions | `OWNER_CONFIRMED` |
| DEC-C02 | Account model | Personal/standalone accounts and organization-linked accounts; one person may need multiple memberships | `OWNER_CONFIRMED` |
| DEC-C03 | Roles | Student, teacher, parent/guardian, organization admin and platform super-admin in scope; teacher + parent allowed; student + teacher prohibited | `OWNER_CONFIRMED` |
| DEC-C04 | Enrollment | Self-registration plus invitations, approval and organization enrollment | `OWNER_CONFIRMED` |
| DEC-C05 | AI credentials | Both individual personal API keys and institutional provider keys | `OWNER_CONFIRMED` |
| DEC-C06 | AI network boundary | Provider calls server-side; browser must not receive provider secrets | `OWNER_CONFIRMED` |
| DEC-C07 | Model experience | Automatic model selection and advanced manual selector | `OWNER_CONFIRMED` |
| DEC-C08 | Model preferences | Prioritize tutoring quality, latest eligible versions, context handling, multilingual performance and privacy | `OWNER_CONFIRMED` |
| DEC-C09 | Fallback | Combination of fallback and user choice, visible status | `OWNER_CONFIRMED` |
| DEC-C10 | Custom providers | Native adapters plus configurable OpenAI-compatible/custom endpoint support | `OWNER_CONFIRMED` |
| DEC-C11 | Hosting | AWS EC2 and S3; AWS account exists but infrastructure needs provisioning | `OWNER_CONFIRMED` |
| DEC-C12 | Deployment baseline | Prototype/pilot can use a single EC2 instance, with its availability limitations understood | `OWNER_CONFIRMED` |
| DEC-C13 | Cloud persistence | Chat/session history, learning state, assessments, teacher instructions, reports, billing and audit events must persist | `OWNER_CONFIRMED` |
| DEC-C14 | Data ownership | Institution owns its student and course data; processing/exports subject to agreed policy | `OWNER_CONFIRMED` |
| DEC-C15 | Deletion pattern | Soft-delete initially, followed by defined retention and permanent-deletion policy | `OWNER_CONFIRMED` |
| DEC-C16 | Academic scope | Any grade, subject or curriculum is the target capability from day one | `OWNER_CONFIRMED` |
| DEC-C17 | Curriculum workflows | Teachers and admins can create/publish subject to roles/workflows | `OWNER_CONFIRMED` |
| DEC-C18 | Learning pedagogy | Shared framework, teacher-configurable teaching methods | `OWNER_CONFIRMED` |
| DEC-C19 | Mastery | Hybrid model evaluation plus explicit validation; AI does not unilaterally mutate canonical mastery | `OWNER_CONFIRMED` |
| DEC-C20 | Offline | Cached reading/course material and sync when connected; no requirement for fully offline AI inference on web | `OWNER_CONFIRMED` |
| DEC-C21 | Parents | Progress, summaries, assessments, activity/time, finance and communication subject to organization privacy policies | `OWNER_CONFIRMED` |
| DEC-C22 | Teacher access | Teachers may review authorized student transcripts with audit logging | `OWNER_CONFIRMED` |
| DEC-C23 | Assessment | MCQ, numerical, subjective, coding, adaptive practice and timed examinations | `OWNER_CONFIRMED` |
| DEC-C24 | Billing scope | Institution fee features and monetization are in scope; payment provider still open | `OWNER_CONFIRMED` |
| DEC-C25 | Auth baseline | Email/password with verification, privileged MFA, session/device management, age/guardian-aware approval capabilities | `OWNER_CONFIRMED` |
| DEC-C26 | External AI consent | Connected-provider use allowed after required disclosures/consent and organization policy permit it; exact rule must be finalized for minors/institutions | `OWNER_CONFIRMED` |
| DEC-C27 | Logging | Complete prompt/response and application event logging requested for future tutor improvement | `OWNER_CONFIRMED` |
| DEC-C28 | Training governance | Data usage must respect institution ownership, applicable consent and privacy policies; actual eligibility rule remains open | `OWNER_CONFIRMED` (scope), `OPEN` (policy) |
| DEC-C29 | Monetization | Freemium: limited free access, paid individual plans and institutional plans | `OWNER_CONFIRMED` |
| DEC-C30 | Limits/model control | Provider is the primary usage/billing authority; model allowlists and alerts/admin controls required. App-enforced budget behavior unresolved | `OWNER_CONFIRMED` (provider authority), `OPEN` (enforcement) |
| DEC-C31 | Launch size | Expected 100–1,000 registered users and 50–250 peak concurrent users | `OWNER_CONFIRMED` |
| DEC-C32 | Languages | Eight UI languages described in reference project | `OWNER_CONFIRMED` |
| DEC-C33 | Delivery | Responsive website for desktop/mobile; PWA not explicitly required | `OWNER_CONFIRMED` |
| DEC-C34 | Implementation | Fresh web implementation, using current repository as functional reference | `OWNER_CONFIRMED` |
| DEC-C35 | Release ambition | Broad/full feature scope targeted for first release; no phase may silently remove functionality | `OWNER_CONFIRMED` |

## Open decisions

### DEC-001 — Transactional database
- **State:** `APPROVED`
- **Approved Date:** 2026-10-24 (Owner confirmed in gayatri_cloud_agent_goal.md)
- **Approved Choice:** RDS PostgreSQL + pgvector + S3. Local development and testing uses local PostgreSQL (or SQLite/Postgres compatibility adapter); production architecture targets RDS PostgreSQL with pgvector and S3.
- **Why:** memberships, learning state, transactions, audit indexes, filters and concurrent updates require relational integrity; S3 is object storage, not a relational transaction engine.

### DEC-002 — Repository location and project packaging
- **State:** `APPROVED`
- **Approved Date:** 2026-10-24 (Owner confirmed in gayatri_cloud_agent_goal.md)
- **Approved Choice:** Dedicated repository workspace `Gayatri Cloud` pushing to remote `https://github.com/Gayatri-Education/Gayatri-Cloud.git`. Reference repository `Gayatri AI - Godess of Knowledge` remains intact and untouched.

### DEC-003 — Web stack
- **State:** `APPROVED`
- **Approved Date:** 2026-10-24 (Owner confirmed in gayatri_cloud_agent_goal.md)
- **Approved Choice:** Next.js / React + TypeScript frontend, FastAPI / Python 3.12 backend, PostgreSQL + pgvector, Tailwind CSS, pytest, and GitHub Actions CI. Structured ADR recorded in P01.

### DEC-004 — Organization joining defaults
- **State:** `RECOMMENDED_PENDING_APPROVAL`
- **Recommendation:** configurable invitations, membership requests and verified-domain flows. A verified matching domain may grant a limited pending/basic membership only if the organization enables that path; it never grants privileged roles by itself. Teacher/admin privileges require explicit authorization.
- **Open details:** which flows are enabled by default; whether domain auto-join creates an active member or an approval request.

### DEC-005 — Cross-role compatibility
- **State:** `OPEN`
- **Confirmed constraints:** teacher + parent allowed; student + teacher prohibited globally per owner clarification.
- **Open combinations:** student + parent; organization admin + teacher; course admin + teacher; parent + teacher in different organizations; future guest/guardian states.
- **Recommendation:** centrally enforce known rules and store policy for remaining combinations; block conflicting combinations by default until approved.

### DEC-006 — Domain and identity verification details
- **State:** `OPEN`
- **Recommendation:** domain ownership verification via DNS or another documented control; email domain matching is insufficient by itself. Invite tokens must expire and be single-use. Parent-child links require a separate verification workflow.

### DEC-007 — Authentication integrations
- **State:** `OPEN`
- **Confirmed baseline:** email/password, verified email, MFA for privileged accounts, session/device controls, account recovery and age/guardian-aware approval.
- **Not confirmed:** Google/Microsoft sign-in, institutional SAML/OIDC SSO, phone OTP/passwordless.

### DEC-008 — Provider key precedence and students' BYOK
- **State:** `OPEN`
- **Recommendation:** organization/provider policy determines which providers are permitted; user chooses among eligible personal/org keys where policy allows; UI always labels the payer/key owner. Student/minor BYOK is disabled by default until owner defines age/guardian and organization policy.

### DEC-009 — Model selection trade-offs and pinning
- **State:** `RECOMMENDED_PENDING_APPROVAL`
- **Recommendation:** quality-first, task-aware routing; hard filters for access, privacy, required capability and institution allowlist; configurable cost/latency ceiling; optional session pinning. New model must pass benchmark/approval before becoming default-eligible.
- **Open:** Is cost/latency a hard ceiling? Should users be allowed to pin one model per session? Who approves model promotions?

### DEC-010 — Application-level usage budgets
- **State:** `OPEN`
- **Confirmed:** provider quota is primary billing authority; admins can restrict model choices and receive usage/failure alerts.
- **Open:** whether Gayatri may block/throttle by user/org/token/cost. Do not represent application budgets as enforced until decided and tested.

### DEC-011 — General-model training eligibility
- **State:** `APPROVED`
- **Approved Date:** 2026-10-24 (Owner confirmed in gayatri_cloud_agent_goal.md)
- **Approved Policy:** Deny-by-default. Full events and interactions are captured and archived in secure, restricted storage for auditing/system improvement, but real student records are prohibited from being used in general-model training without explicit institutional authorization + student/guardian opt-in + automated PII scrubbing. Synthetic and curated datasets are permitted for testing and evaluation.

### DEC-012 — Retention, deletion and training lineage
- **State:** `OPEN` and blocking for production real data until periods are defined
- **Required categories:** raw chats, app/audit logs, financial records, uploaded source documents, training candidates, approved datasets, embeddings/indexes, exports/backups.
- **Recommendation:** category-specific retention and deletion periods. Define how deletion/correction requests are reflected in future dataset builds and model retraining limits.

### DEC-013 — Organization administrator transcript visibility
- **State:** `OPEN`
- **Confirmed:** authorized teachers may review transcripts for assigned students with audit logging; parents see policy-filtered information and not full transcripts by default.
- **Open:** whether org-admins may access raw transcripts and under what reasons/approval/audit conditions.

### DEC-014 — Payment gateway, launch mode and operational target
- **State:** `OPEN`
- **Recommendation:** keep payment gateway behind an adapter; no live payment use until merchant, fees, refund, settlement and reconciliation policy is approved. Treat a feature-complete pilot separately from public production launch. Single EC2 is a pilot arrangement, not high availability.

### DEC-015 — Budget, deadline, domain and AWS monthly ceiling
- **State:** `OPEN`
- **Required owner input:** target date, developer capacity, one-time build budget, monthly AWS spend ceiling, domain/brand and DNS access. Never invent these values.

### DEC-016 — File/data input types not explicitly confirmed
- **State:** `OPEN`
- **Confirmed:** PDF/scanned PDFs, DOCX/PPTX/text, images, web sources, manually authored Q&A and video/lecture material.
- **Open:** CSV/XLSX structured data ingestion. Don't make it a release blocker unless approved.

### DEC-017 — Additional feature interpretation
- **State:** `OPEN`
- **Not explicitly confirmed:** public guest course access, PWA, parent visibility into raw transcripts, direct teacher-parent messaging details, Google/Microsoft login, notification channels (email/SMS/push), advanced SSO, external web search/retrieval at tutoring time.

## Decision entry template

### DEC-XXX — Short title
- **State:** `OPEN` / `RECOMMENDED_PENDING_APPROVAL` / `APPROVED` / `SUPERSEDED`
- **Raised:** YYYY-MM-DD
- **Owner decision/evidence:** exact user approval or no decision yet
- **Options:** ...
- **Recommendation and rationale:** ...
- **Security/data/cost impact:** ...
- **Affected phases/docs/tests:** ...
- **Supersedes / superseded by:** ...
