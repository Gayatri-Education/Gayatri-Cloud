# Current State — Resume Checkpoint

> Keep this file short. The phase log and design docs hold the details. This file is the first place an agent should look after context loss.

**Checkpoint created:** 2026-10-24  
**Timezone:** Asia/Kolkata  
**Current phase:** P07 — AI provider gateway, API credentials and model discovery  
**Phase status:** `NOT_STARTED`  
**Last verified GREEN phase:** P06 — Content ingestion, indexing and course-scoped RAG  
**Branch / commit:** `main`  
**Repository status:** P00 through P06 are GREEN. 44 passing tests covering health, database constraints, isolation repositories, authentication endpoints, organization RBAC, storage abstraction, MIME sniff verification, immutable course versions, multi-format extraction, prompt-injection defense, and course-scoped hybrid RAG. Clean lint and formatting on both backend and frontend.  
**Tests run:** `python -m pytest backend/tests -v` (44 passed in 8.21s), `ruff check` (pass), `ruff format --check` (pass), `npm run lint` (pass), `npm run test` (3 passed).

## Confirmed direction

- Cloud-first web version of Gayatri, independent learners and institutions.
- Decoupled monorepo: FastAPI (Python 3.12) backend, Next.js (TypeScript) frontend.
- Global UserAccount with PBKDF2 hashing, JWT access/refresh token rotation, session device tracking.
- Organizations and memberships isolate tenant contexts.
- Strict RBAC: Student and Teacher cannot be held by same account in organization.
- Object storage abstraction: Local filesystem in dev/test, S3 design in production.
- Course versions immutable once published; offering deployments strictly tied to published versions.
- Hybrid RAG (lexical BM25 + dense semantic embeddings) strictly scoped to course version and tenant.
- Remote repository: `https://github.com/Gayatri-Education/Gayatri-Cloud.git`.

## Open blockers / decision references

- DEC-001, DEC-002, DEC-003, DEC-011 are `APPROVED`.
- DEC-C01 to DEC-C35 confirmed by owner.
- Open decisions: `DEC-004` to `DEC-010`, `DEC-012` to `DEC-017` (provisional options documented, non-blocking).

## Exact next action

Execute Phase P07: AI provider gateway, API credentials and model discovery.
