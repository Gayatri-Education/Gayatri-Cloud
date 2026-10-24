# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P21 — Release packaging and local pre-flight verification  
**Phase status:** `GREEN` (Local verification 100% certified with zero defects; all 7 pre-flight harness phases PASS; ready for EC2 pilot upload upon owner authorization)  
**Last verified GREEN phase:** P21 — Release packaging and local pre-flight certification  
**Branch / commit:** `main`  
**Repository status:** All phases P00 through P21 are technically complete, tested, and certified locally. 132 passing backend tests and 67 passing frontend tests. Delivered 7-phase unified local pre-flight certification harness (`scripts/run_local_preflight.py`), local developer stack orchestrator (`scripts/dev_local_stack.py`), local verification and manual testing guide (`docs/operations/LOCAL_PREFLIGHT_VERIFICATION_GUIDE.md`), and certification report (`local-preflight-report.json` with verdict `CERTIFIED_READY_FOR_DEPLOYMENT`). Resolved SSR hydration mismatch error by guarding client-only states (network status, user session) until mount. Decluttered frontend navigation with role-specific navbars and a 1-Click Role Switcher. Added missing `/api/v1/organizations/memberships` endpoint and automatic tenant context resolution for personal/public viewing. Hardened course version query ordering for deterministic offline bundle staleness checks. Executed comprehensive frontend defensive hardening across all 33 components and all 31 Next.js application routes to safeguard collection mapping (`.map`), object indexing, and null states against API schema variations. Clean lint across backend and frontend, 31 compiled Next.js routes, and zero open defects.  
**Tests run:** Backend pytest 132/132 PASS; Frontend vitest 67/67 PASS; ESLint 0 warnings/errors.

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
