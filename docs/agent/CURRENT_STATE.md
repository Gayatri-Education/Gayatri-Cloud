# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P06 — Content ingestion, indexing and course-scoped RAG  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P05 — File storage abstraction and course lifecycle  
**Branch / commit:** `main`  
**Repository status:** P00, P01, P02, P03, P04, and P05 are GREEN. 36 passing tests covering health, database constraints, isolation repositories, authentication endpoints, organization RBAC, storage abstraction, MIME sniff verification, immutable course versions, offering deployment, and student enrollment. Clean lint and formatting on both backend and frontend.  
**Tests run:** `python -m pytest backend/tests -v` (36 passed in 7.78s), `ruff check` (pass), `ruff format --check` (pass), `npm run lint` (pass), `npm run test` (3 passed).

## Confirmed direction

- Cloud-first web version of Gayatri, independent learners and institutions.
- Decoupled monorepo: FastAPI (Python 3.12) backend, Next.js (TypeScript) frontend.
- Global UserAccount with PBKDF2 hashing, JWT access/refresh token rotation, session device tracking.
- Organizations and memberships isolate tenant contexts.
- Strict RBAC: Student and Teacher cannot be held by same account in organization.
- Object storage abstraction: Local filesystem in dev/test, S3 design in production. Private by default.
- Course versions immutable once published; offering deployments strictly tied to published versions.
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P06: Content ingestion, indexing, and course-scoped RAG pipeline.
