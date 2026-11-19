# PrepCompass Agentic Study Coach — Product and Engineering Design

## Product goal

Turn PrepCompass into a user-specific, evidence-grounded exam preparation coach for UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO. The coach observes the learner's plan, study logs, syllabus coverage, test responses and time availability; diagnoses progress; creates the next weekly plan; and publishes a personalised GS magazine.

This document defines the target architecture. It is not a claim that an autonomous LLM agent, live web ingestion, five-year PYQ analysis or generated magazine is already operational.

## Agent responsibilities

1. Exam intelligence agent: maintains cycle-specific stages, papers, marks, duration, negative marking and optional subject rules from official notifications. Every fact has source, source date and verification status.
2. PYQ analysis agent: indexes the last five available years of official papers by exam, year, stage, paper, question, syllabus node, theme, question format and difficulty. It computes trends only from parsed and reviewed records. A paper link is not evidence that its questions were parsed.
3. Current-affairs research agent: collects primary sources and permitted public coaching analysis (official sites, RSS, openly accessible pages, licensed feeds/uploads). It stores metadata and concise notes with source URLs; it does not scrape paywalled content, bypass access controls, or reproduce proprietary magazine text.
4. Assessment designer: creates a weekly test in the selected exam's actual paper format. It can include licensed/attributed PYQs and newly authored questions inspired by high-level patterns. Every item is labelled PYQ or original AI, with provenance.
5. Evaluator: scores objective items deterministically; evaluates descriptive answers using a rubric and AI feedback, with uncertainty labels and human review. It must not claim UPSC examiner equivalence.
6. Learner analyst: combines accuracy, negative marks, time per question, attempt rate, answer quality, topic coverage, revision age and study consistency.
7. Weekly GS magazine editor: creates a personalised digest based on exam targets, weak areas, syllabus, PYQ trends and dated sources. Every claim has source links and publication dates.
8. Planning agent: proposes next-week tasks based on available hours, attempt dates, syllabus gaps, revision due dates and test diagnoses. It does not silently overwrite plans.

## User-specific weekly loop

Capture study sessions, syllabus progress and mock responses continuously. On a configurable review day, aggregate the preceding seven days, generate an exam-specific test blueprint, evaluate the attempt, update topic mastery with confidence/sample size, publish the weekly GS magazine and propose next-week tasks. The user can accept or edit the proposed plan. Keep dated history of tests, agent decisions, source snapshots and plan versions.

## Exam-format profiles

Do not use one generic quiz for every exam. Each profile is versioned by notification cycle and includes stage, paper, subject/optional, question types, question count, marks, duration, section structure, negative marking, descriptive word limits, medium and official source. The selected profile drives mock composition. If the scheme for the target attempt year is not verified, show a warning rather than inventing a format.

## Five-year PYQ analysis

Build a source inventory first, then ingest actual papers. Primary sources:
- UPSC current index: https://www.upsc.gov.in/examinations/previous-question-papers
- UPSC archive: https://www.upsc.gov.in/examinations/previous-question-papers/archives
- UPPSC previous papers: https://uppsc.up.nic.in/OuterPages/PreQuesPapers.aspx?ID=PrevQues

UPSC's index/archive exposes recent CSE and IFoS papers, including Forestry and Geology. Availability differs by exam and paper. For every paper record exact title, year, paper, URL, retrieval date, checksum, parser status and coverage. Report the rolling five-year window as available years / target years; never fabricate absent years. Extract only legally accessible content and preserve provenance.

Analysis outputs: topic frequency, recurrence by year, trend direction, question archetypes, difficulty/cognitive demand with confidence, current-affairs linkage and marks distribution from official scheme. AI tags require confidence and human review/correction.

## Coaching magazines and current affairs

Potential public sources to assess for access terms and licensing include Vision IAS, Insights IAS, ForumIAS and Drishti IAS. Register access mode (public page, RSS, licensed feed, user upload or metadata only) and review terms. Do not assume a PDF is licensed for ingestion merely because it is downloadable. Prefer primary sources: PIB, PRS India, ministries, RBI, courts, Parliament, statutory bodies, MoEFCC, FSI, GSI, IMD, CPCB, ISRO and Uttar Pradesh government departments.

Magazine sections: weekly executive brief; dated current-affairs items; exam relevance and syllabus mapping; prelims facts and traps; mains background, constitutional/legal/economic/social/environmental dimensions, arguments, data, challenges and way forward; IFoS/ACF-RFO forestry, biodiversity, climate, protected areas, forest policy, geology and disaster-risk section; UP-specific governance, economy, geography, schemes and environment; weak-area spotlight; original practice questions with explanations; answer-writing prompts and revision checklist. Do not copy coaching paragraphs; independently summarise with citations.

## Bounded agent architecture

Use a bounded workflow/state machine, not an unconstrained autonomous agent. Each run stores run ID, user, trigger, input snapshot, tool calls, source citations, provider/model, prompt version, output, token/cost metadata, status and error. Require schema-validated outputs. Apply per-user rate limits and budget caps. Cache research by source/date. User can inspect citations and reject/edit plan proposals.

Provider settings are server-side only: AI_PROVIDER, AI_MODEL, AI_API_BASE and AI_API_KEY. Without a configured provider, deterministic analytics and transparent templates remain available; do not claim AI evaluation or live research. Never expose keys to the frontend or logs.

## Target data model

exam_pattern_versions; paper_sources; paper_documents; paper_questions; syllabus_question_tags; topic_trend_snapshots; current_affairs_sources; current_affairs_items; magazine_issues; magazine_citations; assessment_blueprints; mock_tests; mock_questions; mock_responses; descriptive_submissions; evaluation_rubrics; evaluations; learner_topic_mastery; weekly_diagnostics; agent_runs; agent_decisions; plan_proposals. Every learner-owned row includes user_id; global source/question data is separate from private attempts and analytics.

## Acceptance criteria

1. User selects exam, attempt year, paper and optional subject; only valid profiles are selectable.
2. Dashboard reports PYQ coverage by year/paper and never claims five-year analysis with fewer years.
3. Weekly mock follows selected official profile and has a reproducible blueprint.
4. PYQs and original AI questions are visibly distinguished.
5. Objective scoring is deterministic and tested, including negative marking.
6. Descriptive evaluation uses paper-specific rubrics, criterion feedback and uncertainty labels.
7. Weekly analysis shows trends, strengths, weaknesses, time management and sample size.
8. Magazine claims have dated citations and syllabus mapping.
9. Proposed plans account for available hours and require user approval.
10. Personal tests, answers, evaluations and recommendations are isolated by user.
11. Provider-offline mode works and states its limitations.
12. Tests cover scoring, profiles, isolation, output validation and partial PYQ coverage.

## Delivery phases

A. Verified exam-pattern registry and five-year paper inventory.
B. PYQ document ingestion, OCR/parser, question tagging and review UI.
C. Mock blueprint generator and exam-format test runner.
D. Objective/descriptive evaluation and learner analytics.
E. Current-affairs source registry and personalised weekly GS magazine.
F. Bounded agent orchestration and adaptive weekly plan proposals.
G. Monitoring, audit trail, privacy, cost controls and export/backup.

Do not represent the entire target as complete until each phase has tests and source coverage evidence.
