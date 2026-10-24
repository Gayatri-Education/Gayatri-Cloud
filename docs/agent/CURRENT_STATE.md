# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P21 — Release packaging and deployment readiness  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P20 — Integrated verification, end-to-end and load testing  
**Branch / commit:** `main`  
**Repository status:** P00 through P20 are GREEN. 125 passing backend tests and 67 passing frontend tests. Delivered integrated end-to-end system journey (`backend/tests/test_e2e_integrated_journey.py`) verifying the complete 12-milestone product lifecycle: registration, organization creation with RQ-003 invariant enforcement and cross-tenant mutation denial, course authoring and immutable version publishing, offering deployment, 5-tier teacher instructions, intervention queue acknowledgement, parent guardian linking with privacy-filtered views, freemium checkout and idempotent student fee payments, 8-language translations with English fallback, offline course bundle packaging with SHA-256 integrity verification, GDPR Art. 20 data export archive, and account deletion with statutory accounting legal hold retention and student PII pseudonymization. Delivered pilot-scale multi-user concurrency testing engine (`backend/tests/test_load_concurrency.py`) simulating 50 concurrent virtual users measuring latency (p95 < 500ms) and throughput with zero deadlocks and zero race conditions. Delivered frontend vitest integrated cross-portal navigation test suite (`frontend/tests/integrated-e2e-journey.test.ts`). Clean lint across backend and frontend, 31 compiled Next.js routes, and zero open defects.  
**Tests run:** `Push-Location backend ; python -m pytest ; Pop-Location` (125 passed in 35.34s), `Push-Location frontend ; npm run test ; Pop-Location` (67 passed in 2.29s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 31/31 routes static/dynamic).

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
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P21: Release packaging and deployment readiness.
