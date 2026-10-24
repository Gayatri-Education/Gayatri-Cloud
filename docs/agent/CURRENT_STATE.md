# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P20 — Integrated verification, end-to-end and load testing  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P19 — Observability, reliability and recovery  
**Branch / commit:** `main`  
**Repository status:** P00 through P19 are GREEN. 123 passing backend tests and 59 passing frontend tests. Delivered observability, reliability, and recovery layer: thread-safe metrics collector (`MetricsCollector`) tracking HTTP traffic, AI provider latencies, token consumption, and outbox lag with Prometheus text exposition (`/metrics/prometheus`); circuit breaker state machine (`CLOSED` -> `OPEN` -> `HALF_OPEN` -> `CLOSED`) with 503 fast-fail and administrative emergency kill-switch; deep readiness health probe (`DeepHealthService`) inspecting database, storage volume, outbox backlog, and circuit breakers with sanitized diagnostics; backup and recovery simulator (`BackupRecoverySimulator`) generating point-in-time snapshot manifests with SHA-256 verification and simulated disaster recovery drills with zero data divergence. Delivered Next.js 14 Admin Observability & Reliability Portal (`/admin/observability`), deep health cards, interactive breaker toggles, and snapshot recovery verification panel. Clean lint, 31 compiled Next.js routes, and zero open defects.  
**Tests run:** `Push-Location backend ; python -m pytest ; Pop-Location` (123 passed in 31.31s), `Push-Location frontend ; npm run test ; Pop-Location` (59 passed in 3.49s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 31/31 routes static/dynamic).

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
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P20: Integrated verification, end-to-end and load testing.
