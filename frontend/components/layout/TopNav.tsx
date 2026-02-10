"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import {
  FileText,
  GitBranch,
  TrendingUp,
  MessageSquare,
  BarChart3,
  Home,
  Search,
  Moon,
  Sun,
  Bell,
  Command,
  LogIn,
  LogOut,
  Library,
  Box,
  Users,
  BookOpen,
  Compass,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/ThemeProvider";
import { useAuth } from "@/components/AuthProvider";

/* ── Nav structure ── */
const primaryNav = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/papers", label: "Papers", icon: FileText },
  { href: "/repos", label: "Repos", icon: GitBranch },
];

const exploreNav = [
  { href: "/trending", label: "Trending", icon: TrendingUp },
  { href: "/huggingface", label: "HuggingFace", icon: Box },
  { href: "/openreview", label: "OpenReview", icon: BookOpen },
  { href: "/community", label: "Community", icon: Users },
];

const toolsNav = [
  { href: "/chat", label: "AI Chat", icon: MessageSquare, authOnly: true },
  { href: "/reports", label: "Reports", icon: BarChart3 },
];

export default function TopNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [query, setQuery] = useState("");
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showExplore, setShowExplore] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const exploreRef = useRef<HTMLDivElement>(null);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(href));

  const isExploreActive = exploreNav.some((item) => isActive(item.href));

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
      if (
        exploreRef.current &&
        !exploreRef.current.contains(e.target as Node)
      ) {
        setShowExplore(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-[1440px] items-center px-6">
        {/* Logo */}
        <Link href="/" className="flex shrink-0 items-center gap-2.5 mr-6">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <Command size={14} className="text-primary-foreground" />
          </div>
          <span className="text-[15px] font-semibold tracking-tight text-foreground">
            RRI
          </span>
        </Link>

        {/* ── Navigation ── */}
        <nav className="flex items-center gap-0.5">
          {/* Primary: Dashboard, Papers, Repos */}
          {primaryNav.map(({ href, label, icon: Icon }) => {
            const active = isActive(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[13px] font-medium transition-all duration-150",
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
                <span>{label}</span>
              </Link>
            );
          })}

          {/* Separator */}
          <div className="mx-1.5 h-4 w-px bg-border" />

          {/* Explore dropdown */}
          <div className="relative" ref={exploreRef}>
            <button
              onClick={() => setShowExplore(!showExplore)}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[13px] font-medium transition-all duration-150",
                isExploreActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Compass size={15} strokeWidth={isExploreActive ? 2.2 : 1.8} />
              <span>Explore</span>
              <ChevronDown
                size={12}
                className={cn(
                  "transition-transform duration-200",
                  showExplore && "rotate-180"
                )}
              />
            </button>

            {showExplore && (
              <div className="absolute left-0 top-full mt-1.5 w-52 rounded-xl border border-border bg-card p-1.5 shadow-xl shadow-black/10 animate-in fade-in slide-in-from-top-1 duration-150">
                {exploreNav.map(({ href, label, icon: Icon }) => {
                  const active = isActive(href);
                  return (
                    <Link
                      key={href}
                      href={href}
                      onClick={() => setShowExplore(false)}
                      className={cn(
                        "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors",
                        active
                          ? "bg-primary/10 text-primary"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground"
                      )}
                    >
                      <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
                      <span>{label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Separator */}
          <div className="mx-1.5 h-4 w-px bg-border" />

          {/* Tools: AI Chat, Reports */}
          {toolsNav
            .filter((item) => !item.authOnly || user)
            .map(({ href, label, icon: Icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[13px] font-medium transition-all duration-150",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
                  <span>{label}</span>
                </Link>
              );
            })}
        </nav>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Search */}
        <form onSubmit={handleSearch} className="relative w-56">
          <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-1.5 transition-colors focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
            <Search size={14} className="shrink-0 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground/60 outline-none"
            />
            <kbd className="hidden shrink-0 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline-block">
              /
            </kbd>
          </div>
        </form>

        {/* ── Actions ── */}
        <div className="flex items-center gap-0.5 ml-4">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
          </button>

          {/* Notifications */}
          <button className="relative flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground">
            <Bell size={15} />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
          </button>

          {/* User / Auth */}
          {user ? (
            <div className="relative ml-1.5" ref={menuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 rounded-lg border border-border px-2.5 py-1.5 transition-colors hover:bg-muted"
              >
                <div className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/20 text-[10px] font-bold text-primary">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="text-[11px] font-medium text-foreground">
                  {user.username}
                </span>
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1.5 w-48 rounded-xl border border-border bg-card p-1.5 shadow-xl shadow-black/10 animate-in fade-in slide-in-from-top-1 duration-150">
                  <Link
                    href="/my-library"
                    onClick={() => setShowUserMenu(false)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-foreground transition-colors hover:bg-muted"
                  >
                    <Library size={14} />
                    My Library
                  </Link>
                  <button
                    onClick={() => {
                      setShowUserMenu(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] text-red-500 transition-colors hover:bg-red-500/10"
                  >
                    <LogOut size={14} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="ml-1.5 flex items-center gap-2 rounded-lg border border-border px-2.5 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-muted"
            >
              <LogIn size={14} />
              Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
