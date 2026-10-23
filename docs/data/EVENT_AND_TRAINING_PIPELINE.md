# Event Capture, Archival and Training Data Pipeline

**Status:** Required design baseline. Real learner-data training is blocked until DEC-011 and DEC-012 are approved. Event capture is not training authorization.

## 1. Objectives

- Capture a reconstructable record of tutoring sessions and relevant product/security/business events.
- Keep chat payloads available for approved product analytics and tutor-improvement work, while controlling access.
- Avoid silent event loss during process failure, network outage, retries or archive errors.
- Preserve source and policy provenance from original interaction to dataset and model evaluation.
- Support retention, correction, deletion and training-eligibility changes.

## 2. Event categories

At minimum capture the following event families with versioned schemas:

1. **Identity and membership:** sign-in successes/failures, session creation/revocation, invitation issue/accept/reject/expiry, membership requested/approved/revoked, role grants/changes.
2. **Course/content:** upload, validation, quarantine, parsing, indexing, source removal, version submission/approval/publish/archive, enrollment/unenrollment.
3. **Tutor conversation:** session opened/closed, user turn, assistant turn, task type, context/source manifest, turn validation, cancellation, retry, fallback and state commit/failure.
4. **Learning/assessment:** attempt created/submitted, rubric/evaluator version, hint use, answer evaluation, mastery candidate and authoritative state transition, review scheduling and intervention.
5. **AI execution:** provider/model, credential reference (never secret), selection reason, policy version, prompt/response references in protected storage, usage/latency, outcome and normalized error.
6. **Administration/privacy:** policy changes, provider/key changes, transcript access, exports, deletion requests, consent/eligibility decisions, configuration updates.
7. **Billing:** invoice/payment/refund/webhook/reconciliation state, with no unnecessary payment secret/card data.
8. **Operations:** background job lifecycle, archive reconciliation, service errors and health/latency summaries. Ordinary ops telemetry should not contain full learner content.

## 3. Canonical envelope

Every event should include, where applicable:
- immutable unique event ID;
- event type and schema version;
- UTC event time and server receive time;
- actor/principal ID and actor type;
- organization/membership context or an explicit global/personal scope;
- entity type/ID;
- session, turn, correlation and causation IDs;
- idempotency key for retryable operations;
- sensitivity and retention class;
- payload reference or encrypted/protected payload;
- producer/application version;
- authorization/policy version for sensitive actions;
- archive/processing status maintained separately from immutable event facts.

Use server-controlled time and IDs where appropriate; do not trust clients to set tenant ownership or event ordering. Define how delayed/offline events are represented if cached reading later syncs.

## 4. Reliability pattern

Where the business record lives in PostgreSQL, prefer a transactional outbox: write the authoritative business change and its outbox event in the same database transaction when feasible. A worker processes pending events with bounded retries, idempotent writes and explicit state. Archive batches to private S3 objects with checksums, schema version, counts and time range. Preserve a searchable index/manifest in the application database or an agreed query store.

Required properties:
- duplicate delivery does not create duplicate business effects;
- retry is bounded and observable;
- poison events are quarantined with a diagnostic category and manual recovery path;
- partial S3 write/retry behavior is safe;
- batch manifests and checksums permit reconciliation;
- alert on oldest unprocessed outbox item, error rate and event count mismatch;
- preserve event ordering for a session using sequence numbers rather than assuming global total order;
- support replay to a new derived consumer without rerunning side effects.

Do not place every large prompt/response payload into a transactional row if size/retention makes that inefficient. The payload storage abstraction may store encrypted protected content separately and reference it from the event, while preserving atomicity and reconciliation guarantees. The final design must explain failure cases where payload and event commit separately.

## 5. Separate three planes

### A. Protected interaction/event store
Full tutoring inputs/outputs, course evidence references, session history and educational events. Access is limited, audited and governed by retention/training policy.

### B. Operational logs and metrics
Structured errors, latencies, service status, correlation IDs and redacted diagnostics. No API keys/passwords or unnecessary complete prompts. Use this plane for monitoring, not as the source of training conversations.

### C. Training candidate and approved datasets
Only events with positive eligibility decisions. Includes derived examples, labels, source provenance, transformation/redaction versions, quality review and dataset version manifests. Access should be narrower still and separate from routine application roles.

## 6. Training eligibility policy

Every candidate record must pass a deny-by-default policy check. A decision should reference:
- institution data rights and current authorization;
- relevant user/guardian consent or other approved authorization basis;
- allowed purpose (service delivery, product analytics, general-model training, organization-private model, debugging, etc.);
- policy version and time window;
- retention and deletion status;
- source event and related content references;
- exclusions/redaction result.

Do not infer general-model training permission from API consent, a privacy checkbox unrelated to training, or the fact that a chat is stored. Do not use a tenant's data to train an organization-independent shared model unless the applicable policy explicitly authorizes it. The owner must choose the actual rule before real student data enters a general training corpus.

## 7. Dataset preparation and quality

Candidate processing should:
1. select only eligible records;
2. exclude duplicates, malformed/incomplete turns and disallowed content;
3. minimize/remove direct identifiers and sensitive details where possible;
4. preserve useful course/source context only when authorized and license-compatible;
5. screen for wrong answers, unsafe advice, prompt injection, answer-key leakage and poor pedagogy;
6. add structured labels for subject/task/teaching method/answer quality when defensible;
7. split train/validation/test to avoid session/student/course leakage and near-duplicate contamination;
8. preserve transformation pipeline version and checksums;
9. require human or approved automated quality gates;
10. benchmark any trained candidate before use.

Training may improve pedagogy or format, but RAG remains the mechanism for current/versioned course grounding. Do not treat fine-tuning as a replacement for access control or source retrieval.

## 8. Data deletion and model lineage

Define retention per category before production. A deletion request may affect active records, raw payloads, indexes, caches, exports, event archives and future dataset builds. The policy must specify how already-built datasets are rebuilt/excluded and what guarantees can or cannot be made for an already-trained model. Do not claim machine unlearning or exact removal from model weights unless implemented and evaluated.

Financial/security records may require a distinct lawful retention schedule. Preserve only what is necessary for that purpose and avoid retaining learner content in the exception record.

## 9. Controls and tests

- Event envelope schema and version migration tests.
- Turn/event reconstruction and per-session ordering tests.
- Outbox crash-after-commit, worker retry, duplicate and partial archive tests.
- S3 permissions, encryption and tenant isolation tests.
- Reconciliation detects missing/duplicate events.
- Training eligibility defaults deny; revoke/withdrawal excludes future dataset inclusion.
- Dataset manifest reproducibility and provenance checks.
- Redaction/secret-scan tests.
- Retention and deletion propagation tests once policy is approved.
- Access audit for raw transcript and dataset downloads.

## 10. Blocking governance questions

- Does general training allow institution-authorized records only, individual opt-in data, or both?
- What separate consent/authorization applies to learners who are minors?
- What retention periods apply to raw chats, event logs, audit records, financial records, training candidates and approved datasets?
- Does a deletion/consent withdrawal require a rebuild of dataset versions already generated?
- Are institution-specific private fine-tuned models allowed and who owns resulting artifacts?

Track these in `DECISION_LOG.md` and do not substitute an agent-generated default.
