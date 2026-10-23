# Security and Privacy Baseline — Gayatri Cloud

**Status:** Requirements baseline; must be expanded and verified during P03/P04/P18/P20. This is not a compliance certification or legal advice.

## 1. Security objectives

- Prevent cross-organization access and privilege escalation.
- Protect children/learners, conversation content, credentials and institutional material.
- Prevent leaked provider keys and unsafe custom-endpoint requests.
- Ensure tutoring/learning state cannot be corrupted by prompt injection, retries or partial failures.
- Make privileged actions and sensitive access auditable.
- Support data export, deletion, retention, consent and training eligibility with clear ownership.

## 2. Authentication and account lifecycle

Confirmed baseline includes email/password with verification, multi-factor authentication for privileged users, session/device management, account recovery and age/guardian-aware approval capabilities. Password hashes must use a current strong password hashing algorithm and safe parameters. Tokens require bounded lifetimes, secure cookie/token choices, rotation/revocation and protection from CSRF/XSS/session theft according to the chosen frontend architecture.

Do not add Google/Microsoft OAuth, SAML/OIDC SSO or phone OTP as assumed requirements; record them as open until approved. Rate-limit sign-in, verification, recovery, invitation redemption and membership requests. Error messages should not enable user/account enumeration.

## 3. Roles and scopes

- `SUPER_ADMIN`: platform-wide capability, highly privileged, MFA mandatory, shortest practical privileged session, audited actions and break-glass policy.
- `ORG_ADMIN`: one organization only, can manage authorized organization users/policy/courses/fees but cannot access other organizations.
- `COURSE_ADMIN` / academic coordinator: scope defined by explicit assignment/policy; role still requires owner confirmation for launch scope.
- `TEACHER`: assigned courses/classes/students only; course management and transcript review limited by permissions.
- `STUDENT`: own learning/session/assessment records and explicitly assigned courses.
- `PARENT/GUARDIAN`: explicitly verified linked learner(s), access filtered by organization policy and relationship validity.
- `GUEST`: optional scope remains open; never assign privileged permissions by default.

Known role rule: teacher + parent is permitted; student + teacher is prohibited globally per owner clarification. Other role combinations remain open. Until approved, enforce known restrictions and avoid granting ambiguous combinations. Roles are not a hierarchy where every higher role automatically inherits all lower capabilities; permissions must be explicit.

## 4. Tenant isolation

Every API handler, repository method, background job, export, object-storage action, search and RAG operation must use trusted authorization context. Client-supplied organization IDs are selectors, not proof. Verify active membership, role, assigned course/offering/student and record ownership for each operation.

Required negative tests:
- User changes `org_id`, `user_id`, `student_id`, `course_id`, `session_id`, object key or query filter.
- Teacher fetches unassigned students or courses.
- Parent guesses another child's ID or uses a revoked relationship.
- Organization admin reads/writes a different tenant.
- Search/RAG returns a document from another tenant/course version.
- Background worker processes a job after membership, source or consent has been revoked.
- Cached response leaks across users/tenants because cache key omits principal/scope.

Object-store access should be private by default. Pre-signed URLs must be short-lived, scoped to one object/action and issued only after authorization. Avoid putting sensitive names or course content in object keys.

## 5. API-key and provider security

- Provider calls are server-side only.
- Store API keys in encrypted secret storage; relational rows contain a reference and limited metadata, not readable secret values.
- Never return raw keys after connection setup; display a masked label and permit rotate/revoke.
- Validate key syntax and connection; protect validation endpoints with rate limits.
- Prevent SSRF in custom endpoint configuration: allow HTTPS by default; block loopback, link-local, private/internal address ranges and cloud metadata endpoints unless a separately reviewed safe network policy allows them. Revalidate redirects and resolved addresses to mitigate DNS rebinding. Apply egress controls and short timeouts.
- Do not follow arbitrary provider-supplied URLs for tools without allowlists and safe URL handling.
- Prevent secrets in exceptions, request dumps, telemetry and browser error messages.
- Use explicit provider/key owner and payer metadata for usage transparency.

## 6. AI input/output safety

Treat uploaded content and retrieved text as untrusted data. Delimit retrieved sources from instructions; never let source text override system policy or tenant authorization. Validate tool calls against typed schemas and an allowlist. Tools that execute code or access external systems require sandboxing and resource limits.

Use course-version-scoped retrieval. Require source attribution when the answer uses RAG evidence. Keep the model from directly mutating canonical mastery or payment/access state. Validate candidate output before state commit. Have safe behavior for insufficient source evidence, provider refusal, malformed output, timeout, unsafe tool request and assessment answer leakage.

Prompt-injection detection may help, but it is not the only security boundary. Authorization must be enforced structurally outside the model.

## 7. Data classes and logging

Suggested sensitivity classes:
- **Public:** approved public marketing/course catalogue.
- **Internal:** non-sensitive operational metadata.
- **Confidential:** organization records, course drafts, assessment keys, invoices.
- **Restricted learner data:** student profile, chat/transcript, answers, learning state, guardian links and training candidates.
- **Secret:** API keys, passwords, signing/encryption keys, payment secrets.

Raw conversations must be access-controlled and encrypted. Technical logs should be structured and redacted; never log API keys/passwords or full payment credentials. If complete chats are retained for training, store them in the protected conversation/event plane, not indiscriminately in general application logs. Audit each transcript read, export, deletion, consent change, key access/revocation and privileged policy change.

## 8. Privacy, consent and external AI

Before sending learner data to a third-party model, enforce the applicable provider allowlist, organization data policy, user/guardian consent and required disclosure. Minimize prompt context to information needed for the task; avoid sending unrelated identifiers or other students' data. Record provider, model, policy version, data categories transferred and timestamp in the transmission audit without duplicating unnecessary sensitive content.

Actual legal obligations vary by users, location, school arrangement and data type. Owner should obtain appropriate privacy/legal review for minors, educational records, cross-border provider processing, payments, cookies and retention before public launch.

## 9. Data subject and institution workflows

Support export, correction/deletion requests, soft-delete, approval exceptions and permanent deletion under a documented policy. Separate raw conversation, audit, financial and training dataset schedules. Financial/audit retention exceptions must be documented. Propagate deletion/eligibility changes to source objects, indexes, caches, event archives and future training dataset builds as required by policy. Do not promise removal from an already trained model unless a verified retraining/unlearning process exists.

## 10. Training data rules

The event-capture requirement does not equal permission to train a general model. Keep per-event eligibility deny-by-default until DEC-011 and DEC-012 are approved. Maintain institution/user/guardian authorization evidence, provenance, redaction and policy version. Exclude non-permitted events and ensure a dataset build cannot bypass exclusions. Separate internal debugging access from training approval.

## 11. Security testing and release gates

- Dependency and secret scanning.
- Auth/session/recovery abuse tests.
- Tenant isolation and IDOR tests.
- API-key protection and custom-endpoint SSRF tests.
- XSS/CSRF/CORS/security-header tests appropriate to stack.
- Upload size/type/parser-bomb and path traversal tests.
- Prompt injection/RAG poisoning/tool schema tests.
- Audit-log completeness and redaction tests.
- Backup restore and deletion propagation tests.
- Independent review of critical findings before public release.

A critical/high security issue that affects confidentiality, integrity, tenant isolation or privileged access blocks GREEN/release until fixed or owner-approved mitigations are documented with expiry.
