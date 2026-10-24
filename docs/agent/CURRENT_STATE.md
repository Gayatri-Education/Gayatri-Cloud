# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P14 — Parent/guardian portal  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P13 — Teacher and academic-administration portal  
**Branch / commit:** `main`  
**Repository status:** P00 through P13 are GREEN. 82 passing backend tests and 23 passing frontend tests. Delivered teacher domain models (TeacherIntervention, ClassAnnouncement), TeacherService, REST APIs for rosters, cascade directives, analytics, interventions, and copilot briefings. Delivered Next.js 14 Teacher Web UI: searchable class roster with mastery progress and misconception counts, 5-tier instruction cascade editor (ORG, COURSE, CLASS, STUDENT, SESSION) with priority sliders and deactivation, class analytics with cohort mastery distributions and hardest concepts, intervention queue with severity badges and acknowledge/resolve workflow, evidence-grounded AI copilot briefing card with explicit uncertainty notice, and assessment oversight with manual grade adjustments. Clean lint, 15 compiled Next.js routes, and zero open defects.  
**Tests run:** `Push-Location backend ; python -m pytest ; Pop-Location` (82 passed in 30.24s), `Push-Location frontend ; npm run test ; Pop-Location` (23 passed in 1.55s), `npm run lint` (pass, 0 warnings), `npm run build` (compiled successfully, 15/15 routes static/dynamic).

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

Execute Phase P14: Parent/guardian portal.
