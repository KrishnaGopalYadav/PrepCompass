# Stage 2 — Content and Data Foundation

**Scope:** source registry, PYQ discovery catalogue, topic taxonomy, acquisition rules and provenance model.  
**Initial exams:** UPSC CSE, UPSC IFoS, UPPSC PCS, UPPSC ACF/RFO.  
**Initial medium:** English, with Hindi-ready metadata design.

## 1. What is included now

The runtime catalogue is seeded into SQLite by `backend/app/resource_catalog.py` and exposed through authenticated APIs:

- `GET /api/resources/sources` — list curated source records; optional `source_type` and `exam_id`.
- `GET /api/resources/pyqs` — list exam/stage collection records; optional `exam_id` and `stage`.

The catalogue intentionally stores source metadata and links. It does not claim to have downloaded, OCR'd, verified or question-tagged every paper.

## 2. Official PYQ discovery starting points

| Exam / collection | Official portal | Coverage notes |
|---|---|---|
| UPSC CSE Prelims | [UPSC current papers](https://www.upsc.gov.in/exam-documents/question-papers/) and [archives](https://www.upsc.gov.in/examinations/previous-question-papers/archives) | GS-I and GS-II/CSAT; verify each year and paper link |
| UPSC CSE Mains | Same UPSC portal and archive | Essay, GS I–IV, language and optional papers; availability varies |
| IFoS Prelims | UPSC CSE Preliminary papers | Common screening paper; avoid duplicate assets and preserve cross-exam mapping |
| IFoS Mains | UPSC portal and archive | General English, General Knowledge and optional subject papers; discover each paper dynamically |
| UPPSC PCS Prelims | [UPPSC previous papers](https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues) | Portal offers exam, year, paper and series filters |
| UPPSC PCS Mains | Same UPPSC portal | Includes Hindi, Essay and GS papers; attachment visibility may expire |
| UPPSC ACF/RFO | Same UPPSC portal | Filter by exact recruitment/exam/year; preserve ACF/RFO and optional-paper distinctions |

Observed UPPSC years in the portal at catalogue preparation include 2025, 2024, 2023, 2021, 2020, 2018 and 2017. These are years shown by the portal, not proof that every paper for every exam exists for every year. Some entries have a visible-until date. The connector must discover current links rather than construct guessed PDF URLs.

UPSC current and archive portals contain paper listings across examinations. The archive includes CSE Mains GS and Essay papers for historical cycles. The official portal should be queried at ingestion time; do not freeze a claimed complete range into the product.

## 3. Source hierarchy and recommended resource universe

### Tier 1 — exam authorities and primary government sources

- UPSC: examination notices, rules, syllabus, question papers, answer keys, cut-offs and results.
- UPPSC: advertisements, corrigenda, syllabus, previous papers, answer keys and results.
- Gazette of India: statutory rules, notifications and amendments.
- PIB and originating Union ministries: scheme announcements, policy releases and annual reports.
- MoEFCC and Forest Survey of India: forest, biodiversity, climate and environmental material; include India State of Forest Report 2023 and subsequent official editions when released.
- India Budget and Economic Survey: budget speech, expenditure/receipts, outcome documents and annual macroeconomic analysis.
- MoSPI and data.gov.in: official statistics and open datasets, subject to dataset licence and metadata.
- RBI: annual reports, monetary policy, financial stability, state finances and Database on Indian Economy.
- NITI Aayog: reports, indices, policy and SDG material.
- India Code, Supreme Court, Parliament/Digital Sansad and CAG: legislation, judgments, debates, committee and audit reports.
- Government of Uttar Pradesh and UP Budget: state policies, budget, department reports and state-specific data.
- IMD, ISRO, Agriculture Ministry and MHA/MEA: technical and subject-specific primary information.

### Tier 2 — education and research references

- NCERT textbook catalogue and ePathshala: use links and permitted user access. NCERT's copyright notice explicitly prohibits republishing its textbooks or packaging them inside a digital content service; do not bundle the textbook PDFs.
- ICFRE research/publication portals and other public research institutions: record the publisher and document-specific usage rights.
- University and public research repositories: only ingest items whose licence/permission allows it.

### Tier 3 — secondary analysis

- PRS Legislative Research: useful bill summaries, legislative briefs and monthly policy review. Label it independent secondary analysis; cross-check legal status and primary facts against Parliament, Gazette or India Code.
- Reputable newspapers and journals may be registered as secondary current-affairs sources if their terms permit the intended use. Never use them as the sole authority for legal/statistical claims.

## 4. Required metadata for each source

| Field | Purpose |
|---|---|
| source_id | Stable internal identifier |
| title / publisher | Human-readable source and issuing authority |
| source_type | Exam authority, Gazette, ministry, dataset, report, textbook catalogue, secondary analysis |
| canonical_url / landing_url | Stable discovery and source page |
| authority_level | official, secondary, research, user-provided |
| exam_scope | CSE, IFoS, PCS, ACF/RFO and GS/subject tags |
| check_frequency | Suggested discovery cadence, not a guarantee |
| publication_date | Publisher's date, when available |
| retrieved_at | UTC timestamp of successful fetch |
| content_hash | SHA-256 for exact-byte change detection |
| mime_type / file_size | Safe parser selection and limits |
| language | en, hi, bilingual, etc. |
| licence / usage_notes | Allowed use, attribution and restrictions |
| verification_status | discovered, fetched, checksum_verified, parsed, reviewed, rejected |
| document_version | Preserve changed versions; do not overwrite historical source |
| locator | Page, section, paragraph, table, question number |
| supersedes / related_source | Corrigenda and revised editions |

## 5. PYQ data model (next acquisition step)

Do not store a question as plain text without its provenance. A question record should include:

- `question_id`, `exam_id`, `cycle_year`, `stage`, `paper_code`, `paper_title`, `language`, `question_number`, `series` (where applicable).
- `source_id`, `document_id`, `page_number`, `source_locator`, `content_hash`.
- `question_text`, `options_json`, `question_type`, `marks`, `negative_marks` only when explicitly supported by the relevant exam rules/paper.
- `answer_key_id`, `answer_status` (not_available, provisional, official, corrected), `answer_source_locator`.
- `topic_ids`, `subtopic_ids`, `difficulty` and `tagging_status` (untagged, machine_suggested, reviewed).
- `record_origin` (official_paper, official_answer_key, user_upload, licensed_partner, generated_practice).
- `reviewed_by`, `reviewed_at`, `created_at`, `updated_at`.

Question text copied from an official public paper should still retain the issuing authority and document provenance. AI-generated practice must have `record_origin=generated_practice` and must never be mixed into official PYQ filters.

## 6. Ingestion workflow and gates

1. Discover source page/feed from an allowlisted source registry.
2. Fetch politely with timeouts, bounded response size, user-agent, retries with exponential backoff and host-specific rate limits.
3. Record HTTP status, redirect chain, retrieval timestamp and final URL.
4. Validate content type, file size, checksum and document identity.
5. Compare checksum/canonical URL with prior versions; create a new version on change.
6. Parse PDF/HTML while preserving page/section locators. OCR only scanned pages; store OCR confidence and retain page images where permitted.
7. Detect duplicate documents using SHA-256 and secondary similarity; do not merge distinct exam cycles or paper series solely because text matches.
8. Extract questions into a staging table; do not publish unreviewed OCR.
9. Attach official answer keys only when the issuing authority publishes them; record provisional/corrected status and answer-key version.
10. Map questions to syllabus taxonomy using machine suggestions plus review. Preserve multi-topic tags and confidence.
11. Publish only after validation; keep rejected/needs-review states visible to maintainers.
12. Index approved chunks/questions into lexical and vector search. Indexes are rebuildable; source documents and metadata remain the authority.

## 7. Copyright, access and privacy policy

- Publicly reachable does not mean public domain or permission to redistribute.
- NCERT's textbook notice prohibits republishing/redistribution and inclusion in digital content packages. Store catalogue metadata and official links, not copies of textbook PDFs.
- Do not scrape paywalled coaching material, proprietary test series, newspapers or magazines without explicit rights.
- For third-party resources, store bibliographic metadata, permitted links and user-authorised uploads; enforce per-user access controls.
- Follow website terms, robots policies and reasonable request rates. Prefer official bulk downloads, feeds and open-data APIs.
- Do not commit user uploads, private study records, credentials or raw personal data into Git.
- Retain deletion/retention policies and provenance for user-uploaded material.

## 8. Content domains to cover

### Shared GS foundation
- History and culture; geography; polity and constitution; governance; economy; social justice; international relations; science and technology; environment and ecology; disaster management; internal security; ethics; essay; current affairs.
- Prelims facts and concepts should be cross-linked to Mains analytical themes, but paper/stage remains explicit.

### Uttar Pradesh-specific layer
- Uttar Pradesh history, culture, geography, rivers, agriculture, irrigation, industry, infrastructure, urbanisation, demographics, social sector, state schemes, budget, economy, governance, local bodies, environment, protected areas and disaster risks.
- Maintain UP-specific source IDs and data periods; do not infer UP facts from all-India aggregates.

### IFoS / ACF-RFO specialist layer
- Silviculture, forest ecology, forest management, mensuration, forest soils, watershed, agroforestry, social forestry, forest protection, forest economics, wildlife biology, biodiversity, conservation, forest policy and legislation.
- Geology, botany, agriculture and other optionals must be exam-notification-specific. IFoS and ACF/RFO optionals are not interchangeable without verification.

## 9. Quality checks before content enters RAG or publication

- Source authority and publication date visible.
- Source URL resolves and matches claimed publisher.
- Cycle, exam, stage and paper correctly assigned.
- Document hash and version recorded.
- PDF extraction coverage and OCR confidence measured.
- Tables, maps, equations and footnotes not silently dropped.
- No unsupported answer-key claim.
- No duplicate question with conflicting series/year.
- Topic mapping includes confidence and review state.
- Generated factual summaries have citations to approved source chunks.
- Conflicts and stale data are flagged; no silent overwrite.
- Human review for high-impact legal, constitutional, economic and exam-rule updates.

## 10. First content-acquisition backlog

| Priority | Collection | Initial action |
|---|---|---|
| P0 | UPSC CSE Prelims and Mains PYQs | Enumerate official paper links by year/paper; acquire and verify source metadata |
| P0 | UPPSC PCS Prelims and Mains PYQs | Use official filters; capture expiry dates and attachment IDs |
| P0 | UPSC IFoS Mains | Enumerate English, GK and optional papers; do not infer missing years |
| P0 | UPSC / UPPSC notices and syllabus | Store current-cycle notice, corrigenda and versioned syllabus |
| P1 | India Budget, Economic Survey, RBI, MoSPI | Create annual/periodic edition records and dataset series metadata |
| P1 | PIB, ministries, Gazette, Parliament, India Code, Supreme Court, CAG | Daily/weekly discovery and event/entity tagging |
| P1 | FSI ISFR, MoEFCC, ICFRE | Forestry and environment reference catalogue |
| P1 | UP Budget, UP government departments and statistics | UPPCS-specific state knowledge base |
| P2 | NCERT catalogue, ePathshala | Topic-to-book/chapter references and official links only |
| P2 | PRS and permitted secondary analysis | Secondary context with source-type labels and primary-source cross-checks |

## 11. APIs delivered by this PR

### `GET /api/resources/sources`

Authenticated. Optional query parameters: `source_type`, `exam_id`. Returns source metadata and `catalogue_status=curated_discovery_registry`.

### `GET /api/resources/pyqs`

Authenticated. Optional query parameters: `exam_id`, `stage`. Returns collection landing URLs, archive URLs, observed years and explicit coverage caveats. `catalogue_status=discovery_only`.

These APIs are not a downloader and do not claim that every listed paper has been acquired. A future ingestion worker must add retrieval logs, versions and document status before claiming acquisition.

## 12. Acceptance criteria

- Registry seeds idempotently without deleting user data.
- Sources are grouped by authority and type, with official vs secondary clearly labelled.
- PYQ collections distinguish exam, stage and cycle and carry caveats.
- Auth is required; invalid exam/stage filters return 422.
- Official and secondary sources remain distinct.
- No copyrighted textbook or coaching content is copied into the repository.
- No AI-generated question can be mistaken for an official PYQ.
