# PrepCompass AI Knowledge, RAG, Adaptive Learning and GS Content Engine

**Status:** Architecture proposal and implementation blueprint  
**Target examinations:** UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO  
**Initial language:** English  
**Initial deployment:** Local-first Docker Compose on the user's Mac; later portable to a hosted multi-user deployment  
**Core rule:** verified sources are the knowledge authority; AI is an assistant that must cite evidence and expose uncertainty.

## 1. Product outcome

PrepCompass will evolve from a planner and study tracker into an evidence-grounded preparation workspace. It will:

1. Maintain a versioned knowledge base of official notifications, syllabi, PYQs, government publications, current affairs and user-authorised study resources.
2. Refresh source catalogues daily, detect new/changed documents, validate and deduplicate them, and index approved content for retrieval.
3. Provide exam- and syllabus-aware RAG for explanations, topic notes, answer feedback, question generation and study planning.
4. Learn a candidate's strengths, weak areas, pace, revision needs and question performance from their own activity, then propose explainable plan adjustments.
5. Generate a daily GS brief, weekly GS magazine and monthly GS magazine with source links, publication dates, exam mapping and revision questions.
6. Build practice sets and mock tests while keeping official PYQs distinct from AI-generated questions.

## 2. Non-negotiable knowledge and safety rules

- A source document is not authoritative merely because it appears in a search result. Store publisher, source URL, publication date, retrieval date, source type, verification state and document checksum.
- Prefer UPSC, UPPSC, Gazette of India, PIB, relevant Union ministries/departments, government statistical publications, Parliament, Supreme Court and official Uttar Pradesh government sources.
- Mark mirrored or third-party copies as such. Do not label them official-publisher content.
- Keep source cycles separate. A 2026 syllabus must not silently become the 2028 syllabus. Refresh when the relevant official 2028 notification is published.
- Every generated factual claim should carry citations to retrieved source chunks. If retrieval is weak or sources conflict, say so and do not fabricate a confident answer.
- Preserve original documents and their versions. Re-indexing creates new versions; it does not erase historical provenance.
- Separate official PYQs, official answer keys, coaching material with permitted access, user-uploaded content and AI-generated practice questions. Never label synthetic questions as PYQs.
- Respect copyright, robots/access rules, provider terms and personal-data boundaries. Do not scrape paywalled/proprietary coaching content or reproduce copyrighted books/magazines wholesale. Store permitted metadata, user-owned files, links and limited derived notes.
- AI-generated content must never automatically become a trusted source. Human/user review or independent source verification is required before promotion into curated knowledge.
- Do not use candidate-specific personal data to train a shared/global model. User performance data is account-scoped and used only for that user's recommendations unless they explicitly opt into another use.

## 3. Architecture

### 3.1 Components

| Component | Responsibility | Initial implementation |
|---|---|---|
| Source registry | Approved publishers, URLs, schedules, trust levels and exam tags | SQLite tables + admin configuration |
| Ingestion connectors | Fetch pages, feeds, PDFs and official question papers | Python connectors using httpx, BeautifulSoup/trafilatura and PDF extraction |
| Document processor | Extract text, page/section locators, metadata, checksum and language | PyMuPDF or pypdf; HTML parser; normalisation |
| Validation and deduplication | Detect duplicates, stale copies, source changes and suspicious inputs | SHA-256, canonical URL, publisher rules and review state |
| Knowledge metadata store | Source/document/chunk/version provenance and publication records | Existing SQLite database initially |
| Lexical retrieval | Exact terms, names, dates, acts, schemes and paper references | SQLite FTS5 |
| Vector retrieval | Semantic retrieval across document chunks | Qdrant local Docker service |
| Embeddings | Convert chunks and queries to vectors | Ollama local embedding model (e.g. nomic-embed-text), behind an interface |
| RAG orchestration | Filter by exam/cycle/topic/source trust, retrieve, rerank and construct cited prompts | Python service layer; lexical + vector hybrid retrieval |
| AI generation | Grounded JSON/text generation and question generation | Existing Gemini/Groq/Ollama provider adapter; no paid-provider fallback |
| Adaptive learner | Account-scoped mastery, spaced repetition, weak-area and plan adjustment signals | Deterministic metrics first; AI explains recommendations |
| Content publisher | Daily briefs, weekly/monthly magazines, mocks and review workflow | Python jobs + SQLite; authenticated APIs |
| Scheduler/worker | Daily discovery, ingest, generation, retention and retry | Separate Docker worker process; one active scheduler in local deployment |
| Frontend | Knowledge search, source viewer, daily GS, magazines, PYQs, mocks and learning insights | Dedicated Next.js feature pages |

