# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P13 — Teacher and academic-administration portal  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P12 — Student portal  
**Branch / commit:** `main`  
**Repository status:** P00 through P12 are GREEN. 75 passing backend tests and 14 passing frontend tests. Delivered full student portal in Next.js 14 App Router: learner dashboard with enrolled courses, active streak, and retention queue; course catalog with pinned version tags; interactive Socratic tutor chat with SSE streaming, citation pills, and helpfulness feedback; assessment runner across all 6 question types with countdown timer and draft autosave; assessment result view with rubric criteria scoring and misconception alerts; visual concept mastery roadmap; organization context switcher isolating personal and school contexts; BYOK encrypted AI key vault with masked keys; transparent DEC-011 training consent governance; and actionable recovery error states. Clean lint, successful production build, and zero open defects.  
**Tests run:** `Push-Location backend; python -m pytest; Pop-Location` (75 passed in 33.47s), `cd frontend; npm run test` (14 passed in 2.00s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 10/10 routes static/dynamic).

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
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P13: Teacher and academic-administration portal.
