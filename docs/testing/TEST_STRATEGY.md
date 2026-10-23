# Test Strategy — Gayatri Cloud

**Status:** Initial test contract. Exact commands are finalized after stack selection in P01. This document does not claim any tests have run or passed.

## 1. Testing principles

- Tests are added with behavior and defects become regression cases.
- Test user-visible behavior plus security and data invariants; don't only test happy paths.
- Unit tests are deterministic and do not require live paid provider/AWS credentials.
- Integration tests may use local disposable infrastructure or mocks; real cloud/provider tests are opt-in and separately authorized.
- Every phase runs targeted tests, then the required regression suite, then diff/security review.
- No silent skipping. Report blocked tests as `BLOCKED`, not `PASS`.
- Keep fixtures anonymized/synthetic; never commit production student records.

## 2. Test layers

### Unit
Pure routing/eligibility logic, policy resolution, role compatibility, curriculum versioning, event schema, state transition rules, input validation, cost/model ranking and normalized provider errors.

### Repository/database integration
Migrations from empty and previous schema, constraints, tenant-scoped queries, transactions, outbox, idempotency, soft deletion, retention selection, indexes and rollback/restore behavior.

### Service/API integration
Authentication/session lifecycle, membership workflows, provider connection, file lifecycle, RAG permission filtering, tutor turn orchestration, assessment grading, transcript access, export/deletion and billing webhook processing.

### Contract
Each AI provider adapter tested against fixtures for catalogue pagination/absence, success/streaming, tool calls, invalid key, rate limit, quota, malformed response, timeout and unknown model. Custom endpoints require SSRF validation tests.

### End-to-end journeys
Independent learner registers → creates/joins course → studies → attempts assessment → sees progress; teacher creates/publishes course → assigns class → monitors authorized learner → intervenes; parent verifies link → sees allowed summary/assessment/fees; admin creates org/policy/memberships; user joins a second organization without leaking personal history; organization isolation across all portals.

### Security/adversarial
IDOR/cross-tenant, privilege escalation, stale sessions, CSRF/XSS as applicable, bad upload, path traversal, malicious PDF/doc/image, prompt injection, poisoned RAG content, unauthorized tool calls, object key guessing, SSRF, secret leakage, log injection, consent/retention bypass and unauthorized training-data inclusion.

### Reliability/performance
Provider outage, retry storms, archive worker unavailable, DB connection loss, duplicate delivery, transaction rollback, S3 timeout, webhook replay, cache isolation and session concurrency. Load-test agreed 50–250 peak concurrency using defined tutor workload and reporting p50/p95 latency/error rates/DB pool/worker backlog/provider errors.

### Accessibility/localization
Keyboard navigation, semantic labels, contrast, responsive layouts, translated keys, language selection persistence, long translated labels and language fallback. Confirm the exact eight languages against the reference/current product requirement during P17.

## 3. Required test cases by high-risk area

### Identity and tenancy
- Every route has expected anonymous/user/role behavior.
- Access decisions use server-side membership and scope.
- User A cannot read/update/export/delete User B data by ID changes.
- Teacher can access assigned students but not unassigned students.
- Parent access stops when relationship is revoked or policy changes.
- Organization admin cannot cross tenant boundary.
- Role compatibility restrictions are tested; unresolved combinations fail closed.

### RAG and course state
- Source/course/version filters always applied.
- Superseded/archived source not returned for current pinned version unless policy explicitly permits.
- Unauthorized documents never appear in prompt/context/citations.
- Retrieval failure is distinguishable from “no relevant source.”
- Ingestion jobs are retryable and do not publish partially built indexes.

### Tutor and learning state
- Teacher instruction precedence, expiry and conflict tests.
- Candidate model answer is validated before commit.
- Failed provider call does not mutate mastery or mark a turn complete.
- Duplicate client request does not double-count assessment or learning evidence.
- Model cannot directly write canonical mastery without domain validation.
- Uncertain/unsupported answer path is tested.

### AI provider routing
- Eligibility filters occur before scoring.
- Automatic selection ignores models without access/approval/required capabilities.
- Manual choice cannot bypass policy.
- Cross-payer fallback is blocked unless authorized and made visible.
- New/unbenchmarked model cannot auto-promote where benchmark gating is required.
- Quota, model retirement and provider outage produce normalized visible statuses.

### Event and training pipeline
- A committed important action has a recoverable event.
- Worker retry/deduplication preserves exactly-once business effect even if delivery is at-least-once.
- Event replay reconstructs per-session sequence.
- Raw content is not exposed through ordinary logs.
- Training eligibility defaults deny when authorization is missing or stale.
- Archived/derived content follows retention and deletion policy.

## 4. Phase GREEN test gate

For an active phase:
1. Formatter/linter/type checker for changed code passes, as selected by stack.
2. Targeted unit tests pass.
3. Relevant integration tests pass.
4. Security/negative tests for new trust boundaries pass.
5. Required regression suite passes.
6. No required test is silently skipped; blocked external checks are explicitly recorded.
7. Acceptance criteria are linked to evidence.
8. Diff contains no secrets or unrelated modifications.

Owner-approval gates remain `AWAITING_OWNER` even if technical tests pass. A test blocked by unavailable credentials may be separated from mock-based tests; it cannot be described as verified against the real provider.

## 5. Defect and debugging workflow

For each failure: capture command/environment, test name, failure summary, expected/actual, root-cause hypothesis, confirming evidence, minimal fix, focused retest, full regression outcome and related defect ID. Preserve failing evidence. Do not keep adding retries or timeouts to hide a deterministic logic defect.

## 6. Test data rules

- Use synthetic users/organizations with at least two tenants in cross-tenant tests.
- Use fake API keys and mocked provider payloads.
- Store no production chats or personally identifiable learner data in fixtures.
- Provider live tests are opt-in and small, with cost ceiling and owner approval.
- Payment tests use sandbox/mocked webhooks until provider and merchant setup are approved.

## 7. Reporting template

Record exact command, tool/runtime versions, exit code, passed/failed/skipped/blocked counts, duration if useful, artifact path, known limitations and commit/hash. Avoid ungrounded words such as “all tests pass” unless the complete required suite was actually executed.
