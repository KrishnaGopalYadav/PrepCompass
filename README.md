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

## Current milestone: Phase 1 foundation
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

## Preparation profile defaults
The initial product plan is based on the following preparation context and can be edited in later milestones:
- Target year: 2028
- Exams: UPSC CSE, UPSC IFoS, UPPSC PCS, UPPSC ACF/RFO
- Medium: English
- Available study time: approximately 2–3 hours/day
- Provisional optionals: Sociology (CSE); Forestry and Geology (IFoS / ACF-RFO, subject to the relevant notification)

Exam rules and eligibility must always be checked against the notification for the relevant examination year. UPPSC PCS does not have an optional subject; ACF/RFO and IFoS have their own subject requirements.

## Roadmap
1. Foundation and study-session tracking
2. Personalised exam calendar, daily planner and syllabus tracker
3. Revision scheduling and resource library
4. Topic-wise tests, mock tests and performance analytics
5. Progress export/import and ChatGPT study-coach workflow
6. Backup, restore, usability and reliability improvements

## Privacy
Do not commit real study records, database files, API keys or personal secrets. Local database files are ignored by Git.
