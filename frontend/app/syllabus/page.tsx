"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, BookOpen, ExternalLink, FileCheck2, Filter, Info, Loader2, Save, ShieldCheck } from "lucide-react";
import { getCurrentUser, getOptionalSubjects, getPlannerOverview, getSyllabusCatalog, OptionalSubjectResponse, SyllabusNode, User, saveOptionalSubjects } from "@/lib/api";

const exams = [
  { id: "upsc_cse", label: "UPSC CSE" },
  { id: "upsc_ifos", label: "UPSC IFoS" },
  { id: "uppsc_pcs", label: "UPPSC PCS" },
  { id: "uppsc_acf_rfo", label: "UPPSC ACF/RFO" },
];

export default function SyllabusPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [examId, setExamId] = useState("upsc_cse");
  const [stage, setStage] = useState("all");
  const [items, setItems] = useState<SyllabusNode[]>([]);
  const [notice, setNotice] = useState("");
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [optional, setOptional] = useState<OptionalSubjectResponse | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [isTarget, setIsTarget] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  const load = useCallback(async () => {
    setCatalogLoading(true); setError(""); setSuccess("");
    try {
      const [catalog, overview] = await Promise.all([
        getSyllabusCatalog({ exam_id: examId, stage: stage === "all" ? undefined : stage }),
        getPlannerOverview(),
      ]);
      setItems(catalog.items);
      setNotice(catalog.notice);
      const target = overview.exam_targets.some(t => t.exam_id === examId);
      setIsTarget(target);
      if ((examId === "upsc_ifos" || examId === "uppsc_acf_rfo") && target) {
        const choices = await getOptionalSubjects(examId);
        setOptional(choices);
        setSelected(choices.selected);
      } else {
        setOptional(null); setSelected([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load syllabus catalogue");
    } finally { setCatalogLoading(false); }
  }, [examId, stage]);

  useEffect(() => { if (user) load(); }, [user, load]);

  const grouped = useMemo(() => {
    const groups = new Map<string, SyllabusNode[]>();
    for (const item of items) {
      const key = item.stage.toUpperCase();
      groups.set(key, [...(groups.get(key) ?? []), item]);
    }
    return Array.from(groups.entries());
  }, [items]);

  const requiredCount = optional?.required_count ?? (examId === "upsc_cse" ? 1 : 2);

  function toggleSubject(code: string) {
    setSelected(prev => prev.includes(code) ? prev.filter(x => x !== code) : prev.length < requiredCount ? [...prev, code] : prev);
  }

  async function saveSubjects() {
    setSaving(true); setError(""); setSuccess("");
    try {
      await saveOptionalSubjects(examId, selected);
      await load();
      setSuccess("Your optional subject choices have been saved to your private profile.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save optional subjects"); }
    finally { setSaving(false); }
  }

  if (!user) return <main className="planner-loading"><Loader2 className="spin" size={22}/> Loading syllabus…</main>;

  return <main className="syllabus-shell">
    <header className="syllabus-header">
      <Link href="/planner" className="daily-back"><ArrowLeft size={16}/> Exam planner</Link>
      <b>PrepCompass <span>SYLLABUS INTELLIGENCE</span></b>
    </header>
    <section className="syllabus-content">
      <div className="syllabus-intro">
        <div><div className="planner-kicker"><BookOpen size={13}/> SOURCE-LINKED EXAM OUTLINES</div>
          <h1>Know exactly <em>what to prepare.</em></h1>
          <p>Explore stage-wise paper outlines, official source documents and examination-specific optional subjects.</p></div>
        <Link href="/planner/daily">Daily study plan →</Link>
      </div>

      <div className="syllabus-filters">
        <label>EXAMINATION<select value={examId} onChange={e=>setExamId(e.target.value)}>{exams.map(e=><option key={e.id} value={e.id}>{e.label}</option>)}</select></label>
        <label>EXAM STAGE<select value={stage} onChange={e=>setStage(e.target.value)}><option value="all">All stages</option><option value="preliminary">Preliminary</option><option value="mains">Mains</option><option value="interview">Interview</option></select></label>
      </div>

      <div className="syllabus-alert"><AlertTriangle size={18}/><div><b>Historical source baseline — not yet a complete 2028 syllabus</b><p>{notice}</p></div></div>
      {error && <div className="planner-error" role="alert">{error}</div>}
      {success && <div className="daily-plan-notice">{success}</div>}

      {(examId === "upsc_cse" || examId === "upsc_ifos" || examId === "uppsc_acf_rfo") && <section className="optional-panel">
        <div className="optional-heading"><div><div className="planner-kicker"><ShieldCheck size={13}/> CANDIDATE PROFILE</div><h2>{requiredCount === 1 ? "Choose your optional subject" : "Choose your two optional subjects"}</h2><p>Selections are private to your account and checked against the source-cycle combination restrictions.</p></div><span>{selected.length}/{requiredCount} selected</span></div>
        {!isTarget ? <p className="optional-hint">Add this examination to your <Link href="/planner">exam planner</Link> before selecting optionals.</p> : optional && <>
          <div className="optional-grid">{optional.options.map(option=><button type="button" key={option.subject_code} onClick={()=>toggleSubject(option.subject_code)} className={selected.includes(option.subject_code)?"optional-choice active":"optional-choice"}><span>{selected.includes(option.subject_code)?"✓":""}</span>{option.subject_name}</button>)}</div>
          <div className="optional-foot"><small>{requiredCount === 1 ? "One subject is required." : "Two subjects are required."} Prohibited combinations are rejected by the server.</small><button className="planner-primary" disabled={saving||selected.length!==requiredCount} onClick={saveSubjects}>{saving?<Loader2 className="spin" size={15}/>:<Save size={15}/>} Save optional subjects</button></div>
          {optional.prohibited_combinations.length>0 && <details className="optional-rules"><summary>View prohibited combinations</summary><ul>{optional.prohibited_combinations.map((rule,i)=><li key={i}>{rule.subject_a.replaceAll("_"," ")} + {rule.subject_b.replaceAll("_"," ")} — {rule.reason}</li>)}</ul></details>}
        </>}
      </section>}

      {catalogLoading ? <div className="planner-loading"><Loader2 className="spin" size={22}/> Loading source-linked syllabus…</div> :
        grouped.length===0 ? <div className="syllabus-empty">No syllabus entries found for this filter.</div> :
        grouped.map(([name, nodes])=><section className="syllabus-stage" key={name}>
          <div className="syllabus-stage-title"><span>{name}</span><small>{nodes.length} catalogue entries</small></div>
          <div className="syllabus-node-list">{nodes.map(node=><article className="syllabus-node" key={node.node_id}>
            <div className="syllabus-node-icon">{node.node_type==="paper"?<FileCheck2 size={17}/>:<BookOpen size={17}/>}</div>
            <div className="syllabus-node-body"><div className="syllabus-node-meta">{node.paper_code} · {node.node_type.toUpperCase()} · SOURCE CYCLE {node.cycle_year}</div><h3>{node.title}</h3><p>{node.description}</p><small>{node.source_locator}</small></div>
            <a href={node.document_url} target="_blank" rel="noreferrer" aria-label="Open source document"><ExternalLink size={16}/></a>
          </article>)}</div>
          {nodes[0] && <div className="syllabus-source-line"><Info size={14}/><span>{nodes[0].source_title} · {nodes[0].verification_status.replaceAll("_"," ")}</span><a href={nodes[0].landing_url} target="_blank" rel="noreferrer">Publisher portal</a></div>}
        </section>)
      }
    </section>
  </main>;
}
