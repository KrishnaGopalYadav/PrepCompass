"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Monitor, Moon, ShieldCheck, Sun, UserRound } from "lucide-react";
import AppShell from "@/components/AppShell";
import { useTheme, type Theme } from "@/components/ThemeProvider";
import { getCurrentUser, type User } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  if (!user) return <main className="auth-loading">Loading account…</main>;

  const choices: { value: Theme; label: string; description: string; icon: typeof Sun }[] = [
    { value: "light", label: "Light", description: "Bright surfaces and subtle borders", icon: Sun },
    { value: "dark", label: "Dark", description: "Low-glare surfaces for focused sessions", icon: Moon },
  ];

  return (
    <AppShell userName={user.display_name} title="Settings">
      <div className="pc-page-heading">
        <div><div className="pc-kicker">ACCOUNT & PREFERENCES</div><h1>Settings</h1><p>Manage your workspace appearance, account and privacy information.</p></div>
      </div>
      <div className="pc-settings-grid">
        <section className="pc-panel">
          <div className="pc-settings-heading"><span className="pc-action-icon"><Monitor size={19} /></span><div><h2>Appearance</h2><p>Choose how PrepCompass looks on this device.</p></div></div>
          <div className="pc-theme-choices" role="group" aria-label="Color theme">
            {choices.map(choice => {
              const Icon = choice.icon;
              const selected = theme === choice.value;
              return <button type="button" key={choice.value} className={"pc-theme-choice" + (selected ? " selected" : "")} onClick={() => setTheme(choice.value)} aria-pressed={selected}>
                <span className="pc-theme-choice-icon"><Icon size={19} /></span><span><b>{choice.label}</b><small>{choice.description}</small></span><span className="pc-theme-radio" aria-hidden="true">{selected ? "✓" : ""}</span>
              </button>;
            })}
          </div>
          <p className="pc-settings-note">Your theme preference is saved in this browser and applied across PrepCompass pages.</p>
        </section>
        <section className="pc-panel">
          <div className="pc-settings-heading"><span className="pc-action-icon"><UserRound size={19} /></span><div><h2>Account profile</h2><p>Your signed-in account information.</p></div></div>
          <div className="pc-account-detail"><span>DISPLAY NAME</span><b>{user.display_name}</b></div>
          <div className="pc-account-detail"><span>EMAIL ADDRESS</span><b>{user.email}</b></div>
          <details className="pc-disclosure"><summary><span className="pc-disclosure-label"><ShieldCheck size={17} /> Privacy & local data</span></summary><div className="pc-disclosure-content">Study sessions, planner settings and diagnostics are associated with your account. Keep your device and database backups secure.</div></details>
        </section>
      </div>
    </AppShell>
  );
}
