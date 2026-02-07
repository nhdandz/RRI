"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  FileText,
  GitBranch,
  TrendingUp,
  MessageSquare,
  BarChart3,
  Bell,
  Home,
  Search,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/papers", label: "Papers", icon: FileText },
  { href: "/repos", label: "Repositories", icon: GitBranch },
  { href: "/trending", label: "Trending", icon: TrendingUp },
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/reports", label: "Reports", icon: BarChart3 },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-zinc-200 dark:border-zinc-800 px-4">
        {!collapsed && (
          <span className="text-sm font-bold text-blue-500">OSINT Research</span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded p-1 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-2">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-blue-500/10 text-blue-500"
                  : "text-zinc-500 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/50 hover:text-zinc-900 dark:hover:text-white"
              )}
            >
              <Icon size={18} />
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-zinc-200 dark:border-zinc-800 p-2">
        <div className={cn("flex items-center gap-2 px-3 py-2 text-xs text-zinc-500", collapsed && "justify-center")}>
          <div className="h-2 w-2 rounded-full bg-green-500" />
          {!collapsed && <span>System Online</span>}
        </div>
      </div>
    </aside>
  );
}
