"""Transparent, deterministic rolling planner.

The starter topic list is deliberately labelled provisional. It is a planning scaffold,
not a claim that it is a complete or notification-verified syllabus for any exam.
"""
import json
import sqlite3
from datetime import date, timedelta

STARTER_TOPICS = [
    ("polity-constitution", "General Studies", "Constitution: historical background and making", 90),
    ("polity-features", "General Studies", "Constitution: salient features and preamble", 90),
    ("rights", "General Studies", "Fundamental Rights, Duties and Directive Principles", 120),
    ("union-government", "General Studies", "Union executive and Parliament", 120),
    ("federalism", "General Studies", "Federalism, Centre–State relations and local government", 120),
    ("modern-history", "History", "Modern India: 18th-century transition and early resistance", 120),
    ("freedom-movement", "History", "Indian national movement: major phases and organisations", 120),
    ("ancient-culture", "History", "Ancient India: society, polity and cultural developments", 120),
    ("physical-geography", "Geography", "Physical geography: geomorphology and climatology", 120),
    ("indian-geography", "Geography", "India: resources, agriculture and regional geography", 120),
    ("economy-basics", "Economy", "National income, inflation, monetary and fiscal policy", 120),
    ("environment-ecology", "Environment", "Ecology, ecosystems, biodiversity and conservation", 120),
    ("environment-law", "Environment", "Environmental governance, institutions and conventions", 90),
    ("science-tech", "Science and Technology", "Science and technology: concepts and applications", 90),
    ("ethics-intro", "Ethics", "Ethics, values, attitude and aptitude: foundational concepts", 90),
    ("csat-reasoning", "CSAT", "CSAT: comprehension and analytical reasoning practice", 60),
    ("current-affairs", "Current Affairs", "Current affairs: issue-based reading and short notes", 45),
    ("forestry-ecology", "Forestry", "Forest ecology: structure, functions and succession", 120),
    ("forestry-silviculture", "Forestry", "Silviculture: regeneration, tending and forest management", 120),
    ("geology-basics", "Geology", "Geology: minerals, rocks and the rock cycle", 90),
]

TASK_TYPES = [
    ("learn", "Study the core concepts and make concise notes", 0.60),
    ("recall", "Close the material and write a short active-recall summary", 0.20),
    ("practice", "Attempt topic-linked questions and review every explanation", 0.20),
]


def ensure_planning_schema(database_path: str) -> None:
    with sqlite3.connect(database_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            assumptions_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, version)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS plan_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_date TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            subject TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            task_type TEXT NOT NULL,
            instruction TEXT NOT NULL,
            estimated_minutes INTEGER NOT NULL CHECK(estimated_minutes > 0),
            exam_ids_json TEXT NOT NULL,
            syllabus_status TEXT NOT NULL DEFAULT 'provisional',
            status TEXT NOT NULL DEFAULT 'planned',
            actual_minutes INTEGER NOT NULL DEFAULT 0,
            notes TEXT NOT NULL DEFAULT '',
            completed_at TEXT,
            created_at TEXT NOT NULL,
            UNIQUE(plan_id, task_date, sequence)
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plan_tasks_user_date ON plan_tasks(user_id, task_date)")
        conn.commit()


def generate_rolling_plan(database_path: str, user_id: int, horizon_days: int = 28) -> dict:
    if horizon_days < 7 or horizon_days > 56:
        raise ValueError("Planning horizon must be between 7 and 56 days")
    with sqlite3.connect(database_path) as conn:
        conn.row_factory = sqlite3.Row
        profile = conn.execute(
            "SELECT preparation_start_date, daily_hours, selected_days, current_level, medium FROM planner_profiles WHERE user_id=?",
            (user_id,),
        ).fetchone()
        targets = conn.execute(
            "SELECT exam_id, priority FROM candidate_exam_targets WHERE user_id=? ORDER BY priority, exam_id",
            (user_id,),
        ).fetchall()
        if not profile or not targets:
            raise ValueError("Complete your exam planner setup before generating a schedule")
        selected_days = set(json.loads(profile["selected_days"]))
        if not selected_days:
            raise ValueError("Your profile has no available study days")
        start = max(date.fromisoformat(profile["preparation_start_date"]), date.today())
        forest_targets = any(t["exam_id"] in {"upsc_ifos", "uppsc_acf_rfo"} for t in targets)
        topics = [
            x for x in STARTER_TOPICS
            if forest_targets or not x[0].startswith(("forestry-", "geology-"))
        ]
        daily_capacity = int(float(profile["daily_hours"]) * 60 * 0.85)
        if daily_capacity < 25:
            raise ValueError("Available daily time is too low to create useful study blocks")
        exam_ids = [row["exam_id"] for row in targets]
        created = date.today().isoformat()
        latest = conn.execute("SELECT COALESCE(MAX(version),0) AS v FROM study_plans WHERE user_id=?", (user_id,)).fetchone()["v"]
        version = latest + 1
        end = start + timedelta(days=horizon_days - 1)
        assumptions = {
            "engine": "deterministic-v1",
            "horizon_days": horizon_days,
            "daily_hours": float(profile["daily_hours"]),
            "capacity_buffer_percent": 15,
            "selected_days": sorted(selected_days),
            "exam_ids": exam_ids,
            "exam_ids_meaning": "Selected exam context only; not a claim that every provisional topic satisfies each exam syllabus.",
            "syllabus_status": "provisional",
            "notice": "Starter topics are illustrative planning scaffolds, not a complete or notification-verified syllabus. Confirm exam stages, syllabus and dates against the relevant official notification.",
        }
        cursor = conn.execute(
            "INSERT INTO study_plans(user_id,version,start_date,end_date,status,assumptions_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (user_id, version, start.isoformat(), end.isoformat(), "active", json.dumps(assumptions), created),
        )
        plan_id = cursor.lastrowid
        conn.execute("UPDATE study_plans SET status='superseded' WHERE user_id=? AND id<>? AND status='active'", (user_id, plan_id))
        day = start
        topic_index = 0
        scheduled_days = 0
        total_minutes = 0
        while day <= end:
            if day.weekday() in selected_days:
                remaining = daily_capacity
                sequence = 0
                topic = topics[topic_index % len(topics)]
                # Learning, recall and practice blocks reinforce the same topic.
                while remaining >= 25 and sequence < 3:
                    task_type, instruction, share = TASK_TYPES[sequence]
                    estimate = min(remaining, max(25, int(round(min(75, daily_capacity * share) / 5) * 5)))
                    if estimate < 25:
                        break
                    conn.execute(
                        """INSERT INTO plan_tasks(plan_id,user_id,task_date,sequence,subject,topic_id,topic,task_type,instruction,
                           estimated_minutes,exam_ids_json,syllabus_status,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (plan_id,user_id,day.isoformat(),sequence+1,topic[1],topic[0],topic[2],task_type,
                         instruction,estimate,json.dumps(exam_ids),"provisional",created),
                    )
                    remaining -= estimate
                    total_minutes += estimate
                    sequence += 1
                topic_index += 1
                scheduled_days += 1
            day += timedelta(days=1)
        conn.commit()
    with sqlite3.connect(database_path) as conn:
        task_count = conn.execute("SELECT COUNT(*) FROM plan_tasks WHERE plan_id=?", (plan_id,)).fetchone()[0]
    return {
        "plan_id": plan_id, "version": version, "start_date": start.isoformat(),
        "end_date": end.isoformat(), "scheduled_days": scheduled_days,
        "task_count": task_count,
        "planned_minutes": total_minutes, "assumptions": assumptions,
    }