### 3.2 Local-first topology

- FastAPI remains the authenticated API.
- SQLite remains the system of record for accounts, source metadata, jobs, content editions, user performance and audit history.
- Qdrant is a separate persistent Docker service for vector indexes. It is rebuildable from source documents and chunk metadata.
- Ollama provides local embeddings and optional local generation. Existing Gemini/Groq free-tier provider configuration remains available for generation, subject to current provider quotas and terms.
- A separate worker container runs scheduled ingestion and publication. It shares the SQLite data volume and Qdrant network.
- Do not run multiple scheduler replicas against SQLite. A hosted multi-instance deployment should move to PostgreSQL, use a distributed job queue/lease mechanism and managed vector storage.

### 3.3 Retrieval flow

1. Authenticate user and resolve selected exams, target attempt years, language and relevant syllabus nodes.
2. Classify the request (syllabus explanation, current affairs, PYQ, answer feedback, mock generation, etc.).
3. Build retrieval filters for exam, stage, paper, topic, source type, source trust, publication window and document version.
4. Retrieve candidates from SQLite FTS5 and Qdrant in parallel.
5. Merge and rerank; prioritise official and primary sources while retaining relevant secondary sources as clearly labelled context.
6. Assemble a context window with source IDs, page/paragraph locators and publication dates.
7. Generate an answer constrained to the supplied evidence and a strict output schema.
8. Validate citation IDs against retrieved chunks; reject invented citations.
9. Return answer, citations, confidence/coverage warning, source freshness and a feedback action.
10. Record retrieval and answer provenance for audit and later quality evaluation.

A response without adequate evidence should return an explicit insufficient-evidence state rather than fill gaps from model memory.

## 4. Data model (initial logical schema)

All tables below are proposed additions; implementation should use additive, idempotent migrations and preserve existing user, planner, syllabus and study-session records.

### 4.1 Sources and knowledge documents

- `knowledge_sources`: source_id, name, publisher, source_type, base_url, allowed_domains, trust_tier, exam_ids, fetch_strategy, schedule, enabled, last_checked_at, last_success_at.
- `source_fetch_runs`: run_id, source_id, started_at, completed_at, status, http_status, discovered_count, changed_count, error_summary.
- `knowledge_documents`: document_id, source_id, canonical_url, title, document_type, exam_ids_json, syllabus_node_ids_json, publication_date, retrieved_at, content_hash, language, mime_type, storage_path, source_trust, verification_status, version_number, supersedes_document_id.
- `knowledge_chunks`: chunk_id, document_id, version_number, chunk_index, page_number, section_path, text, token_estimate, content_hash, embedding_model, vector_point_id, indexed_at.
- `knowledge_review_events`: document_id, reviewer/account, decision, reason, timestamp.
- `knowledge_tags`: controlled tags for exam, stage, paper, subject, topic, geography, scheme, issue and source class.

Raw files should be stored in a controlled data directory or object store, not embedded as huge SQLite blobs. The DB stores checksums and paths. Keep source documents immutable by version.

### 4.2 PYQs, question bank and mocks

