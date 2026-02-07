"use client";

import { useEffect, useState } from "react";
import { FileText, Download, RefreshCw, TrendingUp, BookOpen, GitFork } from "lucide-react";
import { fetchWeeklyReport, fetchAlerts } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function ReportsPage() {
  const [report, setReport] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"report" | "alerts">("report");

  useEffect(() => {
    Promise.all([
      fetchWeeklyReport().catch(() => null),
      fetchAlerts({ limit: 20 }).catch(() => ({ items: [] })),
    ]).then(([r, a]) => {
      setReport(r);
      setAlerts(a.items || a || []);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Reports & Alerts</h1>
        <p className="mt-1 text-sm text-zinc-500">Weekly digests and research alerts</p>
      </div>

      <div className="flex gap-1 rounded-lg bg-zinc-900 p-1">
        {(["report", "alerts"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-300"
            }`}
          >
            {t === "report" ? "Weekly Report" : "Alerts"}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-zinc-500">Loading...</p>}

      {!loading && tab === "report" && (
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-6">
          {report ? (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText size={20} className="text-blue-500" />
                  <div>
                    <h2 className="text-lg font-semibold text-white">
                      {report.title || "Weekly Research Digest"}
                    </h2>
                    <p className="text-xs text-zinc-500">{formatDate(report.generated_at || report.created_at)}</p>
                  </div>
                </div>
              </div>

              {report.summary && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-zinc-500">Summary</h3>
                  <p className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-zinc-300">
                    {report.summary}
                  </p>
                </div>
              )}

              {report.highlights && report.highlights.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-zinc-500">Highlights</h3>
                  <ul className="mt-2 space-y-2">
                    {report.highlights.map((h: any, i: number) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                        <TrendingUp size={14} className="mt-0.5 shrink-0 text-green-500" />
                        <span>{typeof h === "string" ? h : h.text || h.title}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {report.top_papers && report.top_papers.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-zinc-500">Top Papers</h3>
                  <div className="mt-2 space-y-2">
                    {report.top_papers.map((p: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-zinc-300">
                        <BookOpen size={12} className="text-blue-400" />
                        {p.title || p}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {report.top_repos && report.top_repos.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-zinc-500">Top Repositories</h3>
                  <div className="mt-2 space-y-2">
                    {report.top_repos.map((r: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-sm text-zinc-300">
                        <GitFork size={12} className="text-green-400" />
                        {r.full_name || r}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {report.content && (
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase text-zinc-500">Full Report</h3>
                  <div className="prose prose-invert mt-2 max-w-none text-sm text-zinc-300">
                    <pre className="whitespace-pre-wrap rounded-md bg-zinc-800 p-4 text-xs">
                      {report.content}
                    </pre>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <FileText size={40} className="text-zinc-700" />
              <p className="mt-3 text-sm text-zinc-500">No weekly report available yet.</p>
              <p className="mt-1 text-xs text-zinc-600">
                Reports are generated automatically every Monday.
              </p>
            </div>
          )}
        </div>
      )}

      {!loading && tab === "alerts" && (
        <div className="space-y-3">
          {alerts.length > 0 ? (
            alerts.map((alert: any, i: number) => (
              <div
                key={alert.id || i}
                className={`rounded-lg border p-4 ${
                  alert.severity === "high"
                    ? "border-red-500/30 bg-red-500/5"
                    : alert.severity === "medium"
                    ? "border-yellow-500/30 bg-yellow-500/5"
                    : "border-zinc-800 bg-zinc-900/30"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">
                    {alert.title || alert.alert_type}
                  </span>
                  <span className="text-xs text-zinc-500">{formatDate(alert.created_at)}</span>
                </div>
                {alert.message && (
                  <p className="mt-1 text-sm text-zinc-400">{alert.message}</p>
                )}
              </div>
            ))
          ) : (
            <div className="flex flex-col items-center py-12 text-center">
              <RefreshCw size={40} className="text-zinc-700" />
              <p className="mt-3 text-sm text-zinc-500">No alerts yet.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
