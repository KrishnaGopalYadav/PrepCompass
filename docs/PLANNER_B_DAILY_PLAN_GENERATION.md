# Planner B — Rolling Daily Plan Generation

## Delivered

- Deterministic Python planning module: `backend/app/planner_engine.py`.
- Authenticated generation endpoint: `POST /api/planner/generate` (7–56 day horizon; UI currently requests 28).
- Authenticated plan read endpoint: `GET /api/planner/plan`.
- Account-scoped task progress endpoint: `PATCH /api/planner/tasks/{task_id}`.
- SQLite persistence for versioned plans and daily tasks.
- Responsive daily-plan page at `/planner/daily`, linked from the saved planner profile.
- Test coverage for generation constraints, progress updates and account isolation.

## Planning rules in this milestone

1. The planner uses the saved start date, daily hours and selected weekdays.
2. It reserves 15% of the declared daily time as a recovery/buffer margin.
3. It schedules up to three blocks on each selected study day: learning, active recall and practice, reinforcing one topic on that day.
4. The generated plan is a rolling window (28 days by default) and regeneration creates a new version; the previous active version becomes superseded.
5. Tasks carry the selected exam context and a provisional topic identifier. This is not a claim that every topic satisfies every selected exam syllabus.
6. Completion records status, actual minutes and notes; task history remains attached to the plan version.
7. All plan and task reads/writes are scoped to the authenticated user.

## Important syllabus limitation

The topic list is explicitly **provisional** and illustrative. It is not a complete syllabus and must not be represented as verified for UPSC CSE, IFoS, UPPSC PCS or UPPSC ACF/RFO. In particular, this phase does not yet encode paper/stage-specific depth, official syllabus versions, notification dates, optional subject rules, PYQ weights or resource references. The UI surfaces this limitation.

## Next implementation work

1. Build versioned syllabus source records from the official exam notifications and syllabus PDFs for the applicable cycles.
2. Model exam cycle → stage → paper → subject → topic, including effective dates and source URLs.
3. Add explicit shared-topic mappings with per-exam coverage notes; similar topic names must not imply identical coverage.
4. Add candidate optional-subject selection and validate eligibility/subject choices against the applicable notification.
5. Replace the illustrative starter topic rotation with verified syllabus nodes and prerequisite-aware workload allocation.
6. Add verified resource records and map them to syllabus nodes.
7. Add a weekly review and safe replanning workflow that preserves completed tasks and shows capacity trade-offs.

## API examples

Generate a 28-day plan:

```bash
curl -X POST http://localhost:8011/api/planner/generate \
  -H 'Content-Type: application/json' \
  -b cookies.txt -d '{"horizon_days":28}'
```

Read the active plan:

```bash
curl http://localhost:8011/api/planner/plan -b cookies.txt
```

Mark a task complete:

```bash
curl -X PATCH http://localhost:8011/api/planner/tasks/1 \
  -H 'Content-Type: application/json' -b cookies.txt \
  -d '{"status":"completed","actual_minutes":55,"notes":"Reviewed and practised"}'
```

The endpoints require an authenticated PrepCompass session cookie.
