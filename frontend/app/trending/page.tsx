"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { TrendingUp, Star, BookOpen, GitFork, ArrowUpRight } from "lucide-react";
import { fetchTrendingPapers, fetchTrendingRepos, fetchTechRadar } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

export default function TrendingPage() {
  const [papers, setPapers] = useState<any[]>([]);
  const [repos, setRepos] = useState<any[]>([]);
  const [radar, setRadar] = useState<any>(null);
  const [tab, setTab] = useState<"papers" | "repos" | "radar">("papers");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchTrendingPapers({ limit: 20 }).catch(() => ({ items: [] })),
      fetchTrendingRepos({ limit: 20 }).catch(() => ({ items: [] })),
      fetchTechRadar().catch(() => null),
    ]).then(([p, r, t]) => {
      setPapers(p.items || []);
      setRepos(r.items || []);
      setRadar(t);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Trending</h1>
        <p className="mt-1 text-sm text-zinc-500">Hot papers, repositories, and technology radar</p>
      </div>

      <div className="flex gap-1 rounded-lg bg-zinc-900 p-1">
        {(["papers", "repos", "radar"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-300"
            }`}
          >
            {t === "papers" ? "Papers" : t === "repos" ? "Repositories" : "Tech Radar"}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-zinc-500">Loading...</p>}

      {!loading && tab === "papers" && (
        <div className="space-y-3">
          {papers.map((item: any, i: number) => (
            <Link
              key={item.id}
              href={`/papers/${item.id}`}
              className="flex items-start gap-4 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 transition-colors hover:border-zinc-700"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-sm font-bold text-zinc-400">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-white">{item.title}</h3>
                <div className="mt-1 flex items-center gap-3 text-xs text-zinc-500">
                  <span className="flex items-center gap-1 text-orange-400">
                    <TrendingUp size={12} /> {(item.trending_score || 0).toFixed(1)}
                  </span>
                  <span>Citations: {item.citation_count || 0}</span>
                  {item.primary_category && <span>{item.primary_category}</span>}
                </div>
              </div>
              <ArrowUpRight size={14} className="shrink-0 text-zinc-600" />
            </Link>
          ))}
          {papers.length === 0 && <p className="text-sm text-zinc-500">No trending papers yet.</p>}
        </div>
      )}

      {!loading && tab === "repos" && (
        <div className="space-y-3">
          {repos.map((item: any, i: number) => (
            <Link
              key={item.id}
              href={`/repos/${item.id}`}
              className="flex items-start gap-4 rounded-lg border border-zinc-800 bg-zinc-900/30 p-4 transition-colors hover:border-zinc-700"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-sm font-bold text-zinc-400">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <h3 className="font-medium text-blue-400">{item.full_name}</h3>
                {item.description && (
                  <p className="mt-0.5 text-sm text-zinc-400 line-clamp-1">{item.description}</p>
                )}
                <div className="mt-1 flex items-center gap-3 text-xs">
                  <span className="flex items-center gap-1 text-orange-400">
                    <TrendingUp size={12} /> {(item.trending_score || 0).toFixed(1)}
                  </span>
                  <span className="flex items-center gap-1 text-yellow-500">
                    <Star size={12} /> {formatNumber(item.stars_count || 0)}
                  </span>
                  <span className="flex items-center gap-1 text-zinc-500">
                    <GitFork size={12} /> {formatNumber(item.forks_count || 0)}
                  </span>
                  {item.primary_language && (
                    <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-zinc-400">
                      {item.primary_language}
                    </span>
                  )}
                </div>
              </div>
              <ArrowUpRight size={14} className="shrink-0 text-zinc-600" />
            </Link>
          ))}
          {repos.length === 0 && <p className="text-sm text-zinc-500">No trending repos yet.</p>}
        </div>
      )}

      {!loading && tab === "radar" && (
        <div className="space-y-4">
          {radar ? (
            <>
              {["adopt", "trial", "assess", "hold"].map((ring) => {
                const items = radar[ring] || [];
                if (items.length === 0) return null;
                return (
                  <div key={ring} className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
                    <h3 className="mb-3 text-sm font-semibold uppercase text-zinc-400">
                      {ring === "adopt" && "🟢"} {ring === "trial" && "🔵"}{" "}
                      {ring === "assess" && "🟡"} {ring === "hold" && "🔴"} {ring}
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {items.map((tech: any, i: number) => (
                        <span
                          key={i}
                          className="rounded-full border border-zinc-700 px-3 py-1 text-sm text-zinc-300"
                        >
                          {tech.name || tech}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </>
          ) : (
            <p className="text-sm text-zinc-500">Tech radar data not available yet.</p>
          )}
        </div>
      )}
    </div>
  );
}
