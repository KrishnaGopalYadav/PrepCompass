const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type StudySession = {
  id: number;
  subject: string;
  topic: string;
  duration_minutes: number;
  studied_on: string;
  notes: string;
};

export type DashboardData = {
  today: { date: string; studied_minutes: number; goal_minutes: number };
  this_week: { studied_minutes: number; goal_minutes: number };
  total_sessions: number;
  recent_sessions: StudySession[];
};

export async function getDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load dashboard");
  return response.json();
}

export async function saveStudySession(payload: {
  subject: string; topic: string; duration_minutes: number; studied_on: string; notes: string;
}): Promise<StudySession> {
  const response = await fetch(`${API_BASE}/api/study-sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail?.[0]?.msg || "Could not save study session");
  }
  return response.json();
}
