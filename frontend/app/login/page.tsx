"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Compass, ShieldCheck } from "lucide-react";
import { getCurrentUser, getGoogleOAuthConfig, googleSignInUrl, loginAccount, registerAccount } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("register");
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [googleEnabled, setGoogleEnabled] = useState(false);

  useEffect(() => {
    getCurrentUser().then(() => router.replace("/")).catch(() => undefined);
    getGoogleOAuthConfig().then(config => setGoogleEnabled(config.enabled)).catch(() => undefined);
  }, [router]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        await registerAccount({ email, display_name: displayName, password });
      } else {
        await loginAccount({ email, password });
      }
      router.replace("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not authenticate");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="pc-login-shell"><section className="pc-login-story"><div className="pc-login-logo"><span className="pc-brand-mark"><Compass size={21}/></span><span><b>PrepCompass</b><small>YOUR PREPARATION OS</small></span></div><div className="pc-login-message"><span className="pc-login-eyebrow">PLAN · PREPARE · PROGRESS</span><h1>Make every study hour <em>count.</em></h1><p>A calmer, clearer workspace for your civil services preparation. Bring your goals, study routine and progress into one place.</p><div className="pc-login-points"><span><i>✓</i> Plan for multiple examinations</span><span><i>✓</i> Track focused study sessions</span><span><i>✓</i> Learn from your preparation patterns</span></div></div><div className="pc-login-foot">BUILT FOR THE LONG GAME · YOUR JOURNEY, YOUR PACE</div></section><section className="pc-login-form-side">
      <section className="auth-card">
        <div className="auth-brand"><span className="auth-mark"><Compass size={25} /></span><div><strong>PrepCompass</strong><small>YOUR PREPARATION OS</small></div></div>
        <div className="auth-intro"><span className="auth-eyebrow">YOUR JOURNEY, IN FOCUS</span><h1>{mode === "register" ? "Create your workspace." : "Welcome back."}</h1><p>Your preparation records stay private to your account.</p></div>
        <div className="auth-tabs">
          <button type="button" className={mode === "register" ? "selected" : ""} onClick={() => { setMode("register"); setError(""); }}>Create account</button>
          <button type="button" className={mode === "login" ? "selected" : ""} onClick={() => { setMode("login"); setError(""); }}>Sign in</button>
        </div>
        <form className="auth-form" onSubmit={submit}>
          {mode === "register" && <label>YOUR NAME<input value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder="Your name" autoComplete="name" required maxLength={80} /></label>}
          <label>EMAIL ADDRESS<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required /></label>
          <label>PASSWORD<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder={mode === "register" ? "At least 10 characters" : "Your password"} autoComplete={mode === "register" ? "new-password" : "current-password"} minLength={mode === "register" ? 10 : 1} maxLength={128} required /></label>
          {error && <div className="auth-error" role="alert">{error}</div>}
          <button className="auth-submit" type="submit" disabled={busy}>{busy ? "Please wait…" : mode === "register" ? "Create my account" : "Sign in to PrepCompass"}</button>
        </form>
        {googleEnabled && <><div className="auth-divider"><span>OR</span></div>
        <a className="google-button" href={googleSignInUrl}>Continue with Google</a></>}
        <div className="auth-privacy"><ShieldCheck size={17} /><span>Each account has its own private study history. Google sign-in is optional.</span></div>
      </section>
      
    </main>
  );
}
