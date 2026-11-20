# Curated data catalogues

- `gs_topic_taxonomy.json` is a starter cross-exam topic taxonomy. It is deliberately labelled as a non-official syllabus crosswalk.
- Runtime source and PYQ discovery records are seeded by `backend/app/resource_catalog.py` into SQLite.
- Do not store downloaded textbooks, coaching PDFs, user uploads, private study data or credentials in this directory.
- Every acquired source must retain publisher, canonical URL, retrieval time, checksum, document version, licence/usage note and review state.
- Every PYQ must retain exam, cycle, stage, paper, language, question number, source locator, source checksum and answer-key status.
- AI-generated practice questions must remain a separate origin/type from official PYQs.