- `question_items`: question_id, origin_type (official_pyq, official_sample, curated, ai_generated), source_document_id, exam_id, exam_cycle, exam_stage, paper, year, question_number, question_text, options_json, correct_answer, answer_key_source_id, explanation, language, difficulty, status.
- `question_topic_mappings`: question_id, syllabus_node_id, mapping_confidence, mapping_method, reviewed_at.
- `question_versions`: question_id, version, content_hash, changed_at, change_reason.
- `mock_tests`: mock_id, owner_scope, exam_id, stage, title, mode, duration_minutes, question_count, status, created_at.
- `mock_test_items`: mock_id, question_id, sequence, marks, negative_marks.
- `mock_attempts`: attempt_id, user_id, mock_id, started_at, submitted_at, score, accuracy, time_spent, result_json.
- `mock_responses`: attempt_id, question_id, selected_answer, correctness, time_spent, confidence, review_note.

Official question text and answer keys need source references and permitted-use review. A generated question is labelled AI-generated, has a model/prompt version and supporting knowledge citations, and cannot be promoted to official PYQ.

### 4.3 Personalisation and adaptive learning

- `user_topic_mastery`: user_id, syllabus_node_id, mastery_score, confidence, evidence_count, last_assessed_at, updated_at.
- `user_learning_events`: user_id, event_type, source_id, topic_id, score, duration, confidence, difficulty, occurred_at.
- `revision_items`: user_id, topic_id, last_reviewed_at, next_review_at, interval_days, ease_factor, repetitions, state.
- `adaptive_recommendations`: user_id, recommendation_type, topic_id, evidence_json, rationale, proposed_action, status, created_at, resolved_at.
- `user_learning_preferences`: user_id, language, explanation_depth, question_difficulty, daily_content_preferences, notification_preferences.

Use an explainable baseline such as SM-2-style spaced repetition plus rolling accuracy, recency and confidence. Mastery must combine evidence from tests, answer writing, revision and candidate feedback; study time alone is not mastery. A recommendation is a proposal until accepted or the candidate's settings explicitly permit a bounded automatic adjustment.

### 4.4 Daily and periodical content

- `content_editions`: edition_id, edition_type (daily_gs, weekly_magazine, monthly_magazine), edition_date, period_start, period_end, language, status (draft, review, published, withdrawn), version, created_at, published_at.
- `content_sections`: section_id, edition_id, sequence, gs_paper, title, body_markdown, exam_relevance, syllabus_node_ids_json.
- `content_citations`: section_id, chunk_id/document_id, locator, claim_group.
- `content_questions`: edition_id, question_id, question_type, answer, explanation, source_refs_json.
- `content_feedback`: user_id, edition_id, rating, usefulness_tags, comment, created_at.

Published editions are immutable snapshots. Corrections create a new edition version with a visible correction note.

### 4.5 Jobs and observability

- `pipeline_jobs`: job_id, job_type, idempotency_key, scheduled_for, started_at, completed_at, status, attempts, input_json, output_json, error_summary.
- `pipeline_job_events`: job_id, event_time, level, message, metadata_json.
- `rag_evaluations`: query_id, expected_source_ids, retrieved_source_ids, citation_validity, answer_quality_score, evaluator, evaluated_at.

Do not log API keys, session cookies, raw passwords or unnecessary personal notes.

## 5. Source catalogue and update strategy

### Tier 1 — primary official sources

- UPSC examination notices, syllabus, annual calendar, official PYQ and answer-key publications.
- UPPSC official notices, syllabus, exam calendar, previous question paper and answer-key pages.
- Gazette of India / e-Gazette for rules, amendments and statutory notifications.
- PIB and official ministry/department releases (Environment, Forest and Climate Change; Agriculture; Finance; Science & Technology; Health; Education; Rural Development; External Affairs; Home Affairs, etc.).
- India Budget, Economic Survey, MoSPI, RBI, NITI Aayog, CAG, Election Commission, Parliament/Lok Sabha/Rajya Sabha publications and Supreme Court judgments/orders.
- Uttar Pradesh government departments, UP Budget/Economic Survey, state gazette and official statistical publications.

