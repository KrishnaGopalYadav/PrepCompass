"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, CalendarDays, Check, CheckCircle2, ChevronRight, Clock3, Compass, GraduationCap, Leaf, Loader2, ShieldCheck, Sparkles, Target, UserRound, BookOpen, Info } from "lucide-react";
import { getCurrentUser, getExamCatalog, getPlannerOverview, getPlannerSetup, savePlannerSetup, ExamOption, PlannerOverview, PlannerTarget, User } from "@/lib/api";

const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const fullDays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const currentYear = new Date().getFullYear();
const initialDate = new Date().toLocaleDateString("en-CA");

type TargetState = Record<string, { selected: boolean; year: number; priority: number }>;

export default function PlannerPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [catalog, setCatalog] = useState<ExamOption[]>([]);
  const [overview, setOverview] = useState<PlannerOverview | null>(null);
  const [step, setStep] = useState(1);
  const [targets, setTargets] = useState<TargetState>({});
  const [startDate, setStartDate] = useState(initialDate);
  const [medium, setMedium] = useState("English");
  const [hours, setHours] = useState(2.5);
  const [level, setLevel] = useState<"beginner" | "intermediate" | "advanced">("beginner");
  const [days, setDays] = useState<number[]>([0, 1, 2, 3, 4, 5]);
  const [restDay, setRestDay] = useState("Sunday");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([getExamCatalog(), getPlannerSetup(), getPlannerOverview()])
      .then(([exams, setup, saved]) => {
        setCatalog(exams);
        setOverview(saved);
        const next: TargetState = {};
        exams.forEach(exam => {
          const existing = setup.exam_targets.find(t => t.exam_id === exam.exam_id);
          next[exam.exam_id] = { selected: !!existing, year: existing?.attempt_year ?? 2028, priority: existing?.priority ?? 1 };
        });
        setTargets(next);
        if (setup.profile) {
          setStartDate(setup.profile.preparation_start_date);
          setMedium(setup.profile.medium);
          setHours(setup.profile.daily_hours);
          setLevel(setup.profile.current_level);
          setDays(setup.profile.selected_days);
          setRestDay(setup.profile.rest_day);
        }
      })
      .catch(e => setError(e instanceof Error ? e.message : "Could not load planner setup"))
      .finally(() => setLoading(false));
  }, [user]);

  const selected = useMemo(() => catalog.filter(exam => targets[exam.exam_id]?.selected), [catalog, targets]);
  const weeklyHours = hours * days.length;
  const selectedTargets: PlannerTarget[] = selected.map(exam => ({
    exam_id: exam.exam_id, attempt_year: targets[exam.exam_id].year, priority: targets[exam.exam_id].priority,
  }));

  function toggleExam(id: string) {
    setTargets(prev => ({ ...prev, [id]: { ...prev[id], selected: !prev[id]?.selected } }));
  }
  function setYear(id: string, year: number) {
    setTargets(prev => ({ ...prev, [id]: { ...prev[id], year } }));
  }
  function toggleDay(index: number) {
    setDays(prev => prev.includes(index) ? prev.filter(d => d !== index) : [...prev, index].sort());
  }
  function nextStep() {
    setError("");
    if (step === 1 && selected.length === 0) { setError("Select at least one examination to continue."); return; }
    if (step === 2 && days.length === 0) { setError("Choose at least one study day."); return; }
    setStep(s => Math.min(3, s + 1));
  }
  async function savePlan() {
    setSaving(true); setError(""); setSuccess("");
    try {
      const result = await savePlannerSetup({
        preparation_start_date: startDate, medium, daily_hours: hours,
        current_level: level, selected_days: days, rest_day: restDay,
        exam_targets: selectedTargets,
      });
      const fresh = await getPlannerOverview();
      setOverview(fresh);
      setSuccess(result.message);
      setStep(4);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save your preparation profile.");
    } finally { setSaving(false); }
  }

  if (!user || loading) return <main className="planner-loading"><Loader2 className="spin" size={22} /> Preparing your planner…</main>;

  return (
    <main className="planner-shell">
      <aside className="planner-sidebar">
        <Link href="/" className="planner-brand"><span className="planner-brand-mark"><Compass size={21}/></span><span><b>PrepCompass</b><small>YOUR PREPARATION OS</small></span></Link>
        <div className="planner-side-caption">YOUR WORKSPACE</div>
        <Link href="/" className="planner-nav"><Target size={17}/> Overview</Link>
        <Link href="/planner" className="planner-nav active"><CalendarDays size={17}/> Exam planner <span>NEW</span></Link>
        <a href="/#study-log" className="planner-nav"><Clock3 size={17}/> Study log</a>
        <a href="/#roadmap" className="planner-nav"><BookOpen size={17}/> Syllabus tracker</a>
        <div className="planner-sidebar-foot"><div className="planner-user-avatar">{user.display_name.slice(0,1).toUpperCase()}</div><div><b>{user.display_name}</b><small>Personal workspace</small></div></div>
      </aside>

      <section className="planner-main">
        <header className="planner-topbar"><div><span>Workspace</span><ChevronRight size={13}/><b>Exam planner</b></div><div className="planner-top-user"><span className="planner-local-dot"/> Private workspace <span className="planner-top-avatar">{user.display_name.slice(0,1).toUpperCase()}</span></div></header>
        <div className="planner-content">
          <div className="planner-heading">
            <div><div className="planner-kicker"><Sparkles size={13}/> YOUR PREPARATION, MADE PERSONAL</div><h1>Build your <em>success plan.</em></h1><p>Tell us what you're preparing for. We'll help turn your goal into a realistic daily routine.</p></div>
            <div className="planner-heading-art"><div className="planner-art-circle"><GraduationCap size={34}/></div><span className="planner-art-star">✳</span></div>
          </div>

          {overview?.configured && step === 1 && (
            <section className="planner-saved-banner">
              <div className="planner-saved-icon"><CheckCircle2 size={21}/></div>
              <div><b>You have a preparation profile</b><p>{overview.exam_targets.map(t => t.short_name + " " + t.attempt_year).join(" · ")} · {overview.profile?.daily_hours} hours/day</p></div>
              <button onClick={() => setStep(2)}>Edit profile <ArrowRight size={14}/></button>
            </section>
          )}

          <div className="planner-workspace">
            <div className="planner-form-area">
              <div className="planner-progress-head"><div><span>SETUP YOUR PLAN</span><b>Step {Math.min(step,3)} of 3</b></div><span>{step === 4 ? "SAVED" : Math.round((step/3)*100) + "% complete"}</span></div>
              <div className="planner-progress-track"><span style={{width: step===4 ? "100%" : (step/3*100)+"%"}}/></div>
              <div className="planner-steps">
                {[["01","Choose exams"],["02","Your routine"],["03","Review"]].map(([num,label],i)=><div key={num} className={step===i+1?"current":step>i+1||step===4?"done":""}><span>{step>i+1||step===4?<Check size={13}/>:num}</span>{label}</div>)}
              </div>

              {step === 1 && <section className="planner-step-content">
                <div className="planner-step-title"><div className="planner-step-icon"><GraduationCap size={19}/></div><div><h2>Which exams are you targeting?</h2><p>Select one or more. You can prepare for multiple examinations together.</p></div></div>
                <div className="planner-exam-grid">
                  {catalog.map(exam => {
                    const checked = !!targets[exam.exam_id]?.selected;
                    return <button type="button" key={exam.exam_id} onClick={() => toggleExam(exam.exam_id)} className={"planner-exam-card "+(checked?"chosen":"")}>
                      <span className="planner-exam-check">{checked?<Check size={14}/>:null}</span>
                      <span className="planner-exam-symbol">{exam.exam_id.includes("ifos")||exam.exam_id.includes("acf")?<Leaf size={20}/>:<GraduationCap size={20}/>}</span>
                      <span className="planner-exam-body"><b>{exam.short_name}</b><strong>{exam.name}</strong><small>{exam.conducting_body}</small></span>
                      <span className="planner-exam-desc">{exam.description}</span>
                      {checked && <span className="planner-year-control" onClick={e=>e.stopPropagation()}><label htmlFor={"year-"+exam.exam_id}>TARGET ATTEMPT</label><select id={"year-"+exam.exam_id} value={targets[exam.exam_id].year} onChange={e=>setYear(exam.exam_id,Number(e.target.value))}>{Array.from({length:8},(_,i)=>currentYear+i).map(y=><option key={y} value={y}>{y}</option>)}</select></span>}
                    </button>;
                  })}
                </div>
                <div className="planner-inline-note"><Info size={15}/><span>You can set a different attempt year for each exam. Dates and syllabus details will be checked against the relevant official notification as the planner is developed.</span></div>
              </section>}

              {step === 2 && <section className="planner-step-content">
                <div className="planner-step-title"><div className="planner-step-icon"><Clock3 size={19}/></div><div><h2>Make this plan fit your life.</h2><p>A sustainable routine beats an ambitious plan you cannot follow.</p></div></div>
                <div className="planner-field-grid">
                  <label className="planner-field"><span>PREPARATION START DATE</span><div className="planner-input-icon"><CalendarDays size={16}/><input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)} min={initialDate}/></div><small>When should your preparation plan begin?</small></label>
                  <label className="planner-field"><span>STUDY MEDIUM</span><select value={medium} onChange={e=>setMedium(e.target.value)}><option>English</option><option>Hindi</option><option>Bilingual (English + Hindi)</option></select><small>Resources and explanations will follow this preference.</small></label>
                </div>
                <div className="planner-hours-card"><div className="planner-hours-top"><div><span>DAILY STUDY AVAILABILITY</span><h3>How much time can you give each day?</h3></div><div className="planner-hours-value">{hours}<small>hours / day</small></div></div><input className="planner-range" type="range" min="0.5" max="10" step="0.5" value={hours} onChange={e=>setHours(Number(e.target.value))}/><div className="planner-range-labels"><span>30 min</span><span>5 hours</span><span>10 hours</span></div><div className="planner-week-total"><Clock3 size={15}/><b>{weeklyHours.toFixed(1)} hours / week</b><span>based on {days.length} study days</span></div></div>
                <div className="planner-days-card"><div><h3>Choose your study days</h3><p>Give yourself space to rest and reset.</p></div><div className="planner-day-options">{weekdays.map((day,i)=><button type="button" key={day} onClick={()=>toggleDay(i)} className={days.includes(i)?"selected":""}>{day.slice(0,1)}<small>{day}</small></button>)}</div><label className="planner-rest-day">Preferred rest day <select value={restDay} onChange={e=>setRestDay(e.target.value)}>{fullDays.map(d=><option key={d}>{d}</option>)}</select></label></div>
                <div className="planner-level-card"><div><h3>Where are you in your preparation?</h3><p>This helps estimate the amount of foundation work needed.</p></div><div className="planner-level-options">{(["beginner","intermediate","advanced"] as const).map((v)=><button key={v} type="button" onClick={()=>setLevel(v)} className={level===v?"selected":""}><b>{v[0].toUpperCase()+v.slice(1)}</b><small>{v==="beginner"?"Starting from the basics":v==="intermediate"?"Some syllabus already covered":"Revising and practising"}</small></button>)}</div></div>
              </section>}

              {step === 3 && <section className="planner-step-content">
                <div className="planner-step-title"><div className="planner-step-icon"><ShieldCheck size={19}/></div><div><h2>Your preparation blueprint.</h2><p>Review your choices before saving your profile.</p></div></div>
                <div className="planner-review-card"><div className="planner-review-top"><div><span>YOUR EXAM TARGETS</span><b>{selected.length} examination{selected.length===1?"":"s"} selected</b></div><button onClick={()=>setStep(1)}>Edit</button></div>{selected.map(exam=><div className="planner-review-exam" key={exam.exam_id}><span className="planner-review-check"><Check size={13}/></span><div><b>{exam.short_name}</b><small>{exam.name}</small></div><strong>Attempt {targets[exam.exam_id].year}</strong></div>)}</div>
                <div className="planner-review-grid"><div><CalendarDays size={18}/><span>START DATE</span><b>{new Date(startDate+"T00:00:00").toLocaleDateString("en-IN",{day:"numeric",month:"short",year:"numeric"})}</b></div><div><Clock3 size={18}/><span>WEEKLY TIME</span><b>{weeklyHours.toFixed(1)} hours</b></div><div><BookOpen size={18}/><span>STUDY MEDIUM</span><b>{medium}</b></div><div><UserRound size={18}/><span>STARTING LEVEL</span><b>{level[0].toUpperCase()+level.slice(1)}</b></div></div>
                <div className="planner-review-note"><Sparkles size={18}/><div><b>What happens after you save?</b><p>We'll keep these goals and preferences in your private account. The next milestone uses verified syllabus data to calculate phases, weekly targets, daily tasks and resources. We won't generate a fake schedule from unverified exam information.</p></div></div>
              </section>}

              {step === 4 && <section className="planner-success">
                <div className="planner-success-mark"><CheckCircle2 size={32}/></div><span>PROFILE SAVED</span><h2>Your preparation journey has a starting point.</h2><p>Your exam targets and study preferences are saved to your private PrepCompass workspace.</p>
                <div className="planner-success-summary">{overview?.exam_targets.map(t=><span key={t.exam_id}>{t.short_name} · {t.attempt_year}</span>)}</div>
                <div className="planner-next-box"><b>Coming in the next planner milestone</b><p>Verified syllabus coverage, day-by-day schedule generation, recommended resources, revision cycles and progress validation.</p></div>
                <button className="planner-primary" onClick={()=>router.push("/")}>Go to my dashboard <ArrowRight size={16}/></button>
                <button className="planner-text-button" onClick={()=>setStep(1)}>Edit preparation profile</button>
              </section>}

              {error && <div className="planner-error" role="alert">{error}</div>}
              {success && step===4 && <div className="planner-success-message">{success}</div>}
              {step !== 4 && <div className="planner-form-footer"><button className="planner-back" onClick={()=>step===1?router.push("/"):setStep(s=>s-1)}>{step===1?<><ArrowLeft size={15}/> Dashboard</>:<><ArrowLeft size={15}/> Back</>}</button>{step<3?<button className="planner-primary" onClick={nextStep}>Continue <ArrowRight size={16}/></button>:<button className="planner-primary" onClick={savePlan} disabled={saving}>{saving?<><Loader2 size={16} className="spin"/> Saving…</>:<>Save my plan <Check size={16}/></>}</button>}</div>}
            </div>

            <aside className="planner-aside">
              <div className="planner-aside-card planner-aside-dark"><div className="planner-aside-orbit"><Compass size={24}/></div><span>THE PREPCOMPASS APPROACH</span><h3>A plan that moves with you.</h3><p>Your goals, available time and progress come together in one personal preparation system.</p><div className="planner-aside-points"><div><CheckCircle2 size={15}/> Built around your exam targets</div><div><CheckCircle2 size={15}/> Realistic daily workload</div><div><CheckCircle2 size={15}/> Progress you can measure</div></div></div>
              <div className="planner-aside-card"><div className="planner-aside-small-icon"><Target size={17}/></div><b>One journey. Multiple exams.</b><p>Shared subjects can support more than one exam while each exam's unique syllabus stays visible.</p></div>
              <div className="planner-aside-card planner-trust"><ShieldCheck size={17}/><div><b>Your data stays yours</b><p>Your preparation profile is stored in your local PrepCompass database and isolated by account.</p></div></div>
              <div className="planner-aside-tip"><Sparkles size={15}/><span><b>Small tip</b><br/>Choose the time you can consistently protect, not the time you wish you had.</span></div>
            </aside>
          </div>
          <footer className="planner-footer">PREPCOMPASS <span>·</span> PLAN. PREPARE. PROGRESS.</footer>
        </div>
      </section>
    </main>
  );
}
