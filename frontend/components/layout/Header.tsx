"use client";

import { Search, Bell, Moon, Sun } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "@/components/ThemeProvider";

export default function Header() {
  const [query, setQuery] = useState("");
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/papers?q=${encodeURIComponent(query)}`);
    }
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 px-6">
      <form onSubmit={handleSearch} className="flex w-96 items-center gap-2">
        <div className="flex flex-1 items-center gap-2 rounded-md border border-zinc-300 bg-zinc-100 dark:border-zinc-800 dark:bg-zinc-900 px-3 py-1.5">
          <Search size={16} className="text-zinc-400 dark:text-zinc-500" />
          <input
            type="text"
            placeholder="Search papers, repos, topics..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm text-zinc-900 dark:text-white placeholder-zinc-400 dark:placeholder-zinc-500 outline-none"
          />
        </div>
      </form>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <div className="flex items-center gap-1.5 rounded-full border border-zinc-200 dark:border-zinc-800 p-0.5">
          <button
            onClick={() => theme !== "light" && toggleTheme()}
            className={`rounded-full p-1.5 transition-colors ${
              theme === "light"
                ? "bg-amber-100 text-amber-600"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            aria-label="Light mode"
          >
            <Sun size={14} />
          </button>
          <button
            onClick={() => theme !== "dark" && toggleTheme()}
            className={`rounded-full p-1.5 transition-colors ${
              theme === "dark"
                ? "bg-blue-500/20 text-blue-400"
                : "text-zinc-400 hover:text-zinc-600"
            }`}
            aria-label="Dark mode"
          >
            <Moon size={14} />
          </button>
        </div>

        <button className="relative rounded-md p-2 text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-white">
          <Bell size={18} />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-blue-500" />
        </button>
      </div>
    </header>
  );
}
