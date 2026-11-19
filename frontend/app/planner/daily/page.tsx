"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, BookOpen, CalendarDays, CheckCircle2, Clock3, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { GeneratedPlanResponse, generateStudyPlan, getCurrentUser, getGeneratedPlan, updatePlanTask } from "@/lib/api";

function minutes(value: number) {
  const h = Math.floor(value / 60);
  const m = value % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

export default function DailyPlanPage() {
  const router = useRouter();
  const [data, setData] = useState<GeneratedPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    const result = await getGeneratedPlan();
    setData(result);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await getCurrentUser();
        await refresh();
      } catch (e) {
        if (e instanceof Error && e.message === "Authentication required") router.replace("/login");
        else setError(e instanceof Error ? e.message : "Could not load your plan");
      } finally {
        setLoading(false);
      }
    })();
  }, [refresh, router]);

  async function generate() {
    setGenerating(true); setError(""); setNotice("");
    try {
      const result = await generateStudyPlan(28);
      await refresh();
      setNotice(`Created plan version ${result.version}: ${result.task_count} tasks across ${result.scheduled_days} study days.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate your plan");
    } finally { setGenerating(false); }
  }

  async function completeTask(taskId: number, estimate: number) {
    try {
      await updatePlanTask(taskId, { status: "completed", actual_minutes: estimate, notes: "" });
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update task");
    }
  }

  const grouped = useMemo(() => {
    const map = new Map<string, NonNullable<GeneratedPlanResponse["tasks"]>>();
    for (const task of data?.tasks ?? []) {
      map.set(task.task_date, [...(map.get(task.task_date) ?? []), task]);
    }
    return Array.from(map.entries());
  }, [data]);

  if (loading) return <main className="planner-loading"><Loader2 className="spin" size={22}/> Loading your daily plan…</main>;

  return <main className="daily-plan-shell">
    <header className="daily-plan-header">
      <Link href="/planner" className="daily-back"><ArrowLeft size={16}/> Planner setup</Link>
      <div className="daily-plan-brand"><span><Sparkles size={18}/></span><b>PrepCompass</b></div>
    </header>
    <section className="daily-plan-content">
      <div className="daily-plan-intro">
        <div><div className="planner-kicker"><CalendarDays size={13}/> YOUR NEXT 4 WEEKS</div>
          <h1>Your daily <em>study plan.</em></h1>
          <p>A rolling plan based on your saved availability and selected exams.</p></div>
        {data?.plan && <button className="planner-primary" onClick={generate} disabled={generating}>
          {generating ? <Loader2 className="spin" size={16}/> : <RefreshCw size={16}/>}
          {generating ? "Generating…" : data?.plan ? "Regenerate plan" : "Generate my plan"}
        </button>}
      </div>

      {error && <div className="planner-error" role="alert">{error}</div>}
      {notice && <div className="daily-plan-notice"><CheckCircle2 size={16}/>{notice}</div>}

      {!data?.plan ? <section className="daily-plan-empty">
        <div><CalendarDays size={28}/></div><h2>Your plan is ready to be generated</h2>
        <p>{data?.has_setup ? "Your preparation profile is saved. Generate a rolling 28-day schedule from your selected availability." : "Save your exam targets and availability first. PrepCompass will then create a rolling 28-day schedule."}</p>
        {data?.has_setup && <button className="planner-primary" onClick={generate} disabled={generating}>{generating ? "Generating…" : "Generate my plan"}</button>}
        <Link href="/planner" className="planner-primary">Review planner setup</Link>
      </section> : <>
        <div className="daily-plan-warning"><AlertTriangle size={18}/><div><b>Starter schedule — syllabus verification pending</b><p>{data.plan.assumptions.notice}</p></div></div>
        <div className="daily-plan-summary">
          <div><span>PLAN VERSION</span><b>v{data.plan.version}</b></div>
          <div><span>DATE RANGE</span><b>{data.plan.start_date} – {data.plan.end_date}</b></div>
          <div><span>TASKS</span><b>{data.tasks.length}</b></div>
          <div><span>COMPLETED</span><b>{data.tasks.filter(t=>t.status==="completed").length} / {data.tasks.length}</b></div>
        </div>
        <div className="daily-task-list">
          {grouped.map(([day, tasks]) => <section className="daily-date-group" key={day}>
            <div className="daily-date-heading"><div><span>STUDY DAY</span><h2>{new Date(day+"T00:00:00").toLocaleDateString("en-IN",{weekday:"long",day:"numeric",month:"short"})}</h2></div>
              <span><Clock3 size={14}/> {minutes(tasks.reduce((sum,t)=>sum+t.estimated_minutes,0))}</span></div>
            {tasks.map(task => <article className={"daily-task-card "+(task.status==="completed"?"task-done":"")} key={task.id}>
              <div className="daily-task-type"><BookOpen size={16}/></div>
              <div className="daily-task-body"><div className="daily-task-meta">{task.subject} · {task.task_type.replace("_"," ").toUpperCase()} · {task.syllabus_status.toUpperCase()}</div>
                <h3>{task.topic}</h3><p>{task.instruction}</p>
                <div className="daily-task-foot"><span><Clock3 size={13}/> {minutes(task.estimated_minutes)}</span><span>Selected exam context: {task.exam_ids.join(", ")}</span></div>
              </div>
              <button className="daily-task-action" disabled={task.status==="completed"} onClick={()=>completeTask(task.id,task.estimated_minutes)}>
                {task.status==="completed" ? <><CheckCircle2 size={15}/> Completed</> : "Mark complete"}
              </button>
            </article>)}
          </section>)}
        </div>
      </>}
    </section>
  </main>;
}
