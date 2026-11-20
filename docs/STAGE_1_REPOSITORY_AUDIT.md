# Stage 1 — Repository Audit and Verified Baseline

**Audit snapshot:** 20 November 2026  
**Repository:** KrishnaGopalYadav/PrepCompass  
**Audited ref:** main after PR #14 (UI option 2)  
**Purpose:** distinguish code present, automated tests, user-reported manual checks, and designs that are not yet implemented.

## Executive summary

PrepCompass is a local-first Next.js + FastAPI + SQLite application for UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO. The application already has accounts, study logging, planner setup and rolling plans, a source-linked but explicitly incomplete syllabus catalogue, diagnostics foundations, provider-neutral AI generation and a responsive multi-page UI.

Stage 1 confirms that **RAG, document ingestion, embeddings, vector retrieval, automated PYQ acquisition, mock-test delivery, adaptive mastery, and scheduled GS publishing are not implemented merely because architecture documents describe them**. Stage 2 adds the first structured, queryable resource and PYQ discovery foundation.

## Evidence and status vocabulary

- **Implemented:** relevant code/schema/API exists on the audited branch.
- **Automated-tested:** a corresponding automated test exists; passing status must be taken from a recorded run, not inferred from the test file.
- **User-verified:** user explicitly reported a manual check.
- **Documented only:** design or roadmap exists without runtime implementation.
- **Not implemented:** no corresponding runtime capability was found in the audited tree.
- **Partial / needs verification:** code exists but coverage, correctness or production behavior is not established.

## Repository inventory

| Area | Current evidence | Assessment |
|---|---|---|
| Frontend | Next.js 14, React 18, TypeScript; routes for dashboard, login, planner, daily plan, syllabus, diagnostics, study log and settings | Implemented; UI option 2 merged in PR #14 and user manually verified |
| API | FastAPI application in backend/app/main.py | Implemented |
| Persistence | SQLite with additive schema initialization; local data volume | Implemented; production concurrency/backup limits remain |
| Authentication | Email/password, scrypt hashes, opaque hashed sessions, HTTP-only cookie; optional Google OAuth state + PKCE | Implemented; rate limiting, email verification and password recovery remain gaps |
| Planner | Multi-exam profile, target years, rolling 28-day plan and task tracking | Implemented foundation; topic completeness and plan quality require validation |
| Syllabus | Cycle-specific source records, outline nodes, optional-subject catalogues and APIs | Partial; explicit baseline_incomplete state; 2028 syllabus must await applicable official notices |
| Diagnostics | Metrics engine, persisted reports and optional AI interpretation | Implemented foundation; validate local diagnostics changes and full tests on the developer machine |
| AI providers | Gemini/Groq/Ollama provider adapter and safe readiness status | Provider integration exists; quotas, model availability and provider terms change |
| RAG | Prior architecture proposal specifies FTS5 + Qdrant + Ollama embeddings | Documented only; no ingestion/retrieval runtime found |
| Content ingestion | Source discovery architecture described | Not implemented as a scheduled worker |
| PYQ library | New metadata-only collections and source endpoints in this PR | Discovery catalogue only; no paper binary ingestion, question extraction or answer-key validation |
| Mock tests | Roadmap/design references | Not implemented as a complete test engine |
| Adaptive learning | Design proposes mastery and spaced repetition | Not implemented |
| Daily/weekly/monthly GS | Publishing architecture described | Not implemented |
| Deployment | Docker Compose for frontend/API; frontend and backend CI workflows | Implemented local foundation; no production-grade operations claim |

## Existing architecture and constraints

- Frontend: Next.js 14, React 18, TypeScript, lucide-react.
- API: FastAPI, Pydantic v2, httpx.
- System-of-record database: SQLite.
- Authentication: scrypt password hashing, hashed opaque session tokens, HTTP-only cookies, optional Google OAuth 2.0 with state validation and PKCE.
- AI: provider-neutral Gemini/Groq/Ollama adapter; no paid OpenAI fallback.
- Local runtime: Docker Compose.
- Tests/CI: pytest and GitHub Actions workflows for backend tests and frontend build.
- Proposed but not yet present before Stage 2: SQLite FTS5, Qdrant, Ollama embeddings, document parsers, scheduled worker.

SQLite is suitable for the current single-machine/local-first deployment. Before multi-instance hosted deployment, introduce PostgreSQL, migration discipline, job leasing/queueing, object storage and backup/restore verification. Do not add distributed infrastructure prematurely.

## Stage 2 changes in this PR

1. Add an idempotent resource registry containing official and high-value secondary sources, source authority, exam scope, canonical/landing URLs, update cadence and usage notes.
2. Add exam- and stage-specific PYQ collection metadata for CSE, IFoS, PCS and ACF/RFO. Keep shared CSE/IFoS preliminary papers logically cross-referenced rather than implying distinct question sets.
3. Add authenticated read-only APIs for source discovery and PYQ collection discovery.
4. Add a reusable GS and exam topic taxonomy with stable topic IDs and exam-specific mappings.
5. Add source governance, acquisition, provenance, quality and copyright policies.
6. Preserve an explicit distinction between discovery metadata and actual acquired/verified paper content.

## Known gaps and risks

- The UPPSC portal is dynamic; attachments may expire or be visible only through filters. A discovered year list is not a completeness assertion.
- Official source pages can change URL structure. Store the retrieval timestamp, status and canonical URL when future ingestion is implemented.
- Syllabus records currently cover historical/current cycles, not a verified 2028 syllabus.
- No question-level PYQ rows are being claimed by this stage. Question extraction, paper OCR, answer keys and topic tagging require separate validation.
- No copyright permission is implied by public accessibility. NCERT explicitly prohibits redistribution of its textbooks as part of digital content packages; link users to the official portal instead.
- Secondary explainers (e.g. PRS) are useful context but must never be relabelled as government primary sources.
- Data freshness and correctness need monitoring, not one-time hard-coded assumptions.

## Next implementation gates

- Stage 2A: automated source discovery with fetch status, checksum, change detection and retry/backoff.
- Stage 2B: permitted document acquisition, OCR/text extraction, page locators, deduplication and human review.
- Stage 2C: question-level PYQ schema, verified answer-key linkage, syllabus tagging and import audit trail.
- Stage 3: lexical + vector RAG, citations, evaluation set and refusal on insufficient evidence.
- Stage 4: scheduled daily GS / weekly and monthly magazines with editorial review and traceable citations.
- Stage 5: account-scoped mastery, revision and explainable adaptive planning.

## Acceptance criteria for this audit

- Existing modules are described without claiming architecture documents are runtime features.
- Each exam retains distinct syllabus, paper and cycle identity.
- Official sources are preferred and secondary sources are labelled.
- Resource/PYQ APIs require authentication and validate exam/stage filters.
- No private user data, API secrets, copyrighted books or unverified PYQ text are added.
