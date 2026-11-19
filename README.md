# PrepCompass

**Plan. Prepare. Progress.**

PrepCompass is a local-first study management application for integrated preparation for UPSC Civil Services, Indian Forest Service, UPPSC PCS and UPPSC ACF/RFO.

## Product principles
- Local-first: study data is stored in SQLite on your own machine.
- Practical planning: daily targets, syllabus progress, study sessions, revision and tests.
- Multi-exam aware: shared General Studies foundation with exam-specific requirements.
- AI-assisted, not AI-dependent: exportable progress snapshots can be shared with ChatGPT for analysis and plan adjustments.

## Technology
- Frontend: Next.js, React and TypeScript
- Backend: FastAPI (Python)
- Database: SQLite
- Local runtime: Docker Compose

## Current milestone: Planner B — rolling daily plan generation and task progress
- Generate a deterministic, rolling 28-day schedule from the saved preparation profile
- Respect selected study weekdays and reserve a 15% daily capacity buffer
- Create focused learning, active-recall and practice blocks
- Persist versioned plans and account-scoped daily tasks in SQLite
- View tasks by date and mark work completed with actual minutes
- Clearly label starter topics as provisional until official syllabus sources are verified

## Previous milestone: Planner Foundation — multi-exam setup and candidate profile
- Account-scoped exam catalogue for UPSC CSE, IFoS, UPPSC PCS and ACF/RFO
- Select multiple exams with independent attempt years
- Save preparation start date, study medium, weekly study days, daily hours and current level
- Responsive guided planner setup with exam cards, progress steps and review screen
- Planner catalog, setup, save and overview APIs

## Previous milestone: Phase 2A — accounts and private workspaces
- Email/password registration and sign-in
- Optional Google OAuth 2.0 sign-in with state validation and PKCE
- HTTP-only, hashed server-side sessions
- Authenticated dashboard and study-session APIs
- Per-account study-session isolation
- SQLite migration that leaves pre-account legacy records unassigned
- Regression tests for authentication, isolation and migration

## Previous milestone: Phase 1 foundation
- Responsive dashboard shell
- Daily study goal and tracked study time
- Record a study session with subject, topic, duration and notes
- Recent study-session history
- FastAPI health and dashboard endpoints
- SQLite persistence through a Docker volume

## Run locally with Docker

Prerequisites: Docker Desktop installed and running.

```bash
git clone https://github.com/KrishnaGopalYadav/PrepCompass.git
cd PrepCompass
docker compose up --build
```

Open:
- Frontend: http://localhost:3011
- API health: http://localhost:8011/api/health
- API documentation: http://localhost:8011/docs

To stop: `docker compose down`. Your data remains in `backend/data`.
To stop and remove containers only: `docker compose down`. Do not delete `backend/data` if you want to retain your records.

## Run without Docker

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (in a second terminal):
```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8011` if needed.


## Account setup

On first launch, open the frontend and create an account. Each account has a separate study history. Email/password accounts require a password of at least 10 characters.

### Optional Google sign-in

1. Open Google Cloud Console and create/select a project.
2. Configure the OAuth consent screen for the intended audience.
3. Create an OAuth Client ID with application type **Web application**.
4. Add this authorised redirect URI exactly:
   `http://localhost:8011/api/auth/google/callback`
5. Copy `backend/.env.example` to `backend/.env`.
6. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `backend/.env`.
7. Restart/rebuild the services: `docker compose up --build -d`.

Google credentials belong to the application operator, not each end user. Never commit `backend/.env`, publish the client secret, or paste it into chat. Email/password registration works even when Google credentials are not configured.

For local HTTP development, `COOKIE_SECURE=false` is expected. For an HTTPS deployment, set `COOKIE_SECURE=true`, use HTTPS redirect/origin URLs, and store secrets in the deployment's secret manager.

### Existing study data

The database migration adds a nullable `user_id` to existing study sessions. Old rows remain unassigned and are not automatically exposed to the first account that registers. This is intentional to prevent accidental disclosure in a multi-user installation. A deliberate legacy-data import/claim workflow can be added after the owner verifies which account should receive those records.

### Backend tests

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## Preparation profile defaults
The initial product plan is based on the following preparation context and can be edited in later milestones:
- Target year: 2028
- Exams: UPSC CSE, UPSC IFoS, UPPSC PCS, UPPSC ACF/RFO
- Medium: English
- Available study time: approximately 2–3 hours/day
- Provisional optionals: Sociology (CSE); Forestry and Geology (IFoS / ACF-RFO, subject to the relevant notification)

Exam rules and eligibility must always be checked against the notification for the relevant examination year. UPPSC PCS does not have an optional subject; ACF/RFO and IFoS have their own subject requirements.

## Product roadmap

1. Foundation and study-session tracking
2. Multi-user accounts and secure authentication
3. **Personalised exam planner:** exam selection, attempt-year targets, candidate availability and rolling daily schedules (starter topics currently provisional); next: verified syllabus mapping and resource catalogue
4. Daily execution: calendar, task logging, timers, revision scheduling and resource library
5. Progress validation: planned-versus-actual analytics, topic mastery, tests/mocks and adaptive replanning
6. Progress export/import, ChatGPT study-coach workflow, backup and restore
7. Cross-platform packaging: installable web app (PWA), Android app, iPhone/iPad app and macOS app, with a common product experience

See [Personalised Exam Planner — Product and Technical Design](docs/PERSONALISED_EXAM_PLANNER_DESIGN.md) for the detailed user journey, data model, planning engine, acceptance criteria and delivery milestones.

## Privacy
Do not commit real study records, database files, API keys or personal secrets. Local database files are ignored by Git.
