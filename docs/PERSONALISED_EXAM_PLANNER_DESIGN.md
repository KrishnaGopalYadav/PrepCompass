# Personalised Exam Planner — Product and Technical Design

**Status:** Product direction approved; implementation follows in planner milestones  
**Target platform:** Local-first web application initially, with a shared planning model reusable by Android, iPhone, iPad and macOS clients.

## 1. Product objective

The planner turns a candidate's exam goals into an actionable, date-aware preparation programme. It must do more than display a calendar: it creates a day-by-day plan, explains what to study and why, points to suitable resources, records actual work, measures progress against the plan and adapts future work when the candidate falls behind or moves faster than expected.

The plan belongs to the signed-in user. It must be editable, transparent and recoverable; the candidate remains in control of changes.

## 2. Candidate journey

1. **Choose examinations.** Select one or more exams (for example UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO).
2. **Choose attempt targets.** Set an attempt year for each selected exam. Support separate years where the candidate is targeting different cycles.
3. **Set the preparation window.** Choose the date to start, or confirm today's date, and enter known exam dates when officially announced. If the official date is not known, the plan uses a clearly labelled provisional target window rather than pretending the date is confirmed.
4. **Build a preparation profile.** Capture study hours by weekday, preferred time slots, days off, language/medium, current level, completed syllabus, strengths and weak areas, optional subjects, and resource preferences.
5. **Review the plan proposal.** Show syllabus coverage, phases, weekly workload, milestones, revision cycles and assumptions before generating the daily schedule.
6. **Follow the daily plan.** Each day contains prioritised tasks, estimated duration, exam/subject/topic mapping, instructions, resources and a clear completion action.
7. **Record actual work.** Start a timer or log actual duration, completion, confidence, notes and optional evidence such as test score.
8. **Review and adapt.** Compare planned versus actual work; reschedule incomplete tasks, revise workload and regenerate future days without erasing history.

## 3. Planner setup information

### Required inputs
- One or more examinations and an attempt year for each.
- Preparation start date.
- Available study time (hours/minutes per day, with weekday-specific availability).
- Study medium/language.
- At least one selected syllabus/subject set.

### Optional but valuable inputs
- Target exam date if published; otherwise a provisional target date/window.
- Weekly rest day and unavailable dates.
- Current preparation level and diagnostic test results.
- Previously completed topics and revision status.
- Optional subjects and language papers, where applicable.
- Preferred resources (official PDFs, standard books, videos, question banks, newspapers).
- Target score or performance goals, if meaningful for that exam.
- Existing study sessions imported from the user's account.

Do not force candidates to fill every optional field before they can preview a draft plan. Clearly identify assumptions and allow editing later.

## 4. Multi-exam and shared-syllabus model

A user can prepare for multiple examinations in one integrated plan. The syllabus catalogue must represent:
- Exam → exam cycle/year → stage/paper → subject → topic → subtopic.
- Topic learning outcomes, estimated effort, priority/weighting (only when supported by evidence), prerequisites and revision requirements.
- Shared topic mappings across exams, with exam-specific coverage notes and depth requirements.

A shared topic such as Indian Polity can be studied once in a common learning task, but its completion must update each mapped exam's coverage only to the extent that the topic actually satisfies that exam's requirements. A topic must not be marked complete for every exam merely because its name is similar.

Exam-specific differences remain explicit. CSE, IFoS, PCS and ACF/RFO have different stages, papers, optional/technical requirements and notification rules. UPPSC PCS optional-subject requirements must not be inferred from another exam. IFoS and ACF/RFO subject choices and degree eligibility must be validated against the applicable official notification.

## 5. Plan structure and daily schedule

The generated plan is organised in layers:

- **Overall roadmap:** start date, target attempts, estimated available hours, milestones and risk/assumption notes.
- **Preparation phases:** foundation, syllabus completion, consolidation, prelims-focused practice, mains/subject-specific practice, mock tests and final revision. The exact phases depend on the selected exam and its verified stages.
- **Weekly plans:** outcomes, topic coverage, practice/revision allocation and weekly review.
- **Daily plan:** ordered tasks that fit the candidate's available time.

