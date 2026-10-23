# Logical Data Model — Gayatri Cloud

**Status:** Logical proposal, not a final physical schema. Do not create irreversible migrations until DEC-001 database choice and data policies are settled.

## 1. Modeling rules

- Treat personal identity separately from organization membership and role assignment.
- Every organization-owned row must have an explicit tenant/organization scope or an explicitly documented global scope.
- Never infer permission only from a user-supplied ID or email domain.
- Store identifiers for relationships; avoid copying sensitive student content into analytics tables.
- Keep raw transcript payloads separate from event metadata and technical logs.
- Version curriculum/course content and retrieval indexes; learning records must identify the course version used where relevant.
- Make deletion/retention status and dataset eligibility explicit. A soft delete is a lifecycle state, not permission to keep data forever.
- Keep payment/financial records distinct from general chat/session data.

## 2. Core identity and organization entities

### `UserAccount`
Global person identity: `user_id`, normalized verified email/contact references, display/profile data, age/guardian status where lawfully needed, account status, created/updated timestamps and deletion state. Password hashes or federated identity references are stored using an approved authentication design; never store plaintext passwords.

### `AuthIdentity` / `Credential`
Login method identifier, provider subject, verification state, recovery metadata and lifecycle. Secrets are hashed/encrypted according to credential type; provider API keys are not ordinary identity credentials and must have their own encrypted credential vault/references.

### `Organization`
Organization ID, legal/display name, status, policy version, settings, branding, verified domains, ownership contacts and retention/data-processing configuration.

### `OrganizationDomain`
Domain, verification challenge/status, verification date, approved join method, allowed email patterns if needed and audit reference. Domain verification does not automatically grant a privileged role.

### `Membership`
Membership ID, user ID, organization ID, status (`invited`, `requested`, `pending`, `active`, `suspended`, `rejected`, `left` or equivalent approved enum), source (invitation, request, domain flow, admin), created/approved/revoked actors and timestamps. Enforce idempotency and prevent duplicate active memberships where inappropriate.

### `RoleAssignment`
Principal (user or membership), role, scope, permissions/policy version, grantor, grant time, expiry/revocation and audit event. Platform `SUPER_ADMIN` is global and must be separately protected; organization-admin scope is limited to one organization.

### `Invitation` / `MembershipRequest`
Single-use hashed token or token reference, target email/user where applicable, organization, proposed role (must not self-grant privileged roles), issuer, expiry, status, approval/rejection actor and audit trail.

### `GuardianRelationship`
Guardian user, learner user, verification method/state, authority scope, school policy, validity dates, consent references and revocation history. Access depends on current relationship and visibility policy, not merely the existence of a historical link.

### `SessionDevice` / `RefreshSession`
Session/device identifier, user, creation/last-seen/expiry/revocation, client metadata minimized as appropriate, security event references and refresh-token hash/rotation state if used.

## 3. Academic and course entities

- `Course`: generic subject/curriculum-independent course metadata; global or organization-owned visibility, creator and status.
- `CourseVersion`: immutable published snapshot/version of objectives, concept graph, source set and learning settings; lifecycle draft → review → approved/published → archived (exact state names finalized with implementation).
- `CourseOffering`: course version delivered in a term/class/cohort with organization and status.
- `ClassGroup` / `Cohort`: organization-owned grouping, grade/section/term metadata and assigned staff.
- `CourseEnrollment`: learner, offering, enrollment status, enrollment source and dates. Authorization depends on active enrollment and context.
- `TeachingAssignment`: teacher membership/user, course offering/class scope and dates.
- `TeacherInstruction`: scope tier, target ID, content/policy fields, start/end, author, version and audit metadata. Exact priority order must be verified and documented; do not invent precedence.
- `ContentSource`: uploaded object/web source/Q&A/video transcript with owner, URI/key, content hash, MIME/format, scanning status, processing state, source rights/terms, source version and retention/eligibility metadata.
- `ContentChunk`: chunk/source/course/course-version scope, offsets, text or protected payload reference, metadata and embedding/index reference.
- `CourseIndexVersion`: embedding model/version, extraction pipeline version, source manifest hash, build status and published pin.
- `CourseToolPolicy`: tools/evaluators permitted for a course/offering/role and constraints.

Course source visibility must be enforced on both database and retrieval indexes. A cross-tenant source must not enter context merely because semantic similarity is high.

## 4. Tutor, sessions and learning entities

