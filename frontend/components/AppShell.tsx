"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity,
  BookOpen,
  CalendarDays,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Compass,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Settings,
  Sparkles,
  Sun,
  Timer,
  X,
  type LucideIcon,
} from "lucide-react";
import { logoutAccount } from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

type Props = {
  children: React.ReactNode;
  userName: string;
  title: string;
};

type NavigationItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const workspaceLinks: NavigationItem[] = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
];

const preparationLinks: NavigationItem[] = [
  { href: "/study-log", label: "Study log", icon: Timer },
  { href: "/planner", label: "Exam planner", icon: CalendarDays },
  { href: "/planner/daily", label: "Daily plan", icon: Activity },
  { href: "/syllabus", label: "Syllabus library", icon: BookOpen },
];

const insightLinks: NavigationItem[] = [
  { href: "/diagnostics", label: "AI diagnostics", icon: Sparkles },
];

const accountLinks: NavigationItem[] = [
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function AppShell({ children, userName, title }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [collapsed, setCollapsed] = useState(false);
  const [sidebarPreferenceLoaded, setSidebarPreferenceLoaded] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [preparationOpen, setPreparationOpen] = useState(true);
  const [collapsedGroupOpen, setCollapsedGroupOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(window.localStorage.getItem("prepcompass-sidebar-collapsed") === "true");
    } catch {
      // The sidebar remains expanded when storage is unavailable.
    }
    setSidebarPreferenceLoaded(true);
  }, []);

  useEffect(() => {
    if (!sidebarPreferenceLoaded) return;
    try {
      window.localStorage.setItem("prepcompass-sidebar-collapsed", String(collapsed));
    } catch {
      // The current session still keeps the selected sidebar state.
    }
  }, [collapsed, sidebarPreferenceLoaded]);

  useEffect(() => {
    setMobileOpen(false);
    setCollapsedGroupOpen(false);
  }, [pathname]);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobileOpen(false);
        setCollapsedGroupOpen(false);
      }
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  async function signOut() {
    setSigningOut(true);
    try {
      await logoutAccount();
    } finally {
      router.replace("/login");
      setSigningOut(false);
    }
  }

  const initials = userName.trim().slice(0, 1).toUpperCase() || "U";

  function renderLinks(items: NavigationItem[], compact: boolean, mobile: boolean) {
    return items.map(item => {
      const Icon = item.icon;
      const active = pathname === item.href;
      return (
        <Link
          key={item.href}
          href={item.href}
          title={compact ? item.label : undefined}
          aria-label={compact ? item.label : undefined}
          aria-current={active ? "page" : undefined}
          onClick={() => {
            if (mobile) setMobileOpen(false);
            setCollapsedGroupOpen(false);
          }}
          className={"pc-nav-link" + (active ? " active" : "")}
        >
          <Icon size={18} aria-hidden="true" />
          {!compact && <span>{item.label}</span>}
        </Link>
      );
    });
  }

  function renderSidebar(mobile = false) {
    const compact = collapsed && !mobile;
    const preparationExpanded = compact
      ? collapsedGroupOpen
      : preparationOpen;

    return (
      <div className={"pc-sidebar-inner" + (compact ? " is-compact" : "")}>
        <div className="pc-brand">
          <span className="pc-brand-mark"><Compass size={21} /></span>
          {!compact && (
            <span className="pc-brand-copy">
              <b>PrepCompass</b>
              <small>YOUR PREPARATION OS</small>
            </span>
          )}
          {mobile && (
            <button
              type="button"
              className="pc-mobile-close"
              onClick={() => setMobileOpen(false)}
              aria-label="Close navigation"
            >
              <X size={19} />
            </button>
          )}
        </div>

        <div className="pc-sidebar-scroll">
          <section className="pc-nav-section" aria-label="Workspace navigation">
            {!compact && <div className="pc-nav-caption">WORKSPACE</div>}
            {renderLinks(workspaceLinks, compact, mobile)}
          </section>

          <section className="pc-nav-section pc-preparation-section" aria-label="Preparation navigation">
            <button
              type="button"
              className={"pc-nav-group" + (preparationLinks.some(item => pathname === item.href) ? " has-active-child" : "")}
              onClick={() => {
                if (compact) {
                  setCollapsedGroupOpen(open => !open);
                } else {
                  setPreparationOpen(open => !open);
                }
              }}
              aria-expanded={preparationExpanded}
              aria-label={compact ? "Toggle preparation navigation" : undefined}
              title={compact ? "Preparation" : undefined}
            >
              <CalendarDays size={18} aria-hidden="true" />
              {!compact && <span>PREPARATION</span>}
              {preparationExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </button>

            {preparationExpanded && (
              <div className={compact ? "pc-nav-flyout" : "pc-nav-subnav"}>
                {compact && <div className="pc-nav-flyout-title">PREPARATION</div>}
                {renderLinks(preparationLinks, compact, mobile)}
              </div>
            )}
          </section>

          <section className="pc-nav-section" aria-label="Insights navigation">
            {!compact && <div className="pc-nav-caption pc-nav-caption-lower">INTELLIGENCE</div>}
            {renderLinks(insightLinks, compact, mobile)}
          </section>

          <section className="pc-nav-section" aria-label="Account navigation">
            {!compact && <div className="pc-nav-caption pc-nav-caption-lower">ACCOUNT</div>}
            {renderLinks(accountLinks, compact, mobile)}
          </section>
        </div>

        <div className="pc-sidebar-bottom">
          <div className="pc-user">
            <span className="pc-avatar">{initials}</span>
            {!compact && (
              <span className="pc-user-copy">
                <b>{userName}</b>
                <small>Personal workspace</small>
              </span>
            )}
          </div>
          <button
            type="button"
            className="pc-signout"
            onClick={signOut}
            disabled={signingOut}
            title={compact ? "Sign out" : undefined}
          >
            <LogOut size={17} aria-hidden="true" />
            {!compact && <span>{signingOut ? "Signing out…" : "Sign out"}</span>}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={"pc-layout" + (collapsed ? " pc-collapsed" : "")}>
      <aside className="pc-sidebar" aria-label="Main navigation">
        {renderSidebar()}
        <button
          type="button"
          className="pc-collapse"
          onClick={() => {
            setCollapsed(value => !value);
            setCollapsedGroupOpen(false);
          }}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-pressed={collapsed}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </aside>

      {mobileOpen && (
        <button
          type="button"
          className="pc-mobile-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {mobileOpen && (
        <aside className="pc-mobile-sidebar" aria-label="Mobile navigation" role="dialog" aria-modal="true">
          {renderSidebar(true)}
        </aside>
      )}

      <div className="pc-main">
        <header className="pc-topbar">
          <button
            type="button"
            className="pc-mobile-menu"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
            aria-expanded={mobileOpen}
          >
            <Menu size={20} />
          </button>

          <div className="pc-breadcrumb" aria-label={"Current page: " + title}>
            <span>PrepCompass</span>
            <ChevronRight size={14} aria-hidden="true" />
            <b>{title}</b>
          </div>

          <div className="pc-top-right">
            <button
              type="button"
              className="pc-theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              title={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
            >
              {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
              <span>{theme === "dark" ? "Light theme" : "Dark theme"}</span>
            </button>
            <span className="pc-local-status"><i /> LOCAL WORKSPACE</span>
            <span className="pc-top-avatar" aria-label={userName}>{initials}</span>
          </div>
        </header>

        <main className="pc-page-content">{children}</main>
      </div>
    </div>
  );
}
