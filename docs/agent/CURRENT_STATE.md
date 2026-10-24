# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P10 — Assessment, evaluation and grading  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P09 — Tutor orchestration and adaptive learning engine  
**Branch / commit:** `main`  
**Repository status:** P00 through P09 are GREEN. 60 passing tests covering health, database constraints, isolation repositories, authentication endpoints, organization RBAC, storage abstraction, MIME sniff verification, immutable course versions, multi-format extraction, prompt-injection defense, course-scoped hybrid RAG, AES-256-GCM credential encryption, provider adapter contracts, gateway rate-limit fallback, SSE streaming, tutoring benchmarks, quality-first routing, teacher instruction cascade, pedagogical modes, and deterministic mastery updating with misconception tracking. Clean lint and formatting on both backend and frontend.  
**Tests run:** `Push-Location backend; python -m pytest; Pop-Location` (60 passed in 11.70s), `ruff check` (pass), `ruff format --check` (pass), `npm run lint` (pass), `npm run test` (3 passed).

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
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P10: Assessment, evaluation and grading.
