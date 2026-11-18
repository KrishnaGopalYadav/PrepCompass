"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, ArrowUpRight, BookOpen, CalendarDays, CheckCircle2, Clock3, Compass, GraduationCap, Plus, RefreshCw, Target, Timer, TrendingUp } from "lucide-react";
import { DashboardData, getDashboard, getCurrentUser, logoutAccount, saveStudySession, User } from "@/lib/api";

const subjects = ["General Studies", "Sociology", "Forestry", "Geology", "CSAT", "Current Affairs", "UPPSC-specific", "Essay", "Ethics"];

function minutesLabel(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours ? `${hours}h ${mins}m` : `${mins}m`;
}

export default function Home() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState("");
  const [subject, setSubject] = useState(subjects[0]);
  const [topic, setTopic] = useState("");
  const [duration, setDuration] = useState("60");
  const [notes, setNotes] = useState("");
  const [studiedOn, setStudiedOn] = useState(new Date().toLocaleDateString("en-CA"));

  const refresh = useCallback(async () => {
    try {
      setError("");
      const result = await getDashboard();
      setData(result);
    } catch {
      setError("Unable to connect to the PrepCompass API. Check that Docker services are running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => router.replace("/login")).finally(() => setAuthChecked(true));
  }, [router]);

  useEffect(() => { if (user) void refresh(); }, [user, refresh]);

  async function handleLogout() {
    try { await logoutAccount(); } finally { router.replace("/login"); }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!topic.trim()) return;
    setSaving(true);
    setNotice("");
    try {
      await saveStudySession({
        subject, topic: topic.trim(), duration_minutes: Number(duration),
        studied_on: studiedOn, notes,
      });
      setTopic("");
      setNotes("");
      setNotice("Study session saved to your local database.");
      await refresh();
    } catch (e) {
      setNotice(e instanceof Error ? e.message : "Could not save session.");
    } finally {
      setSaving(false);
    }
  }

  const todayPercent = data ? Math.min(100, Math.round(data.today.studied_minutes / data.today.goal_minutes * 100)) : 0;
  const weekPercent = data ? Math.min(100, Math.round(data.this_week.studied_minutes / data.this_week.goal_minutes * 100)) : 0;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Compass size={22} /></div><div><strong>PrepCompass</strong><span>YOUR PREPARATION OS</span></div></div>
        <div className="side-label">WORKSPACE</div>
        <a className="nav-item active" href="#overview"><Activity size={17} /> Overview</a>
        <a className="nav-item" href="#study-log"><Clock3 size={17} /> Study log <span className="soon">LIVE</span></a>
        <a className="nav-item muted" href="#roadmap"><BookOpen size={17} /> Syllabus tracker</a>
        <a className="nav-item muted" href="#roadmap"><CalendarDays size={17} /> Study planner</a>
        <a className="nav-item muted" href="#roadmap"><Target size={17} /> Tests & revision</a>
        <div className="sidebar-bottom"><div className="profile-chip"><div className="avatar">K</div><div><strong>{user.display_name}</strong><span>{user.email}</span></div></div><p>Your study records are private to your account.</p></div>
      </aside>

      <section className="main-panel">
        <header className="topbar"><div className="breadcrumb">Workspace <span>/</span> Overview</div><div className="top-actions"><span className="local-pill"><span /> LOCAL MODE</span><button className="icon-button" onClick={() => { setLoading(true); void refresh(); }} aria-label="Refresh dashboard"><RefreshCw size={17} /></button><div className="avatar small">{user.display_name.slice(0, 1).toUpperCase()}</div><button className="logout-button" onClick={handleLogout}>Sign out</button></div></header>
        <div className="content">
          <section className="welcome-row" id="overview"><div><div className="eyebrow">WEDNESDAY, 18 NOVEMBER 2026</div><h1>Your journey, <em>in focus.</em></h1><p>A little progress every day adds up to something extraordinary.</p></div><div className="target-tag"><Target size={17} /><span>MISSION 2028</span></div></section>

          <section className="exam-strip"><div className="exam-icon"><GraduationCap size={21} /></div><div className="exam-copy"><strong>Integrated Civil Services Preparation</strong><span>UPSC CSE · Indian Forest Service · UPPSC PCS · ACF/RFO</span></div><div className="exam-year">TARGET <b>2028</b></div></section>

          {error && <div className="alert">{error}</div>}

          <section className="stats-grid">
            <article className="stat-card"><div className="stat-top"><span>STUDY TIME TODAY</span><Clock3 size={17} /></div><div className="stat-number">{loading ? "—" : minutesLabel(data?.today.studied_minutes || 0)}</div><div className="progress-track"><div className="progress-fill teal" style={{ width: `${todayPercent}%` }} /></div><div className="stat-foot"><span>{todayPercent}% of daily goal</span><b>2h 30m goal</b></div></article>
            <article className="stat-card"><div className="stat-top"><span>THIS WEEK</span><CalendarDays size={17} /></div><div className="stat-number">{loading ? "—" : minutesLabel(data?.this_week.studied_minutes || 0)}</div><div className="progress-track"><div className="progress-fill blue" style={{ width: `${weekPercent}%` }} /></div><div className="stat-foot"><span>{weekPercent}% of weekly goal</span><b>17h 30m goal</b></div></article>
            <article className="stat-card"><div className="stat-top"><span>SESSIONS LOGGED</span><CheckCircle2 size={17} /></div><div className="stat-number">{loading ? "—" : data?.total_sessions ?? 0}</div><div className="stat-foot standalone"><span>Every session moves you forward.</span><TrendingUp size={15} /></div></article>
          </section>

          <div className="section-heading"><div><div className="eyebrow">MAKE TODAY COUNT</div><h2>Study workspace</h2></div><span className="section-note"><span className="live-dot" /> SAVED LOCALLY</span></div>
          <section className="workspace-grid" id="study-log">
            <article className="panel session-panel"><div className="panel-heading"><div className="panel-icon"><Timer size={18} /></div><div><h3>Log a study session</h3><p>Capture the work you put in today.</p></div></div>
              <form onSubmit={handleSubmit}>
                <label>SUBJECT<select value={subject} onChange={e => setSubject(e.target.value)}>{subjects.map(item => <option key={item}>{item}</option>)}</select></label>
                <label>TOPIC<input value={topic} onChange={e => setTopic(e.target.value)} placeholder="e.g. Fundamental Rights" required maxLength={200} /></label>
                <div className="form-row"><label>DURATION<select value={duration} onChange={e => setDuration(e.target.value)}><option value="25">25 minutes</option><option value="45">45 minutes</option><option value="60">1 hour</option><option value="90">1 hour 30 min</option><option value="120">2 hours</option><option value="150">2 hours 30 min</option></select></label><label>DATE<input type="date" value={studiedOn} onChange={e => setStudiedOn(e.target.value)} /></label></div>
                <label>NOTES <span className="optional">(OPTIONAL)</span><textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="What did you learn? Any doubts to revisit?" rows={2} /></label>
                <button className="primary-button" type="submit" disabled={saving}><Plus size={17} /> {saving ? "Saving..." : "Save study session"} <ArrowUpRight size={16} /></button>
                {notice && <p className="form-notice">{notice}</p>}
              </form>
            </article>

            <article className="panel recent-panel"><div className="panel-heading recent-heading"><div><div className="eyebrow">YOUR RECENT ACTIVITY</div><h3>Study history</h3></div><span className="count-badge">{data?.recent_sessions.length || 0}</span></div>
              {loading ? <div className="empty-state">Loading your activity…</div> : data?.recent_sessions.length ? <div className="session-list">{data.recent_sessions.map(session => <div className="session-item" key={session.id}><div className="session-subject-icon"><BookOpen size={17} /></div><div className="session-detail"><strong>{session.topic}</strong><span>{session.subject} · {session.studied_on}</span></div><b>{minutesLabel(session.duration_minutes)}</b></div>)}</div> : <div className="empty-state"><div className="empty-icon"><BookOpen size={23} /></div><strong>Your first session starts here.</strong><span>Log a study session to see your progress build over time.</span></div>}
              <div className="recent-footer"><span>Consistency over intensity.</span><span>KEEP GOING ↗</span></div>
            </article>
          </section>

          <section className="roadmap" id="roadmap"><div><div className="eyebrow">COMING INTO FOCUS</div><h2>Your preparation toolkit</h2><p>We're building your complete study command centre, one useful milestone at a time.</p></div><div className="roadmap-items"><div><BookOpen size={18}/><span><b>Syllabus tracker</b><small>Topic-wise completion</small></span><i>UP NEXT</i></div><div><CalendarDays size={18}/><span><b>Smart study planner</b><small>Daily and weekly targets</small></span></div><div><Target size={18}/><span><b>Tests & analytics</b><small>Find and fix weak areas</small></span></div></div></section>
          <footer>PREPCOMPASS <span>·</span> BUILT FOR THE LONG GAME <span>·</span> YOUR DATA, YOUR DEVICE</footer>
        </div>
      </section>
    </main>
  );
}