### Tier 2 — curated context

- Yojana/Kurukshetra and other publications only where access and reuse terms permit.
- Reputable research institutions and international organisations for clearly labelled background.
- Candidate-owned PDFs, notes and books only where the user has rights to upload/process them.

Every source gets an explicit connector, allowed domain list, fetch cadence, last-checked timestamp and failure policy. Do not rely on broad unbounded crawling.

### Daily update pipeline

1. Discover new URLs and changed pages/PDFs using publisher feeds, indexes, sitemap/ETag/Last-Modified where available.
2. Fetch politely with rate limits, retries, backoff and domain allowlists.
3. Store the raw source/version and calculate checksum.
4. Extract text, preserve page and section locations, normalise and detect duplicate content.
5. Classify document type, exam relevance, GS paper and syllabus topics.
6. Validate source trust and extraction quality. Quarantine uncertain, malformed or mirrored content.
7. Create chunks and lexical index; generate embeddings and upsert Qdrant points idempotently.
8. Run extraction/indexing quality checks and record job metrics.
9. Make newly verified material available to retrieval; alert on failures and stale high-priority sources.

A daily run should not imply that every publisher updates daily. The pipeline checks daily, ingests only changed/new items, and reports when no new official documents were published.

### PYQ acquisition and processing

- Discover official UPSC and UPPSC previous-paper and answer-key listings.
- Import year, exam, stage, paper, question number, source URL and source document hash.
- Extract question boundaries and answer options; preserve page locators.
- Validate counts and extraction quality against the original PDF. Keep uncertain parsing in review status.
- Map questions to syllabus nodes using a hybrid classifier and RAG evidence; show mapping confidence and permit correction.
- Store official answer keys separately from model-generated explanations.
- Track year coverage explicitly. Never claim complete PYQ coverage until every claimed paper/year has been checked and reconciled.

## 6. RAG use cases

- Ask a question about a syllabus topic and receive an evidence-backed explanation.
- Compare CSE, IFoS, PCS and ACF/RFO coverage of a shared topic.
- Retrieve official PYQs for a topic, year range or paper.
- Generate notes and revision cards from verified sources.
- Explain current affairs with static background, recent development, constitutional/legal/economic/environmental context and exam linkage.
- Draft mains answer outlines and evaluate submitted answers against a configurable rubric and cited facts.
- Generate topic tests and full-length mocks with answer keys, explanations and difficulty labels.
- Answer "what changed since last update?" from versioned official documents.
- Recommend resources and tasks based on syllabus coverage and the candidate's weak areas.

The RAG prompt must identify source trust and publication dates. It must not treat model knowledge as a substitute for retrieved sources for current or exam-cycle-specific facts.

## 7. Adaptive learning loop

1. Capture study sessions, completed planner tasks, topic confidence, revision events, PYQ attempts, mock attempts and answer feedback.
2. Normalise evidence into account-scoped learning events.
3. Update mastery estimates by syllabus topic, keeping confidence and evidence count visible.
4. Calculate due revisions using spaced repetition; adjust intervals using recall/test results.
5. Identify persistent weak areas, neglected topics, low accuracy, time-management issues and syllabus gaps.
6. Propose next actions with the evidence and expected time cost.
7. Rebalance future planner tasks within the candidate's available study hours; preserve prior plan versions and ask approval for material changes.
8. Evaluate whether recommendations improved later recall/accuracy; down-rank ineffective recommendation patterns.

Do not fine-tune a model on one user's data in the MVP. The first self-learning release is a transparent, deterministic personalisation engine plus RAG feedback, not uncontrolled autonomous model training.

## 8. GS publishing standards

### Daily GS brief

A concise daily edition should include:
- 5–10 selected developments, depending on the news day and relevance.
- What happened (fact summary), why it matters, background/static link, UPSC/UPPSC relevance, GS paper/topic, prelims facts and mains dimensions.
- Primary-source link, publication date and last-verified date.
- A short "what to remember" box and 3–5 original practice questions.
- Explicit labels for facts, analysis and editorial inference.

