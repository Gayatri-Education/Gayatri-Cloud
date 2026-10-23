# Deployment and Recovery Runbook — Gayatri Cloud

**Status:** Proposed operational baseline; not an approval to provision resources or deploy publicly. Owner authorization required before paid AWS resources, live provider usage, payment activation or public release.

## 1. Proposed AWS baseline

- EC2 hosts the web/API application and worker initially.
- RDS PostgreSQL is the proposed transactional database (DEC-001 approval needed).
- S3 stores private course/source objects, generated files, event archives, exports, approved dataset artifacts and backups as appropriate.
- Server-side secrets stored with an approved encrypted secret-management approach.
- TLS at the public ingress, limited inbound ports, least-privilege instance/task roles, private database access and S3 bucket policies.
- Logs/metrics/alarms, database backup policy, S3 versioning/lifecycle where appropriate and a tested restore process.

One EC2 instance is acceptable only for a bounded pilot and is a single point of failure. A public production target must separately decide whether multi-instance deployment, load balancing, autoscaling and a multi-AZ database are required and affordable.

## 2. Provisioning gate

Do not provision until the owner-approved infrastructure ADR records:
- AWS region and data residency rationale;
- database decision and engine/version;
- instance/database sizing assumptions based on load test;
- monthly budget ceiling and alerts;
- network/subnet/security-group plan;
- secret-management choice;
- RPO/RTO (maximum acceptable data loss/recovery time);
- backup retention/encryption and restore owner;
- DNS/domain and TLS approach;
- environment separation (development/staging/production);
- rollback and incident communication process.

Use least privilege and infrastructure-as-code where selected. Changes to live infrastructure must be reviewed, planned and reversible. Do not print credentials or customer data during troubleshooting.

## 3. Release pipeline

Before a deployment:
1. Confirm active phase/commit and release candidate identifier.
2. Run lint/type/unit/integration/regression and relevant security checks.
3. Review migration compatibility, backup status and rollback plan.
4. Confirm no secrets, test-only data or disabled security controls are included.
5. Confirm provider/privacy/training policy versions and required approvals.
6. Deploy to a non-production environment first when one exists.
7. Run readiness and smoke checks: health, auth, database, object store, RAG test fixture, provider mock/approved test and tenant-isolation spot checks.
8. Apply migrations in a controlled operation with recorded outcome.
9. Monitor error rates, latency, provider failures, archive backlog, DB pool and cost/usage alerts.
10. Stop or roll back if release gates fail; document what was observed.

## 4. Data backup and restore

Define separate protections for relational data and S3 objects. The design should specify database automated backups/PITR if supported and chosen, S3 versioning or replication where appropriate, encryption keys recovery, archive checksums and retention. Backups need isolation from ordinary application write permissions.

Before production launch, perform and record a restore drill into an isolated environment. Validate:
- restored schema and migration version;
- row counts/integrity for core entities;
- tenant relationships/constraints;
- recent session/learning/assessment state;
- S3 object availability/checksums;
- event archive reconciliation;
- ability to serve a synthetic course and session;
- recovery time and data-loss window relative to approved RTO/RPO.

A backup that has not been restored is not verified recovery capability.

## 5. Database and migration recovery

- Back up before risky migration.
- Prefer expand/migrate/contract changes for production compatibility.
- Do not rely on down migrations where data loss would occur; write a forward repair or restore plan.
- If migration fails, stop application writes if consistency requires it, capture redacted diagnostics, establish schema/data state, and follow the approved rollback/repair plan.
- Never run a destructive fix against production based only on an LLM suggestion.

## 6. Provider outage/usage incident

On provider outage, rate-limit or quota incident:
- inspect normalized error category, provider status, key owner and request correlation;
- avoid repeated retries that amplify load/cost;
- honor provider retry-after and bounded retry policy;
- use fallback only when privacy, organization policy, required capability and payer rules allow it;
- show users the degraded state and whether provider/model changed;
- do not commit learning state for failed/unvalidated turns;
- alert/record if usage exceeds configured warning thresholds.

An emergency AI kill switch should be specified during operations design. Its authorization, audit reason and behavior should be tested before public production use.

## 7. Event archive incident

If outbox/archive backlog grows or count/checksum reconciliation fails:
- preserve pending events and do not purge before durable archive is confirmed;
- inspect worker health and S3/database error category;
- retry idempotently with bounded backoff;
- isolate poison records without discarding them;
- compare source event counts to manifests and replay safe batches;
- alert on oldest event age and lost/duplicate record suspicion;
- document data gaps and whether training/dataset jobs must pause.

Training dataset creation should pause when event archive completeness or eligibility enforcement cannot be demonstrated.

## 8. Security or privacy incident

- Stop affected access path/provider/export immediately when scope is uncertain.
- Preserve necessary audit evidence without copying extra restricted content.
- Rotate/revoke exposed credentials.
- Determine affected tenants/data categories and containment steps.
- Notify designated owner and follow approved legal/contractual notification process.
- Restore from known-good state only after identifying root cause and preventing recurrence.
- Record incident timeline, scope, corrective action, tests and follow-up work.

## 9. Release-readiness record

A release is not approved until the owner has accepted launch mode and unresolved operational decisions, all required checks are green, cost alerts are active, the backup/restore drill is complete, privacy/retention/training policies are operational, and rollback instructions have been reviewed. This document alone does not establish that those steps have happened.
