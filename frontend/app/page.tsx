"use client";

import { FileText, GitBranch, TrendingUp, Zap, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { fetchPapers, fetchRepos } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/utils";

function StatCard({ icon: Icon, label, value, href }: any) {
  return (
    <Link
      href={href}
      className="group relative rounded-2xl border border-border bg-card p-6 shadow-soft transition-all duration-200 hover:shadow-soft-lg hover:border-primary/20 dark:shadow-soft-dark dark:hover:shadow-soft-dark-lg"
    >
      <div className="flex items-center justify-between">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
          <Icon size={18} className="text-primary" />
        </div>
        <ArrowUpRight
          size={16}
          className="text-muted-foreground/40 transition-all duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-primary"
        />
      </div>
      <div className="mt-5">
        <p className="text-3xl font-semibold tracking-tighter text-foreground">{value}</p>
        <p className="mt-1 text-[13px] text-muted-foreground">{label}</p>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState({ papers: 0, repos: 0, trending: 0 });
  const [recentPapers, setRecentPapers] = useState<any[]>([]);

  useEffect(() => {
    fetchPapers({ limit: 5 })
      .then((d) => {
        setStats((s) => ({ ...s, papers: d.total || 0 }));
        setRecentPapers(d.items || []);
      })
      .catch(() => {});

    fetchRepos({ limit: 1 })
      .then((d) => {
        setStats((s) => ({ ...s, repos: d.total || 0 }));
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-semibold tracking-tighter text-foreground">
          Dashboard
        </h1>
        <p className="mt-2 text-[15px] text-muted-foreground">
          Overview of your research intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={FileText} label="Total Papers" value={formatNumber(stats.papers)} href="/papers" />
        <StatCard icon={GitBranch} label="Repositories" value={formatNumber(stats.repos)} href="/repos" />
        <StatCard icon={TrendingUp} label="Trending" value={formatNumber(stats.trending)} href="/trending" />
        <StatCard icon={Zap} label="Alerts" value="0" href="/reports" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h2 className="text-lg font-semibold tracking-tighter text-foreground">
            Recent Papers
          </h2>
          <div className="mt-5 space-y-2">
            {recentPapers.length === 0 && (
              <p className="py-8 text-center text-[13px] text-muted-foreground">
                No papers collected yet. Start the collection jobs.
              </p>
            )}
            {recentPapers.map((paper: any) => (
              <Link
                key={paper.id}
                href={`/papers/${paper.id}`}
                className="block rounded-xl border border-border p-4 transition-all duration-150 hover:bg-muted/50 hover:border-primary/20"
              >
                <p className="text-[13px] font-medium leading-snug text-foreground line-clamp-1">
                  {paper.title}
                </p>
                <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span>{formatDate(paper.published_date)}</span>
                  {paper.categories?.length > 0 && (
                    <span className="rounded-lg bg-muted px-2 py-0.5 font-medium">
                      {paper.categories[0]}
                    </span>
                  )}
                  <span>{paper.citation_count} citations</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h2 className="text-lg font-semibold tracking-tighter text-foreground">
            Quick Actions
          </h2>
          <div className="mt-5 grid grid-cols-2 gap-3">
            {[
              { href: "/chat", title: "Ask AI", desc: "Query research knowledge" },
              { href: "/trending", title: "View Trending", desc: "Papers & repos" },
              { href: "/papers", title: "Browse Papers", desc: "Latest research" },
              { href: "/reports", title: "Weekly Report", desc: "Research digest" },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group rounded-xl border border-border p-5 text-center transition-all duration-150 hover:border-primary/30 hover:bg-primary/5 hover:shadow-glow"
              >
                <p className="text-[13px] font-semibold text-foreground">{item.title}</p>
                <p className="mt-1 text-[11px] text-muted-foreground">{item.desc}</p>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