### Weekly GS magazine

Aggregate the week's verified daily items and add:
- Executive summary and issue tracker.
- GS I–IV and relevant IFoS/Forestry/Environment and UP-specific sections.
- Topic-wise analysis, multi-dimensional mains perspectives, important reports/data, schemes, judgments and international developments.
- PYQ linkage and answer-writing prompts.
- 15–25 original MCQs and 3–5 mains questions with answer frameworks.
- Revision checklist and source bibliography.

### Monthly GS magazine

Provide a deeper, deduplicated month-in-review:
- Theme-wise coverage and trends.
- Major policy, economic, environment, science, social and governance developments.
- Important reports, indices and data with publication-year context.
- Legislation, bills, rules, judgments and constitutional issues.
- Uttar Pradesh-specific section.
- IFoS/ACF/RFO environment, biodiversity, forestry, wildlife and conservation section.
- Prelims fact sheet, mains issue briefs, essay themes and revision test.
- "Carry forward" topics and unresolved developments to monitor next month.

The daily brief is not merely concatenated into a magazine. Weekly/monthly jobs deduplicate, reconcile updates, add context and preserve citations. If a source changes or a claim is corrected, the affected editions are flagged and a corrected version is published.

### Editorial quality gates

- Validate every citation against stored source IDs and locators.
- Verify dates, names, quantities, schemes and legal references against primary sources.
- Detect duplicate stories and contradictory claims.
- Require review for low-trust, politically sensitive, legal, statistical or ambiguous material.
- Mark generated questions as original AI practice.
- Store generation model, prompt template version, retrieved chunks and reviewer actions.
- Do not publish an empty or low-evidence edition merely to satisfy a schedule. Publish a "no major verified updates" status where appropriate.

## 9. API and frontend surface

Proposed authenticated API groups:

- `GET /api/knowledge/search?q=...&exam_id=...&topic_id=...`
- `GET /api/knowledge/documents/{document_id}`
- `GET /api/knowledge/documents/{document_id}/versions`
- `POST /api/ai/ask` — grounded RAG answer with citations.
- `GET /api/questions?exam_id=...&year=...&topic_id=...`
- `POST /api/mocks`, `POST /api/mocks/{id}/attempts`, `POST /api/mocks/{id}/submit`
- `GET /api/learning/insights`, `GET /api/learning/revisions/due`, `POST /api/learning/recommendations/{id}/accept`
- `GET /api/content/daily/{date}`
- `GET /api/content/magazines?period=weekly|monthly`
- `GET /api/content/editions/{edition_id}`
- Admin/operator-only: `GET /api/admin/pipeline/runs`, `POST /api/admin/pipeline/run`, `GET /api/admin/sources`, `PATCH /api/admin/sources/{source_id}`

Frontend pages:
- Knowledge Hub (search, filters, cited answers and source viewer).
- Current Affairs / Daily GS.
- Weekly and Monthly GS magazines with archive and download/export.
- PYQ Explorer (exam/year/stage/paper/topic filters).
- Mock Tests (practice, timed tests, review and analytics).
- Learning Insights (mastery map, due revisions, weak areas and recommended actions).
- Pipeline Health (operator-only source freshness, ingestion failures and review queue).

## 10. Delivery phases and acceptance criteria

### Phase R0 — foundations and source governance
- Add schema/migrations, source registry, document versioning, provenance and audit events.
- Add configuration and health checks for Qdrant and Ollama embeddings.
- Add a local worker container and idempotent job runner.
- Add source allowlists, rate limiting, retries and review states.
- Acceptance: migration preserves existing data; worker starts independently; a test document can be ingested twice without duplicate rows or vector points.

