const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type User = { id: number; email: string; display_name: string };
export type StudySession = {
  id: number; subject: string; topic: string; duration_minutes: number; studied_on: string; notes: string;
};
export type DashboardData = {
  today: { date: string; studied_minutes: number; goal_minutes: number };
  this_week: { studied_minutes: number; goal_minutes: number };
  total_sessions: number;
  recent_sessions: StudySession[];
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, {
    ...init, headers, credentials: "include", cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || "Request failed");
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export const getCurrentUser = () => request<User>("/api/auth/me");
export const registerAccount = (payload: { email: string; display_name: string; password: string }) =>
  request<User>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) });
export const loginAccount = (payload: { email: string; password: string }) =>
  request<User>("/api/auth/login", { method: "POST", body: JSON.stringify(payload) });
export const logoutAccount = () => request<{ status: string }>("/api/auth/logout", { method: "POST" });
export const googleSignInUrl = `${API_BASE}/api/auth/google/start`;
export const getGoogleOAuthConfig = () => request<{ enabled: boolean }>("/api/auth/google/config");

export const getDashboard = () => request<DashboardData>("/api/dashboard");
export const saveStudySession = (payload: {
  subject: string; topic: string; duration_minutes: number; studied_on: string; notes: string;
}) => request<StudySession>("/api/study-sessions", { method: "POST", body: JSON.stringify(payload) });

 
export type ExamOption = {
  exam_id: string; name: string; short_name: string; conducting_body: string;
  description: string; syllabus_status: string;
};
export type PlannerTarget = { exam_id: string; attempt_year: number; priority: number };
export type PlannerProfile = {
  preparation_start_date: string; medium: string; daily_hours: number;
  current_level: "beginner" | "intermediate" | "advanced";
  selected_days: number[]; rest_day: string;
};
export type PlannerOverview = {
  configured: boolean; profile: (PlannerProfile & { selected_days: number[] }) | null;
  exam_targets: (PlannerTarget & { name: string; short_name: string; syllabus_status: string })[];
};
export const getExamCatalog = () => request<ExamOption[]>("/api/planner/catalog");
export const getPlannerSetup = () => request<{ profile: PlannerProfile | null; exam_targets: PlannerTarget[] }>("/api/planner/setup");
export const savePlannerSetup = (payload: PlannerProfile & { exam_targets: PlannerTarget[] }) =>
  request<{ status: string; exam_count: number; message: string }>("/api/planner/setup", { method: "POST", body: JSON.stringify(payload) });
export const getPlannerOverview = () => request<PlannerOverview>("/api/planner/overview");

export type GeneratedPlanTask = {
  id: number; task_date: string; sequence: number; subject: string; topic_id: string;
  topic: string; task_type: string; instruction: string; estimated_minutes: number;
  exam_ids: string[]; syllabus_status: string; status: string; actual_minutes: number; notes: string;
};
export type GeneratedPlan = {
  id: number; version: number; start_date: string; end_date: string; status: string;
  assumptions: { notice: string; syllabus_status: string; [key: string]: unknown };
};
export type GeneratedPlanResponse = {
  configured: boolean; has_setup: boolean; plan: GeneratedPlan | null; tasks: GeneratedPlanTask[];
};
export const generateStudyPlan = (horizon_days = 28) =>
  request<{ plan_id: number; version: number; start_date: string; end_date: string;
    scheduled_days: number; task_count: number; planned_minutes: number;
    assumptions: GeneratedPlan["assumptions"] }>(
      "/api/planner/generate", { method: "POST", body: JSON.stringify({ horizon_days }) }
    );
export const getGeneratedPlan = () => request<GeneratedPlanResponse>("/api/planner/plan");
export const updatePlanTask = (taskId: number, payload: {
  status: "planned" | "in_progress" | "completed" | "partial" | "skipped";
  actual_minutes: number; notes: string;
}) => request<{ id: number; status: string; actual_minutes: number }>(
  `/api/planner/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) }
);
