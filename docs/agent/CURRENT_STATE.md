# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P21 — Release packaging and deployment readiness  
**Phase status:** `AWAITING_OWNER` (Local technical implementation 100% complete across all 21 phases P00–P21; awaiting owner authorization for live AWS provisioning and public launch)  
**Last verified GREEN phase:** P20 — Integrated verification, end-to-end and load testing  
**Branch / commit:** `main`  
**Repository status:** All phases P00 through P21 are technically complete and verified. 132 passing backend tests and 67 passing frontend tests. Delivered multi-stage production Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`), production container orchestration (`docker-compose.prod.yml`, `nginx/nginx.conf`), pilot deployment runbook (`docs/deployment/PILOT_DEPLOYMENT_RUNBOOK.md`) detailing single-instance EC2 architecture, VPC security groups (zero open port 22, AWS SSM Session Manager access), zero-downtime Alembic migrations and rollback procedures, automated daily encrypted backup snapshots and disaster recovery drill runbook, environment configuration template (`.env.production.example`) with zero hardcoded credentials, automated release verification script (`scripts/release_verification.py`), cryptographically verifiable release manifest (`release-manifest.json`), and owner pre-flight release checklist (`docs/deployment/RELEASE_CHECKLIST.md`). Clean lint across backend and frontend, 31 compiled Next.js routes, and zero open defects.  
**Tests run:** `Push-Location backend ; python -m pytest ; Pop-Location` (132 passed in 36.12s), `Push-Location frontend ; npm run test ; Pop-Location` (67 passed in 3.95s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 31/31 routes static/dynamic in standalone mode), `python scripts/release_verification.py` (pass, 6 artifacts verified).

## Confirmed direction

- Cloud-first web version of Gayatri, independent learners and institutions.
- Decoupled monorepo: FastAPI (Python 3.12) backend, Next.js (TypeScript) frontend.
- Global UserAccount with PBKDF2 hashing, JWT access/refresh token rotation, session device tracking.
- Organizations and memberships isolate tenant contexts.
- Strict RBAC: Student and Teacher cannot be held by same account in organization.
- Object storage abstraction: Local filesystem in dev/test, S3 design in production.
- Course versions immutable once published; offering deployments strictly tied to published versions.
- Hybrid RAG (lexical BM25 + dense semantic embeddings) strictly scoped to course version and tenant.
- Server-side AI provider gateway with AES-256-GCM encrypted keys and zero raw secret exposure to browser.
- Standardized tutoring benchmark suite and quality-first router with model promotion threshold gating.
- Tutor orchestration combining 5-tier teacher instructions, configurable pedagogies, XML document enclosures, and deterministic mastery state machines with stability formulas.
- Assessment engine supporting MCQ, Boolean, Numerical (±2% tolerance, units), Rubric-based Subjective evaluation with misconception detection, AST coding tasks, timed exams with autosave, and anti-leakage protection.
- Event capture and archive with transactional outbox, immutable S3 storage batching, telemetry redaction, deny-by-default training governance (DEC-011), and human dataset sign-off gates.
- Student portal web UI in Next.js 14 App Router delivering learner onboarding, tutoring streaming, assessments, mastery roadmap, and BYOK key vault.
- Teacher portal with rosters, 5-tier instruction cascade, cohort analytics, and AI Copilot briefing.
- Parent portal with multi-child switcher, privacy-filtered progress, completed assessments, and notices.
- Admin portal with operational telemetry, member role lifecycle (RQ-003), domain proofs, AI model policy, and audit trail.
- Billing portal with freemium tier checkout, institutional fees, idempotent webhooks, and receipts.
- Localization in 8 languages, offline lesson bundles with SHA-256 checksums and staleness detection, accessibility controls.
- Security hardening: SSRF guard, OWASP headers, machine-readable data export, deletion grace period, statutory financial legal hold retention with PII pseudonymization.
- Observability and reliability: Prometheus metrics exporter, circuit breakers with emergency kill-switch, deep dependency readiness probes, and disaster recovery simulation drills.
- Integrated verification and load testing: 12-milestone holistic E2E journey, negative cross-tenant isolation, 50-user concurrency stress testing with zero deadlocks.
- Release packaging: Multi-stage Dockerfiles, Docker Compose production stack, automated release verification, single-EC2 pilot deployment runbook, and pre-flight checklist.
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open owner authorizations: Live AWS provisioning (DEC-004, DEC-005) and domain assignment.

## Exact next action

Owner review of `docs/deployment/RELEASE_CHECKLIST.md` and authorization for live AWS pilot deployment.
