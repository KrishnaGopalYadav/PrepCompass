# PrepCompass Project Audit and Verification Baseline

Audit date: 2026-11-19  
Repository: KrishnaGopalYadav/PrepCompass  
Remote main HEAD inspected: 018af133c1aa6ec7b0f93da4a66b4a7bfc211250 (merge PR #11)

> Status convention: implemented means code exists; tested means a test result was observed; planned means design only. Do not treat these as interchangeable.

## 1. Final project goal

PrepCompass is a local-first, multi-exam preparation platform for UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO. It should provide:
- Candidate profile, multi-exam planner, daily execution and study tracking.
- Versioned, source-linked syllabus and resource catalogue.
- Official PYQ library, practice questions, mocks, scoring and answer feedback.
- Source-grounded RAG over official and permitted learning material.
- Personal adaptive learning: topic mastery, weak-area analysis and spaced revision.
- Daily official-source discovery and knowledge-base refresh.
- Daily GS briefs, weekly GS magazines and monthly GS magazines.
- Secure private accounts, backup/export and eventual cross-platform access.

Exam-cycle accuracy and provenance are core requirements. A partial syllabus must not be described as complete or 2028-verified. Official PYQs must never be confused with AI-generated questions. AI content must not silently become trusted knowledge. No outcome or exam success should be guaranteed.

Initial planning context discussed: 2028 targets, English medium, roughly 2–3 study hours/day, and the four exams above. Optional-subject rules must always be checked against the relevant official notification.

## 2. Pull request history

### PR #1 — Build PrepCompass Phase 1 local-first foundation
Introduced Next.js/React/TypeScript frontend, FastAPI API, SQLite persistence and Docker Compose. Added dashboard, health/dashboard endpoints, study-session logging, daily/weekly goal cards, recent activity, persistent data volume and setup/privacy/roadmap docs. Rationale: establish a simple local-first foundation before exam-specific features.

### PR #2 — Add multi-user accounts and secure authentication
Added email/password registration/login/logout/me, optional Google OAuth 2.0 with state validation and PKCE, scrypt password hashes, opaque random session tokens stored as hashes, HTTP-only cookies, account-scoped study sessions and additive SQLite migration. Legacy rows remain unassigned to avoid leaking old data. Google credentials are application-operator configuration, not uploaded by end users. Follow-ups stated in PR: rate limiting, email verification, password reset, HTTPS secure cookies and explicit legacy-data claim/import flow.

### PR #3 — Add personalised exam planner foundation and responsive setup UI
Added seeded exam catalogue for CSE, IFoS, PCS and ACF/RFO; user-scoped planner profile and exam targets; independent attempt year/priority per exam; preparation date, medium, hours, selected weekdays, rest day and level; authenticated setup/overview APIs; guided responsive setup UI; tests and CI. This stores a profile; it does not yet create a verified complete schedule. PR records 8 backend tests passed.

### PR #4 — Generate rolling daily study plans and track task progress
Intermediate feature-branch proposal: deterministic schedule, 15% capacity reserve, learning/active recall/practice blocks, versioned plans, task updates, daily page and tests. It explicitly used provisional topics. No merge commit was found in the inspected recent main history; PR #5 is the canonical mainline daily-plan integration.

### PR #5 — Add rolling daily study plans and progress tracking to main
Integrated 28-day deterministic planning into main, using profile availability and a capacity buffer. Added plan/task persistence, authenticated generate/read/update APIs, daily task completion and actual-minute tracking, tests and docs. The starter topic catalogue remains provisional, not a complete official syllabus.

### PR #6 — Add source-linked syllabus catalogue and optional subject selection
Added source-cycle-aware syllabus source records and outline nodes for CSE 2026, IFoS 2026 and UPPSC PCS/ACF-RFO 2025; stage/paper/topic structure; source locators; explicit common-prelims crosswalks; optional-subject catalogues and server-side combination validation; authenticated APIs and /syllabus UI. PR records 16 backend tests and a successful Next.js production build. Limitations: incomplete outline, not a verified 2028 syllabus; UPPSC source was a third-party mirror requiring official cross-check; old plan history was not rewritten.

### PR #7 — Document Forestry and Geology syllabus mapping for IFoS and ACF/RFO
Documentation-only mapping specification. Separates IFoS Gazette source cycle from UPPSC ACF/RFO source cycle; defines paper/section hierarchy, concept clusters and resource metadata; warns that topic overlap is not syllabus equivalence. No code/tests. No merge commit was found in the inspected recent history; verify current PR state before treating its documentation as part of main.

### PR #8 — Add OpenAI provider foundation for agentic exam preparation coach
Introduced server-side OpenAI Responses API adapter, env-based key/model, authenticated readiness endpoint, secret non-disclosure tests and setup/agent architecture docs. This was a provider foundation, not a complete agent. PR #9 later replaced this direction; OpenAI is not the intended inference path.

### PR #9 — Replace paid OpenAI inference with free hybrid AI providers
Replaced provider-specific OpenAI interface with provider-neutral JSON generation for Gemini Developer API, GroqCloud and local Ollama. Added ordered fallback, hosted model allowlists, no paid OpenAI fallback, secret-safe status/errors, tests and setup docs; removed OpenAI SDK. User-reported live checks: Groq and Ollama generation passed; Groq→Ollama and Gemini→Groq fallback passed; Gemini-only request timed out/failed with root cause not established. User later reported full backend tests passed after fixing a test fixture to use an allowed Gemini model. Provider free-tier limits, availability and data terms can change.

### PR #10 — Redesign PrepCompass frontend with dedicated feature workspaces
Merged commit: 1124acbfc839d4543be7119be3af982b9fd98fd3. Added shared responsive shell, collapsible desktop sidebar/mobile drawer, redesigned login/register and dashboard, dedicated Study Log, AI Diagnostics and Settings pages, shared navigation for planner/daily plan/syllabus, consistent responsive UI patterns. Important dependency: Diagnostics UI calls backend diagnostics endpoints that were uncommitted in the user's local state at the time. Deploy UI and diagnostics backend together.

### PR #11 — Plan RAG knowledge, adaptive learning and GS publishing engine
Merged commit: 018af133c1aa6ec7b0f93da4a66b4a7bfc211250. Documentation/architecture only. Specifies source registry, source trust/versioning, PDF/HTML extraction, deduplication, FTS5 + Qdrant hybrid search, Ollama embeddings, citations, official-vs-generated PYQ provenance, mocks, account-scoped mastery, spaced repetition, daily/weekly/monthly GS publishing, worker, APIs and R0–R6 roadmap. It does NOT implement RAG, Qdrant, embeddings, connectors, ingestion worker, PYQ runtime, mocks, adaptive learner or magazine scheduler.

PR links: [#1](https://github.com/KrishnaGopalYadav/PrepCompass/pull/1) · [#2](https://github.com/KrishnaGopalYadav/PrepCompass/pull/2) · [#3](https://github.com/KrishnaGopalYadav/PrepCompass/pull/3) · [#4](https://github.com/KrishnaGopalYadav/PrepCompass/pull/4) · [#5](https://github.com/KrishnaGopalYadav/PrepCompass/pull/5) · [#6](https://github.com/KrishnaGopalYadav/PrepCompass/pull/6) · [#7](https://github.com/KrishnaGopalYadav/PrepCompass/pull/7) · [#8](https://github.com/KrishnaGopalYadav/PrepCompass/pull/8) · [#9](https://github.com/KrishnaGopalYadav/PrepCompass/pull/9) · [#10](https://github.com/KrishnaGopalYadav/PrepCompass/pull/10) · [#11](https://github.com/KrishnaGopalYadav/PrepCompass/pull/11)

## 3. Technology choices and rationale

| Layer | Technology | Reason / boundary |
|---|---|---|
| Frontend | Next.js 14, React 18, TypeScript | Route-based UI and typed components |
| Icons | lucide-react | Consistent UI iconography |
| API | FastAPI, Python | Typed APIs and Python data ecosystem |
| Validation/HTTP | Pydantic v2, httpx | Input validation and async HTTP |
| Database | SQLite | Local-first system of record for initial single-node deployment |
| Auth | scrypt, hashed opaque sessions, HTTP-only cookies | Password/session security |
| SSO | Google OAuth 2.0 + state + PKCE | Optional application-configured sign-in |
| AI generation | Gemini, Groq, Ollama | Free-tier hosted options plus local inference |
| Runtime | Docker Compose | Reproducible local services |
| Tests/CI | pytest, GitHub Actions | Regression and automated build checks |
| Planned vector DB | Qdrant | Semantic search; not implemented |
| Planned lexical search | SQLite FTS5 | Exact terms, dates, named entities; not implemented |
| Planned embeddings | Ollama embedding model (e.g. nomic-embed-text) | Local embeddings; not implemented |
| Planned parsing | PyMuPDF/pypdf + HTML parser | Page-aware source extraction; not implemented |
| Planned jobs | Separate Python worker | Daily ingestion and scheduled publishing; not implemented |

Hybrid lexical + vector retrieval is proposed because exact names, laws, dates and scheme terms benefit from lexical search, while semantic queries benefit from vectors. First-generation self-learning should be deterministic and explainable (performance evidence, recency, confidence and spaced repetition), not uncontrolled model fine-tuning.

## 4. Current code baseline and local-only work

Remote main inspected includes the frontend, FastAPI, SQLite auth/study/planner/syllabus functionality, provider-neutral AI adapter, PR #10 UI and PR #11 architecture document.

The latest local status supplied by the user was:

```
## main...origin/main
 M backend/.env.example
 M backend/app/ai_provider.py
 M backend/app/main.py
 M backend/tests/test_ai_provider.py
?? .vscode/
?? PrepCompass/
?? backend/app/diagnostics_engine.py
?? backend/tests/test_diagnostics.py
```

The user's local diagnostics implementation is described as:
- new diagnostics engine and tests;
- user-scoped diagnostics table and metrics for a configurable 7–90 day period;
- study-session, subject distribution, planner task completion/planned/actual metrics;
- authenticated create/list/detail diagnostics endpoints;
- AI summary, strengths, weaknesses, risks and recommendations;
- metrics retained when AI fails; insufficient data skips AI;
- tests for persistence, AI failure, insufficient data, period validation, auth and account isolation.

The user reported all backend tests passed after correcting the Gemini test model to an allowlisted ID. The diagnostics-focused test run previously reported 6 passed. The exact final full-suite output/count was not supplied, so this is user-reported evidence, not independently reproduced here. The untracked .vscode/ and PrepCompass/ directories have not been inspected; do not delete them.

## 5. Audit verification and environment limitations

Remote source/history inspection covered README, backend main entry point, AI provider module, dependency manifests, Docker Compose and RAG architecture document. PR #1–#11 descriptions and recent commits were inspected. Merge commits for PR #9, #10 and #11 were confirmed. Remote main HEAD is 018af133c1aa6ec7b0f93da4a66b4a7bfc211250.

An isolated virtual environment was created outside the repository at /tmp/prepcompass-audit-venv using Python 3.13.5 and pip 25.1.1. It is currently empty apart from pip. An attempt to clone the repository to /tmp/prepcompass-audit failed because this runtime could not resolve github.com (DNS/network unavailable). Therefore dependencies could not be installed and the complete pytest suite, Next.js build and Docker build could not be rerun in this environment. The GitHub workflow-run lookup returned no PR-triggered runs for the inspected merge commits; this is not proof that CI did not run, only that the runs could not be independently verified through that lookup.

## 6. Gaps and risks

### P0 — stability and integration
1. Reconcile local diagnostics/provider edits with remote main; keep local uncommitted changes safe.
2. Independently rerun backend tests, frontend production build, Docker build and API smoke tests on one exact commit.
3. Test fresh database initialization and migration from a previous schema; verify no data loss.
4. Test provider success/fallback/all-provider failure, malformed JSON, timeout, allowlist, and secret redaction. Gemini-only failure remains unexplained.
5. Verify PR #10 Diagnostics page against the local diagnostics API; handle unauthenticated, loading, empty, provider failure and validation states.

### P1 — planned product features not yet implemented
- No RAG runtime, document ingestion or source registry.
- No PDF/page extraction, chunking, versioning, deduplication or review queue.
- No FTS5 or Qdrant indexing, embedding pipeline or index rebuild.
- No official PYQ corpus/coverage dashboard, question bank or mock attempt runtime.
- No mastery model, spaced revision or adaptive plan runtime.
- No daily source refresh worker, daily GS publisher, weekly/monthly magazine generation or archive.
- No source freshness dashboard, retries, alerts or pipeline observability.

### P2 — data, security and scale
- Syllabus is incomplete and not a verified 2028 syllabus; mirrored UPPSC source needs official cross-check.
- Provisional planner topic catalogue needs replacement with verified topic trees/resources.
- Public-launch auth hardening: rate limiting, email verification, password reset, HTTPS and secure cookie deployment.
- Review CORS/CSRF, OAuth callback, session revocation and account isolation.
- Future ingestion requires domain allowlists, SSRF protections, size/time limits, safe file parsing and prompt-injection defenses.
- SQLite is for local single-node deployment; hosted multi-instance scale will need PostgreSQL and a job queue.
- Backup/restore for DB, source files and vector index is not yet implemented.
- Check copyright and reuse terms before bulk ingestion or republication.

## 7. Acceptance gates for a stable baseline

Run all checks against the same recorded commit SHA.

**Backend**
- Create a clean virtual environment outside the repository.
- Install backend/requirements-dev.txt.
- Run pytest -q and record exact pass/fail/skip counts.
- Run python -m compileall -q backend/app backend/tests.
- Exercise auth, OAuth configured/unconfigured, account isolation, study sessions, planner, syllabus, AI provider and diagnostics APIs.
- Test fresh DB and migration from an existing DB.

**Frontend**
- Run npm ci and npm run build.
- Verify all routes: login/register, dashboard, study log, planner, daily plan, syllabus, diagnostics and settings.
- Browser-test mobile navigation, expand/collapse, API integration, cookie behavior, logout and error/empty/loading states.

**Docker**
- Build both images from the same commit.
- Start with fresh and existing data volumes.
- Verify /api/health, /docs, frontend routes, authenticated workflows, persistence after restart and logs.

**AI**
- Mocked deterministic tests in CI; separate live provider smoke tests as network/quota dependent.
- Confirm no paid fallback and no secret leakage.

**RAG**
- Do not call RAG implemented until one official source can be ingested, versioned, extracted with page locators, chunked, indexed in lexical/vector stores, retrieved by an authenticated query and cited to the exact source locator. Re-ingestion must be idempotent; unsupported questions must return insufficient evidence.

## 8. Recommended execution order

1. Preserve and inspect local diagnostics/provider changes and unknown untracked directories.
2. Reconcile local code with remote main and make a clean diagnostics implementation PR.
3. Obtain a complete source checkout in a network-enabled environment and use an isolated venv outside the repository.
4. Run backend tests, frontend build, Docker build and API smoke tests on the same commit; fix and rerun until green.
5. Add integration tests for the Diagnostics UI/API dependency.
6. Record exact test counts, tool versions and commit SHA in this audit.
7. Only then start R0/R1 RAG on a separate feature branch.

Do not delete branches/untracked files, reset the user's worktree, merge unverified changes or rebuild the user's Docker environment before the acceptance gates pass.
