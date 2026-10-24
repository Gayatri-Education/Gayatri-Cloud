# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P19 — Observability, reliability and recovery  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P18 — Security, privacy, retention and deletion hardening  
**Branch / commit:** `main`  
**Repository status:** P00 through P18 are GREEN. 116 passing backend tests and 54 passing frontend tests. Delivered security hardening layer: SSRF perimeter guard blocking AWS cloud metadata (`169.254.169.254`), loopback, and private RFC-1918 subnets; path traversal protection against `..` and null bytes; OWASP defensive security headers middleware (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy); Data Subject Rights service (`DeletionService`) generating machine-readable JSON exports with SHA-256 verification (GDPR Art. 20); account deletion lifecycle with 7-day grace period, immediate session invalidation, and statutory accounting legal hold retention on billing records with user PII pseudonymization (`deleted_<id>@anonymized.internal`). Delivered Next.js 14 Privacy & Security Settings portal (`/settings/privacy`), one-click export download, deletion modal, and immutable security audit log. Clean lint, 30 compiled Next.js routes, and zero open defects.  
**Tests run:** `Push-Location backend ; python -m pytest ; Pop-Location` (116 passed in 35.71s), `Push-Location frontend ; npm run test ; Pop-Location` (54 passed in 3.01s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 30/30 routes static/dynamic).

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
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P19: Observability, reliability and recovery.