Each daily task should contain:
- Planned date and order/priority.
- Exam(s), stage/paper, subject and syllabus topic references.
- Task type: learn, read, notes, active recall, answer writing, MCQ practice, revision, mock/test, analysis or current affairs.
- Specific instruction and measurable expected outcome.
- Estimated minutes and optional time slot.
- Resource references with title, type, publisher/author, edition or publication date, URL/file reference and why it is recommended.
- Status: planned, in progress, completed, partially completed, skipped or rescheduled.
- Actual minutes, completion timestamp, confidence/difficulty feedback and notes.

Daily scheduled minutes must never exceed the candidate's stated availability unless the user explicitly approves an overload. Include buffer/recovery capacity and avoid filling every available minute by default.

## 6. Resource recommendation rules

Resources are attached to syllabus topics and tasks, not presented as an unstructured list.

Prioritise:
1. Official exam notifications, syllabus PDFs, previous-year question papers and government sources.
2. Candidate-selected standard books and trusted reference material.
3. Curated learning material mapped to a specific topic.
4. Current-affairs resources with publication dates and source links.

For each resource store its source, title, type, topic mapping, publication/edition date, language, access method and last-verified date. Distinguish free, paid, user-owned and external resources. Do not fabricate titles, editions, links or claims that a resource is official. Flag resources that may be outdated and allow the user to replace or hide recommendations.

The system should explain the task-resource match (for example, syllabus coverage, language preference or question-paper relevance). Resource recommendations should be versioned so that a plan remains auditable if a link or edition changes.

## 7. Progress validation and plan adaptation

The planner validates progress using more than a binary checkbox.

### Completion signals
- Planned minutes versus actual minutes.
- Task completion status.
- Syllabus coverage and topic mastery.
- Revision due/completed state.
- MCQ accuracy, mock scores and answer-writing rubric results when recorded.
- Candidate confidence and self-reported difficulty.
- Consistency: planned study days versus actual study days.

### Dashboard measures
- Today's planned versus completed tasks and minutes.
- Weekly planned versus actual hours.
- Syllabus coverage by exam, stage, subject and topic.
- On-time task completion and overdue workload.
- Revision adherence and topics due for revision.
- Test performance trends and weak areas.
- Forecast risk: whether the current pace is likely to complete required work before the target attempt.

### Replanning rules
- A missed task is not silently deleted. It remains in history and can be rescheduled, reduced, split or deliberately skipped.
- At daily/weekly review, calculate the remaining workload against remaining available days and hours.
- Prioritise prerequisite topics, high-importance syllabus areas, spaced revision and exam-specific deadlines.
- If the workload no longer fits, show the trade-off and ask the user to approve a changed plan (reduce scope, increase hours, move milestones or change attempt target).
- Preserve completed work and historical plan versions. Replanning creates a new version with a reason and timestamp.
- Do not claim a candidate is exam-ready based only on hours or checkboxes; readiness requires topic mastery and relevant practice/test evidence.

## 8. Suggested planning engine

Start with a transparent, deterministic planning engine; AI may assist with explanations and suggestions but must not be the sole source of scheduling truth.

1. Validate selected exam cycles, official syllabus versions and prerequisites.
2. Build a unified topic graph with explicit cross-exam mappings.
3. Estimate total work from topic effort, candidate baseline and task-type allocations.
4. Calculate available capacity from the user's weekly calendar, holidays and target windows.
5. Allocate work by dependency, exam priority, stage deadline and candidate weakness.
6. Insert active recall and spaced revision checkpoints after learning tasks.
7. Schedule question practice, previous-year questions and mocks at suitable milestones.
8. Add buffer capacity and weekly review tasks.
9. Check all daily/weekly capacity constraints and flag infeasible plans.
10. Save a versioned plan and generate readable daily tasks.

AI-assisted functions may propose task decomposition, explain resource choices and suggest adjustments. The system must validate AI proposals against syllabus IDs, available time, resource catalogue and plan constraints before saving them.

## 9. Core data model (proposed)

All candidate-owned records are scoped by user_id.