### Phase R1 — first vertical-slice RAG
- Ingest a small verified set: UPSC/UPPSC syllabi, official notifications and a limited set of official PYQ PDFs.
- Implement PDF/HTML extraction, chunking, FTS5 and Qdrant indexing.
- Implement authenticated search and cited RAG answer endpoints.
- Acceptance: answer citations resolve to exact document/page; ungrounded queries return insufficient evidence; user data is isolated; vector index can be rebuilt from metadata/raw documents.

### Phase R2 — official PYQ library and mock engine
- Expand year coverage and extraction validation.
- Map PYQs to syllabus nodes with confidence and review tools.
- Build original AI question generation, mock assembly, attempts, scoring and analytics.
- Acceptance: official and generated questions are always distinguishable; answer keys cite sources; coverage dashboard shows verified years/papers only.

### Phase R3 — adaptive learning and revision
- Capture performance events, topic mastery, confidence and spaced repetition.
- Surface weak areas and due revisions.
- Add explainable adaptive plan recommendations and user approval.
- Acceptance: recommendations cite the user's own evidence; no silent deletion of tasks; historical plans remain intact.

### Phase R4 — daily current affairs and daily GS brief
- Add official-source connectors and daily change detection.
- Classify, deduplicate, verify and create daily GS editions.
- Add citation validation, review queue and archive UI.
- Acceptance: every published item has traceable sources; daily job is idempotent; failed connectors are visible; no unsupported item is published.

### Phase R5 — weekly and monthly GS magazines
- Aggregate daily material, resolve duplicates and updates, generate deeper issue analysis, tests and revision checklist.
- Add archive, edition versioning and export.
- Acceptance: all claims are traceable; corrections are versioned; weekly/monthly content includes exam-specific sections and original practice questions.

### Phase R6 — hardening and hosted scale
- PostgreSQL migration, distributed worker/queue, object storage, backups, tenant isolation, rate limits, monitoring, retention and deployment secrets.
- Add retrieval and content quality evaluation datasets.
- Acceptance: restore drill succeeds; tenant isolation tests pass; ingestion and publication SLOs are measured; provider spend/quotas are observable.

## 11. Quality and security tests

- Auth and account isolation for all knowledge, mocks, learning events and content feedback.
- Source domain allowlist, URL validation and SSRF protection; never fetch arbitrary user-provided internal URLs.
- Malicious document/prompt injection tests: retrieved documents are untrusted data, never system instructions.
- Parser tests for scanned PDFs, malformed files, duplicate pages and extraction failures.
- Idempotency, retry, timeout, partial failure and worker restart tests.
- Citation validity, source freshness, retrieval recall and answer grounding evaluations.
- PYQ extraction count reconciliation and official-vs-generated provenance tests.
- Adaptive learning tests for sparse data, contradictory signals and user override.
- Daily/weekly/monthly edition regeneration and correction/version tests.
- Backup and restore for SQLite, raw documents and Qdrant snapshots.

## 12. Operational defaults and open configuration

- Timezone: `Asia/Kolkata`.
- Daily source discovery: once every 24 hours; source-specific cadence may be slower.
- Daily GS edition: generated after source ingestion and validation; publication time is configurable.
- Weekly magazine: after the weekly period closes; default Sunday evening, configurable.
- Monthly magazine: after month-end source reconciliation; default on the 1st of the following month, configurable.
- Keep a manual "run now" action for the operator and "regenerate draft" for authorised editors.
- Retain raw source versions and published editions according to an explicit storage/retention setting.
- Initial exam scope: UPSC CSE, IFoS, UPPSC PCS and ACF/RFO; initial output language English.
- No paid inference fallback. Embedding and generation providers are independently configurable so local Ollama can be used where hosted free-tier quotas are unavailable.

## 13. First implementation slice

Do not try to build every connector, every PYQ year and every magazine at once. The first end-to-end slice should prove this chain:

**official source registry → one official PDF/page → versioned extraction → chunk + FTS5/vector index → cited RAG answer → one generated original practice question → user feedback stored.**

Once this works with reliable provenance, expand source coverage and schedule daily ingestion. This prevents a large but untrustworthy corpus from becoming the foundation of the product.
