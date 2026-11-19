"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  Activity, BookOpen, CalendarDays, ChevronDown, ChevronLeft, ChevronRight,
  Compass, LayoutDashboard, LogOut, Menu, Settings, Sparkles, Timer, X,
} from "lucide-react";
import { logoutAccount } from "@/lib/api";

type Props = { children: React.ReactNode; userName: string; title: string };

const links = [
  { href: "/", label: "Overview", icon: LayoutDashboard, group: "workspace" },
  { href: "/study-log", label: "Study log", icon: Timer, group: "study" },
  { href: "/planner", label: "Exam planner", icon: CalendarDays, group: "study" },
  { href: "/planner/daily", label: "Daily plan", icon: Activity, group: "study" },
  { href: "/syllabus", label: "Syllabus library", icon: BookOpen, group: "study" },
  { href: "/diagnostics", label: "AI diagnostics", icon: Sparkles, group: "insights" },
  { href: "/settings", label: "Settings", icon: Settings, group: "account" },
];

export default function AppShell({ children, userName, title }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [studyOpen, setStudyOpen] = useState(true);

  async function signOut() {
    try { await logoutAccount(); } finally { router.replace("/login"); }
  }

  const nav = (
    <>
      <div className="pc-brand">
        <span className="pc-brand-mark"><Compass size={21}/></span>
        {!collapsed && <span><b>PrepCompass</b><small>YOUR PREPARATION OS</small></span>}
      </div>
      {!collapsed && <div className="pc-nav-caption">WORKSPACE</div>}
      {links.filter(x => x.group === "workspace").map(item => {
        const Icon = item.icon;
        return <Link key={item.href} href={item.href} title={item.label} onClick={() => setMobileOpen(false)} className={"pc-nav-link " + (pathname === item.href ? "active" : "")}><Icon size={18}/>{!collapsed && <span>{item.label}</span>}</Link>;
      })}
      {!collapsed && <button className="pc-nav-group" onClick={() => setStudyOpen(v => !v)}><span>PREPARATION</span>{studyOpen ? <ChevronDown size={15}/> : <ChevronRight size={15}/>}</button>}
      {(collapsed || studyOpen) && links.filter(x => x.group === "study").map(item => {
        const Icon = item.icon;
        const active = pathname === item.href || (item.href === "/planner" && pathname.startsWith("/planner"));
        return <Link key={item.href} href={item.href} title={item.label} onClick={() => setMobileOpen(false)} className={"pc-nav-link " + (active ? "active" : "")}><Icon size={18}/>{!collapsed && <span>{item.label}</span>}</Link>;
      })}
      {!collapsed && <div className="pc-nav-caption pc-nav-caption-lower">INSIGHTS & ACCOUNT</div>}
      {links.filter(x => x.group === "insights" || x.group === "account").map(item => {
        const Icon = item.icon;
        return <Link key={item.href} href={item.href} title={item.label} onClick={() => setMobileOpen(false)} className={"pc-nav-link " + (pathname === item.href ? "active" : "")}><Icon size={18}/>{!collapsed && <span>{item.label}</span>}</Link>;
      })}
      <div className="pc-sidebar-bottom">
        <div className="pc-user"><span className="pc-avatar">{userName.slice(0,1).toUpperCase()}</span>{!collapsed && <span><b>{userName}</b><small>Personal workspace</small></span>}</div>
        <button className="pc-signout" onClick={signOut} title="Sign out"><LogOut size={17}/>{!collapsed && <span>Sign out</span>}</button>
      </div>
    </>
  );

  return <div className={"pc-layout " + (collapsed ? "pc-collapsed" : "")}>
    <aside className="pc-sidebar">{nav}<button className="pc-collapse" onClick={() => setCollapsed(v => !v)} aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}>{collapsed ? <ChevronRight size={16}/> : <ChevronLeft size={16}/>}</button></aside>
    {mobileOpen && <div className="pc-mobile-backdrop" onClick={() => setMobileOpen(false)}><button aria-label="Close navigation"><X size={20}/></button></div>}
    {mobileOpen && <aside className="pc-mobile-sidebar">{nav}</aside>}
    <div className="pc-main">
      <header className="pc-topbar"><button className="pc-mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div className="pc-breadcrumb">PrepCompass <ChevronRight size={14}/> <b>{title}</b></div><div className="pc-top-right"><span className="pc-local-status"><i/> LOCAL WORKSPACE</span><span className="pc-top-avatar">{userName.slice(0,1).toUpperCase()}</span></div></header>
      <main className="pc-page-content">{children}</main>
    </div>
  </div>;
}