- exam_catalog: stable exam identifiers and administering body.
- exam_cycles: year, stage dates, notification reference, date confidence/status and source verification.
- syllabus_versions: exam cycle, version, official source and effective date.
- syllabus_nodes: hierarchical subjects/topics/subtopics and learning outcomes.
- topic_exam_mappings: explicit shared-topic relationships and exam-specific depth/coverage notes.
- candidate_exam_targets: user, exam cycle, attempt year, target priority and selected stages.
- candidate_profiles: medium, availability, preferences and baseline.
- availability_rules / unavailable_dates: recurring weekly capacity and exceptions.
- resources / resource_topic_mappings: verified source catalogue and syllabus links.
- study_plans / study_plan_versions: user-owned plan, version, dates, status and generation assumptions.
- plan_tasks: daily tasks, topic mappings, estimates, resource links, status and actual effort.
- task_activity: immutable completion, partial completion, skip and reschedule events.
- topic_mastery: user assessment evidence and confidence over time.
- revision_events: spaced-revision schedule and completion.
- plan_reviews: weekly metrics, risks, decisions and approved changes.

Foreign keys, indexes and user-scoped access checks are required. The current SQLite implementation is suitable for a single-device/local-first deployment; a multi-device sync or hosted multi-user service will require a deliberate sync architecture and likely PostgreSQL.

## 10. User experience / screens

1. **Planner entry:** Create a preparation plan with saved plans and active attempt targets.
2. **Exam selection:** multi-select exams, separate attempt year and priority per exam.
3. **Availability and profile:** weekly hours, days off, medium, baseline and optional subjects.
4. **Plan preview:** phases, milestones, hours/week, syllabus coverage and assumptions; edit before confirmation.
5. **Daily planner:** today's tasks, estimated time, resources, timer, completion and carry-forward.
6. **Calendar:** day/week/month views, exam milestones and revision dates.
7. **Syllabus tracker:** topic-level progress and mastery per exam, with shared-topic handling.
8. **Progress review:** planned vs actual, weak areas, overdue work, forecast and suggested changes.
9. **Plan history:** versions, reschedule reasons and audit trail.

## 11. Delivery roadmap

### Planner A — foundation and setup
- Add exam catalogue, exam cycles and versioned syllabus data model.
- Add candidate exam targets, attempt year, preparation start date and availability profile.
- Build planner onboarding and plan preview.
- Seed only verified exam/syllabus records with source references.

### Planner B — plan generation
- Build topic graph and cross-exam mapping.
- Implement deterministic workload estimation and daily/weekly allocation.
- Add phases, milestones, revision spacing, practice and buffer capacity.
- Validate capacity and surface infeasible plans.

### Planner C — daily execution
- Daily/weekly/monthly planner UI.
- Task status, timer/logging, resources and carry-forward workflow.
- Link actual study sessions to plan tasks without duplicating effort.

### Planner D — validation and adaptive replanning
- Planned-vs-actual analytics and syllabus progress.
- Topic mastery evidence, revision adherence and mock/test results.
- Weekly review and versioned, user-approved replanning.

### Planner E — intelligence and portability
- Optional AI assistance with deterministic validation.
- Export/import plan and progress snapshots.
- Backup/restore and portable data model for future web, Android, iOS/iPadOS and macOS clients.

## 12. Acceptance criteria

- A candidate can select multiple exams and set an independent attempt year for each.
- A candidate can set a preparation start date and realistic weekly availability.
- A preview shows phases, weekly load, daily task examples, milestones, assumptions and resource sources.
- Generated tasks respect daily availability and explicitly flag an infeasible target.
- Every task maps to one or more syllabus nodes and includes a measurable outcome.
- Shared topics are mapped explicitly and do not falsely complete exam-specific requirements.
- A user can record partial/completed/skipped work and actual time.
- The system reports planned versus actual progress by date, exam and topic.
- Missed tasks remain in history; approved replanning creates a new plan version.
- User A cannot read or modify User B's targets, plans, tasks, resources or progress.
- Exam dates, eligibility and syllabus claims are traceable to the applicable official notification/source and show whether they are confirmed or provisional.

## 13. Initial profile to support during product development

The first planning profile should support an integrated 2028 target for UPSC CSE, UPSC IFoS, UPPSC PCS and UPPSC ACF/RFO, English medium and approximately 2–3 hours of study per day. Optional subjects are candidate-editable and must be validated against the relevant exam-year notification. Do not hard-code this profile as a universal default for all users.
