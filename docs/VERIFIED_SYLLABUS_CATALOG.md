# Verified syllabus catalogue — implementation notes

## Purpose

This milestone replaces the planner's assumption that one generic topic list represents four different examinations. It introduces versioned syllabus sources, stage/paper outline nodes, explicit cross-exam relationships and account-scoped optional-subject choices.

The catalogue is a **source-linked outline baseline**, not a complete transcription of every syllabus paragraph. It is deliberately marked incomplete. It must not be used to claim 2028 coverage or to generate a final exam-ready plan until the applicable 2028 notifications and the full syllabus have been verified and imported.

## Seeded source records

| Examination | Source cycle | Source | Trust status |
|---|---:|---|---|
| UPSC CSE | 2026 | [UPSC Examination Notice No. 05/2026-CSE](https://www.upsc.gov.in/sites/default/files/Notif-CSP-2026-Engl-060226Rev.pdf) | Official UPSC publisher |
| UPSC IFoS | 2026 | [Indian Forest Service Examination Rules, Gazette of India](https://egazette.gov.in/WriteReadData/2026/269830.pdf) | Official Gazette publisher |
| UPPSC PCS | 2025 | [Advertisement A-1/E-1/2025 copy](https://cdn-images.prepp.in/public/image/View_Enclosure_UPPSC_Notification_0117f86afb1e60c16a0cb18a0b7c74e3.pdf) | Third-party-hosted copy of the notice; cross-check against UPPSC |
| UPPSC ACF/RFO | 2025 | Same combined notice, including Appendices 3, 5 and 6 | Third-party-hosted copy of the notice; cross-check against UPPSC |

UPPSC's official [Commission portal](https://uppsc.up.nic.in/Home) and its [previous-year question paper index](https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues) are included as the publisher verification route. The seeded PDF is not hosted on the Commission domain, so the record says `official_document_copy_mirrored`, not `official_publisher`.

The 2026 UPSC sources and 2025 UPPSC source are not a substitute for the applicable 2028 notification. Source cycle, publication date, source URL and verification status are stored separately from syllabus nodes.

## Catalogue structure

- `syllabus_sources`: exam, cycle, title, publisher, source URLs, publication date, trust status and notes.
- `syllabus_nodes`: stage, paper, parent node, topic heading, description, sort order and source locator.
- `syllabus_crosswalks`: explicit relationships between nodes, with a rationale. Similar wording alone does not create a crosswalk.
- `optional_subject_catalog`: source-cycle list of selectable optional subjects.
- `optional_subject_conflicts`: prohibited combinations represented as data.
- `candidate_optional_subjects`: private selections per account and examination.

## Exam-specific handling

### UPSC CSE
- Preliminary GS Paper I and qualifying GS Paper II are represented separately.
- Mains Essay, GS I–IV, optional subject papers, qualifying language papers and interview are represented as distinct nodes.
- Candidate selects one optional subject. Sociology is included in the optional catalogue.
- Literature optionals are represented by individual language choices.

### UPSC IFoS
- Preliminary screening is explicitly mapped to the Civil Services Preliminary Examination.
- Mains General English and General Knowledge are separate from the two optional subjects.
- Candidate selects two optional subjects from the 14 listed in the 2026 Gazette rules.
- Prohibited subject combinations are enforced server-side.

### UPPSC PCS
- Preliminary GS I and GS II are separate.
- Mains General Hindi, Essay and GS I–VI are separate.
- PCS does not use an optional-subject selection in this 2025 scheme.

### UPPSC ACF/RFO
- The 2025 notice's common preliminary syllabus is cross-linked to the PCS preliminary syllabus.
- Mains General Hindi/Essay, two General Studies papers and two optional subjects (two papers per subject) are represented.
- Candidate selects two optional subjects from the seeded 2025 list; prohibited combinations are checked server-side.
- Optional subject choices are not inferred from the user's degree or presumed eligibility.

## Explicit crosswalks

Only source-backed relationships are seeded:
- IFoS screening uses the Civil Services Preliminary Examination, including the qualifying CSAT paper.
- UPPSC 2025 Appendix 3 is the common preliminary syllabus for PCS and ACF/RFO.

These relationships mean the candidate can share study preparation for that component. They do not mean every topic, exam weighting, paper format or later-stage requirement is identical.

## API

All endpoints require an authenticated session.

- `GET /api/syllabus/catalog?exam_id=upsc_cse&cycle_year=2026&stage=preliminary`
- `GET /api/syllabus/optional-subjects?exam_id=upsc_cse`
- `PUT /api/syllabus/optional-subjects` with `{"exam_id":"upsc_cse","subjects":["sociology"]}`
- IFoS and ACF/RFO require exactly two distinct optional subjects; CSE requires exactly one.
- Unknown subjects and prohibited pairs are rejected.

The frontend browser is at `/syllabus`. It exposes the source-cycle warning, source-document links, stage filters and optional-subject selector. The syllabus navigation in the planner links to this page.

## Limitations and next work

1. Obtain and verify the 2028 CSE, IFoS, PCS and ACF/RFO notifications when published.
2. Verify the UPPSC 2025 PDF against a Commission-hosted copy before treating its syllabus as authoritative.
3. Transcribe all syllabus subclauses into atomic topic nodes and capture exact appendix/section/page references.
4. Import full Forestry and Geology syllabi separately for IFoS and ACF/RFO; do not assume the wording or coverage is interchangeable.
5. Add the complete CSE optional-subject syllabus tree and the remaining optional-subject topic trees as needed.
6. Add official resource records and PYQ links with source, publication year and syllabus-node mappings.
7. Add user-facing syllabus completion evidence and progress tracking.
8. Update the plan engine to schedule only the candidate's selected optional subjects and verified syllabus nodes. The current deterministic starter-topic plan remains provisional and is not yet replaced by this catalogue.

## Safety of planning data

This phase does not automatically rewrite existing plan tasks or mark any syllabus as completed. Existing plan history is preserved. Source records are seeded idempotently. A new official source cycle should be added as a new version, not silently overwrite a prior cycle.