- `TutorSession`: user, course/offering, organization context, session status, timestamps, privacy context and session-level model preference where approved.
- `ConversationTurn`: sequence, speaker, content reference, relevant policy/version references, provider/model execution metadata, token/latency metadata, validation status and event correlation ID. Raw content access follows transcript policy.
- `TutorExecution`: task type, provider/model attempt(s), routing reason, capability checks, timeout/retry/fallback, source manifest and sanitized diagnostics.
- `Assessment`: course/offering, type, version, duration, rubric, publication window and eligibility rules.
- `AssessmentAttempt`: learner, assessment version, start/submit state, idempotency key and timing/anti-cheat metadata appropriate to policy.
- `AssessmentResponse`: question/item, response reference, evaluator/rubric version, score, evidence, feedback and review state.
- `LearningEvent`: append-oriented learning evidence such as attempt, hint, explanation, misconception signal, success/failure, review outcome or validated mastery evidence.
- `CanonicalLearningState`: learner + course/version/concept scope, mastery evidence/level, stability/review schedule and state version. It must only change through validated, transactional rules.
- `MisconceptionRecord` / `Intervention`: evidence/source, confidence, teacher review state, owner and remediation history.
- `Notification` / `Message`: sender/recipient/scope, type/content reference, delivery state and read/retention metadata; communications must respect organization policies.

## 5. Provider, billing and policy entities

- `ProviderConnection`: owner scope (user or organization), provider type, credential secret reference, display name, connection status, allowed scopes and timestamps. Secret bytes are held in an appropriate encrypted store, not returned by API.
- `ProviderModelSnapshot`: provider/model ID, display/version/lifecycle metadata, observed capabilities, context/tool support, availability time, source and expiration. Catalogue data is a cache and not proof of runtime access.
- `ModelPolicy`: allowed providers/models, task capabilities, benchmark eligibility, privacy constraints, cost/latency ceiling and policy version.
- `ModelBenchmarkRun`: dataset/evaluator version, model/provider version, results, confidence/limits, approver and eligibility decision.
- `AIExecutionUsage`: token/usage estimates or provider-reported usage, payer/key owner, organization/user/session relation, model, latency, status and cost source where available.
- `SubscriptionPlan` / `Entitlement`: feature, seat or capacity allocation, plan version, validity and enforcement state.
- `FeeInvoice` / `PaymentTransaction` / `Refund` / `ReconciliationRecord`: financial status, provider IDs, idempotency, verified webhook/audit facts, amounts/currency/timestamps and immutable reconciliation history.

## 6. Events and training provenance entities

- `ApplicationEvent`: event ID, event type/version, time, actor, organization context if applicable, entity reference, correlation/causation ID, idempotency key, sensitivity classification, retention class and payload reference.
- `EventOutbox`: event payload/reference, created/attempt count, next retry, archive state and last sanitized error. If business state uses relational transactions, the outbox record should commit in the same transaction where applicable.
- `EventArchiveBatch`: S3 object key, schema version, event count, time range, checksums and reconciliation state.
- `TrainingEligibilityDecision`: source event/record references, institution/user/guardian authorization evidence, policy version, allowed use, reason and decision timestamp.
- `TrainingDatasetVersion`: immutable manifest, included source IDs or immutable approved references, transformations, redaction version, quality labels, provenance, checksum, owner/approver and use constraints.
- `ModelEvaluationRun` / `ModelReleaseApproval`: benchmark version, candidate artifact/model, results, failure analysis, approval and rollback reference.

A dataset should be reproducible from an immutable manifest without putting raw personal data into the manifest itself. If a deletion or consent withdrawal affects the dataset, apply the approved data-governance policy and preserve a privacy-conscious audit record of the action.

## 7. Tenant and access patterns

- Store explicit organization scope for organization-owned rows.
- Check ownership/membership in service authorization before database fetch, not only after data is loaded.
- Apply tenant scope within repositories/query builders and, where selected, PostgreSQL row-level security as defense in depth.
- Use separate object prefixes/buckets or equivalent tenant-aware object keys and policies; random object IDs are not authorization.
- Apply course/offering/student scoping to vector/keyword retrieval and analytics queries.
- Test IDOR patterns, alternate identifiers, guessed object keys, export paths and background jobs.

## 8. Indexes and transactions to design

Likely index patterns include account email/identity lookup, membership by user/org/status, enrollment by learner/offering/status, course source/version state, session by user/course/time, event by ID/time/tenant/type/correlation, and payment provider/idempotency reference. Final indexes must be based on queries and explain plans.

Transactional boundaries to preserve include: account + membership creation where coupled; session turn + durable event/outbox; assessment submission + state transition; payment webhook idempotency + ledger/reconciliation; course publication + source/index version pin; and revocation/deletion status update plus queued downstream purge tasks.

## 9. Migration policy

- Number migrations, describe forward and down/repair strategy, and record checksums.
- Test from an empty database and from the latest supported schema.
- Prefer expand/migrate/contract for risky production changes.
- Never drop or rewrite data without backup, impact analysis, rollback plan and required owner approval.
- Verify row counts, constraints and tenant invariants after migration.
- Keep fixtures and migrations aligned; do not let tests pass using an obsolete schema.
