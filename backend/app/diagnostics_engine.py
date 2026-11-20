"""Objective study analytics and diagnostic-history persistence."""

import json
import sqlite3
from datetime import date, timedelta


def ensure_diagnostics_schema(database_path: str) -> None:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS study_diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                period_days INTEGER NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                recommendations_json TEXT,
                ai_status TEXT NOT NULL DEFAULT 'pending',
                ai_provider TEXT,
                ai_model TEXT,
                created_at TEXT NOT NULL
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_diagnostics_user_created
            ON study_diagnostics(user_id, created_at DESC, id DESC)
        """)
        connection.commit()


def calculate_study_metrics(
    database_path: str,
    user_id: int,
    period_days: int = 28,
    today: date | None = None,
) -> dict:
    if not 7 <= period_days <= 90:
        raise ValueError("Diagnostic period must be between 7 and 90 days")

    today = today or date.today()
    start_date = today - timedelta(days=period_days - 1)
    start = start_date.isoformat()
    end = today.isoformat()

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

        sessions = connection.execute("""
            SELECT
                COUNT(*) AS total_sessions,
                COALESCE(SUM(duration_minutes), 0) AS total_minutes,
                COUNT(DISTINCT studied_on) AS study_days,
                COALESCE(AVG(duration_minutes), 0) AS average_session_minutes
            FROM study_sessions
            WHERE user_id = ?
              AND studied_on >= ?
              AND studied_on <= ?
        """, (user_id, start, end)).fetchone()

        subjects = connection.execute("""
            SELECT subject,
                   COUNT(*) AS sessions,
                   SUM(duration_minutes) AS total_minutes
            FROM study_sessions
            WHERE user_id = ?
              AND studied_on >= ?
              AND studied_on <= ?
            GROUP BY subject
            ORDER BY total_minutes DESC, subject
        """, (user_id, start, end)).fetchall()

        profile = connection.execute("""
            SELECT selected_days, daily_hours
            FROM planner_profiles
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        if profile:
            selected_days = set(json.loads(profile["selected_days"]))
            expected_days = sum(
                1 for offset in range(period_days)
                if (start_date + timedelta(days=offset)).weekday() in selected_days
            )
            daily_goal_minutes = round(profile["daily_hours"] * 60)
        else:
            expected_days = period_days
            daily_goal_minutes = None

        tasks = connection.execute("""
            SELECT
                COUNT(*) AS scheduled_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
                    AS completed_tasks,
                SUM(CASE WHEN status = 'partial' THEN 1 ELSE 0 END)
                    AS partial_tasks,
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END)
                    AS skipped_tasks,
                COALESCE(SUM(estimated_minutes), 0) AS planned_minutes,
                COALESCE(SUM(actual_minutes), 0) AS actual_minutes
            FROM plan_tasks
            WHERE user_id = ?
              AND task_date >= ?
              AND task_date <= ?
        """, (user_id, start, end)).fetchone()

    study_days = sessions["study_days"]
    scheduled_tasks = tasks["scheduled_tasks"]
    completed_tasks = tasks["completed_tasks"] or 0

    return {
        "period": {
            "days": period_days,
            "start_date": start,
            "end_date": end,
        },
        "study_activity": {
            "total_sessions": sessions["total_sessions"],
            "total_minutes": sessions["total_minutes"],
            "total_hours": round(sessions["total_minutes"] / 60, 2),
            "study_days": study_days,
            "expected_study_days": expected_days,
            "consistency_percent": round(
                min(study_days, expected_days) / expected_days * 100, 1
            ) if expected_days else 0,
            "average_session_minutes": round(
                sessions["average_session_minutes"], 1
            ),
            "daily_goal_minutes": daily_goal_minutes,
        },
        "subject_distribution": [
            {
                "subject": row["subject"],
                "sessions": row["sessions"],
                "total_minutes": row["total_minutes"],
            }
            for row in subjects
        ],
        "planner_progress": {
            "scheduled_tasks": scheduled_tasks,
            "completed_tasks": completed_tasks,
            "partial_tasks": tasks["partial_tasks"] or 0,
            "skipped_tasks": tasks["skipped_tasks"] or 0,
            "completion_percent": round(
                completed_tasks / scheduled_tasks * 100, 1
            ) if scheduled_tasks else None,
            "planned_minutes": tasks["planned_minutes"],
            "actual_minutes": tasks["actual_minutes"],
        },
        "data_limitations": [
            "Study activity measures recorded sessions, not independently verified learning.",
            "Planner task completion does not establish syllabus mastery.",
            "Subject distribution reflects recorded study time, not exam readiness.",
        ],
    }


def save_diagnostic(
    database_path: str,
    *,
    user_id: int,
    period_days: int,
    metrics: dict,
    ai_status: str,
    recommendations: dict | None = None,
    provider: str | None = None,
    model: str | None = None,
    created_at: str,
) -> int:
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        cursor = connection.execute("""
            INSERT INTO study_diagnostics (
                user_id, period_days, period_start, period_end,
                metrics_json, recommendations_json, ai_status,
                ai_provider, ai_model, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            period_days,
            metrics["period"]["start_date"],
            metrics["period"]["end_date"],
            json.dumps(metrics, ensure_ascii=False),
            json.dumps(recommendations, ensure_ascii=False)
                if recommendations is not None else None,
            ai_status,
            provider,
            model,
            created_at,
        ))
        connection.commit()
        return cursor.lastrowid


def get_diagnostic(
    database_path: str,
    user_id: int,
    diagnostic_id: int,
) -> dict | None:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("""
            SELECT *
            FROM study_diagnostics
            WHERE id = ? AND user_id = ?
        """, (diagnostic_id, user_id)).fetchone()

    if not row:
        return None

    result = dict(row)
    result["metrics"] = json.loads(result.pop("metrics_json"))
    recommendations = result.pop("recommendations_json")
    result["recommendations"] = (
        json.loads(recommendations) if recommendations else None
    )
    return result


def list_diagnostics(
    database_path: str,
    user_id: int,
    limit: int = 20,
) -> list[dict]:
    limit = max(1, min(limit, 100))

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute("""
            SELECT id, period_days, period_start, period_end,
                   ai_status, ai_provider, ai_model, created_at
            FROM study_diagnostics
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

    return [dict(row) for row in rows]
