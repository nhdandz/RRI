"use client";

import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import {
  Search, X, Check, ChevronLeft, ChevronRight, Download, Heart,
  ExternalLink, LayoutGrid, List, ArrowDown, ArrowUp, TrendingUp,
  FileText, BarChart3, Tag, Cpu,
} from "lucide-react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from "recharts";
import { fetchHFModels, fetchHFPapers, fetchHFFilters, fetchHFStats, triggerCollectHFModels, triggerCollectHFPapers } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

const PAGE_SIZE = 20;
const CHART_COLORS = [
  "#3b82f6","#f59e0b","#10b981","#ef4444",
  "#8b5cf6","#ec4899","#06b6d4","#f97316","#a855f7","#14b8a6",
];
const tooltipStyle = {
  backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))",
  borderRadius: "12px", fontSize: "12px", color: "hsl(var(--foreground))",
};

type HFTab = "overview" | "models" | "papers";
type ViewMode = "grid" | "table";
type SortField = "downloads" | "likes";

/* ── Pill ── */
function Pill({ active, onClick, children }: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button onClick={onClick}
      className={`rounded-xl px-3 py-1.5 text-[12px] font-medium transition-all duration-150 ${
        active
          ? "bg-primary/12 text-primary ring-1 ring-primary/20"
          : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
      }`}>
      {children}
    </button>
  );
}

/* ── Filter Modal ── */
function FilterModal({ open, onClose, title, items, selected, onToggle, onClear }: {
  open: boolean; onClose: () => void; title: string; items: string[];
  selected: string[]; onToggle: (i: string) => void; onClear: () => void;
}) {
  const [search, setSearch] = useState("");
  useEffect(() => { if (!open) setSearch(""); }, [open]);
  if (!open) return null;
  const filtered = search ? items.filter((i) => i.toLowerCase().includes(search.toLowerCase())) : items;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 flex max-h-[80vh] w-full max-w-lg flex-col rounded-2xl border border-border bg-card shadow-soft-lg dark:shadow-soft-dark-lg">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h3 className="text-[15px] font-semibold text-foreground">{title}</h3>
            <p className="mt-0.5 text-[12px] text-muted-foreground">{selected.length > 0 ? `${selected.length} selected` : `${items.length} available`}</p>
          </div>
          <button onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"><X size={16} /></button>
        </div>
        <div className="border-b border-border px-5 py-3">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3 py-2 focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10">
            <Search size={14} className="shrink-0 text-muted-foreground/60" />
            <input type="text" placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)}
              className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground/40 outline-none" autoFocus />
            {search && <button onClick={() => setSearch("")} className="text-muted-foreground hover:text-foreground"><X size={12} /></button>}
          </div>
        </div>
        {selected.length > 0 && (
          <div className="flex flex-wrap gap-1.5 border-b border-border px-5 py-3">
            {selected.map((i) => (
              <span key={i} className="inline-flex items-center gap-1 rounded-lg bg-primary/10 px-2 py-1 text-[11px] font-medium text-primary ring-1 ring-primary/20">
                {i}<button onClick={() => onToggle(i)} className="ml-0.5 rounded-full p-0.5 hover:bg-primary/15"><X size={10} /></button>
              </span>
            ))}
            <button onClick={onClear} className="rounded-lg px-2 py-1 text-[11px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground">Clear all</button>
          </div>
        )}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          {filtered.length === 0 && <p className="px-3 py-6 text-center text-[13px] text-muted-foreground/60">No matching items</p>}
          {filtered.map((item) => {
            const sel = selected.includes(item);
            return (
              <button key={item} onClick={() => onToggle(item)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] transition-all ${sel ? "bg-primary/8 text-primary" : "text-foreground hover:bg-muted"}`}>
                <span className={`flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-md border ${sel ? "border-primary bg-primary text-white" : "border-border"}`}>{sel && <Check size={10} />}</span>
                <span className="flex-1 truncate">{item}</span>
              </button>
            );
          })}
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
          <button onClick={onClose} className="rounded-xl bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:opacity-90">Done</button>
        </div>
      </div>
    </div>
  );
}

/* ── Pagination ── */
function Pagination({ currentPage, totalPages, onPageChange }: {
  currentPage: number; totalPages: number; onPageChange: (page: number) => void;
}) {
  const getPageNumbers = () => {
    const pages: (number | "...")[] = [];
    if (totalPages <= 7) { for (let i = 0; i < totalPages; i++) pages.push(i); return pages; }
    pages.push(0);
    if (currentPage > 2) pages.push("...");
    for (let i = Math.max(1, currentPage - 1); i <= Math.min(totalPages - 2, currentPage + 1); i++) pages.push(i);
    if (currentPage < totalPages - 3) pages.push("...");
    pages.push(totalPages - 1);
    return pages;
  };
  return (
    <div className="flex items-center justify-between border-t border-border pt-4">
      <span className="text-[13px] text-muted-foreground">Page {currentPage + 1} of {totalPages}</span>
      <div className="flex items-center gap-1">
        <button onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 0}
          className="rounded-xl border border-border px-3 py-2 text-foreground hover:bg-muted disabled:opacity-40"><ChevronLeft size={14} /></button>
        {getPageNumbers().map((p, i) =>
          p === "..." ? (
            <span key={`e-${i}`} className="px-2 text-[12px] text-muted-foreground/60">...</span>
          ) : (
            <button key={p} onClick={() => onPageChange(p)}
              className={`flex h-8 w-8 items-center justify-center rounded-xl text-[13px] font-medium ${currentPage === p ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}>{(p as number) + 1}</button>
          )
        )}
        <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage >= totalPages - 1}
          className="rounded-xl border border-border px-3 py-2 text-foreground hover:bg-muted disabled:opacity-40"><ChevronRight size={14} /></button>
      </div>
    </div>
  );
}

/* ── Helpers ── */
const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-16"><div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" /></div>
);
const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark ${className}`}>{children}</div>
);

/* ══════════════════════════════════════════════ */
/* ── MAIN PAGE ── */
/* ══════════════════════════════════════════════ */
export default function HuggingFacePage() {
  const [activeTab, setActiveTab] = useState<HFTab>("overview");

  // Models state
  const [models, setModels] = useState<any[]>([]);
  const [modelsTotal, setModelsTotal] = useState(0);
  const [modelsPage, setModelsPage] = useState(0);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [sortBy, setSortBy] = useState<SortField>("downloads");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [pipelineTags, setPipelineTags] = useState<string[]>([]);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);
  const [showTagModal, setShowTagModal] = useState(false);
  const debounceRef = useRef<NodeJS.Timeout>();

  // Papers state
  const [papers, setPapers] = useState<any[]>([]);
  const [keywords, setKeywords] = useState<any[]>([]);
  const [papersLoading, setPapersLoading] = useState(false);
  const [papersLoaded, setPapersLoaded] = useState(false);

  // Overview: top models by downloads + likes for stat cards
  const [topByDownloads, setTopByDownloads] = useState<any[]>([]);
  const [topByLikes, setTopByLikes] = useState<any[]>([]);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [hfStats, setHfStats] = useState<any>(null);
  const [collecting, setCollecting] = useState(false);

  // Debounce search
  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearchQuery(searchInput), 400);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  // Load models
  const loadModels = useCallback(async (page: number, task?: string | null, search?: string, sort?: string) => {
    setModelsLoading(true);
    try {
      const params: any = { skip: page * PAGE_SIZE, limit: PAGE_SIZE, sort: sort || sortBy };
      if (task) params.task = task;
      if (search) params.search = search;
      const data = await fetchHFModels(params);
      setModels(data.items || []);
      setModelsTotal(data.total || 0);
      setModelsPage(page);
    } catch {
      setModels([]);
    } finally {
      setModelsLoading(false);
    }
  }, [sortBy]);

  // Initial load: models + filters + overview data + papers
  useEffect(() => {
    setOverviewLoading(true);
    Promise.all([
      fetchHFModels({ skip: 0, limit: PAGE_SIZE, sort: "downloads" }).catch(() => ({ items: [], total: 0 })),
      fetchHFFilters().catch(() => ({ pipeline_tags: [] })),
      fetchHFModels({ skip: 0, limit: 10, sort: "downloads" }).catch(() => ({ items: [] })),
      fetchHFModels({ skip: 0, limit: 10, sort: "likes" }).catch(() => ({ items: [] })),
      fetchHFPapers().catch(() => ({ papers: [], keyword_trends: [] })),
      fetchHFStats().catch(() => null),
    ]).then(([m, f, topDl, topLk, p, stats]) => {
      setModels(m.items || []);
      setModelsTotal(m.total || 0);
      setPipelineTags(f.pipeline_tags || []);
      setTopByDownloads(topDl.items || []);
      setTopByLikes(topLk.items || []);
      setPapers(p.papers || []);
      setKeywords(p.keyword_trends || []);
      setPapersLoaded(true);
      setHfStats(stats);
      setModelsLoading(false);
      setOverviewLoading(false);
    });
  }, []);

  // Reload when filters change
  useEffect(() => {
    loadModels(0, selectedTask, searchQuery || undefined, sortBy);
  }, [selectedTask, searchQuery, sortBy]); // eslint-disable-line react-hooks/exhaustive-deps

  const totalModelPages = Math.ceil(modelsTotal / PAGE_SIZE);

  const handleSort = (field: SortField) => {
    setSortBy(field);
    setModelsPage(0);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return <span className="w-3" />;
    return <ArrowDown size={12} />;
  };

  const visibleTags = pipelineTags.slice(0, 20);

  // Overview: pipeline tag distribution from stats or top models
  const pipelineDistribution = useMemo(() => {
    if (hfStats?.pipeline_distribution && Object.keys(hfStats.pipeline_distribution).length > 0) {
      return Object.entries(hfStats.pipeline_distribution as Record<string, number>)
        .sort((a, b) => (b[1] as number) - (a[1] as number))
        .slice(0, 8)
        .map(([name, value]) => ({ name, value: value as number }));
    }
    const counts: Record<string, number> = {};
    for (const m of topByDownloads) {
      const tag = m.pipeline_tag || "other";
      counts[tag] = (counts[tag] || 0) + 1;
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([name, value]) => ({ name, value }));
  }, [topByDownloads, hfStats]);

  // Overview: top models bar chart data
  const topModelsChart = useMemo(() => {
    return topByDownloads.slice(0, 8).map((m: any) => ({
      name: m.model_id?.length > 25 ? m.model_id.slice(0, 25) + "..." : m.model_id,
      downloads: m.downloads,
      likes: m.likes,
    }));
  }, [topByDownloads]);

  const totalDownloads = useMemo(() => topByDownloads.reduce((s: number, m: any) => s + (m.downloads || 0), 0), [topByDownloads]);
  const totalLikes = useMemo(() => topByLikes.reduce((s: number, m: any) => s + (m.likes || 0), 0), [topByLikes]);

  const tabs: { id: HFTab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Overview", icon: <BarChart3 size={14} /> },
    { id: "models", label: "Models", icon: <LayoutGrid size={14} /> },
    { id: "papers", label: "Daily Papers", icon: <FileText size={14} /> },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tighter text-foreground">HuggingFace</h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Explore models, papers, and trends from the HuggingFace ecosystem
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              setCollecting(true);
              try {
                await triggerCollectHFModels();
                await triggerCollectHFPapers();
              } finally {
                setCollecting(false);
              }
            }}
            disabled={collecting}
            className="flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-[13px] font-medium text-foreground shadow-soft hover:bg-muted disabled:opacity-50 dark:shadow-soft-dark"
          >
            {collecting ? (
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-muted border-t-primary" />
            ) : (
              <Download size={14} />
            )}
            Collect Data
          </button>
          <a
            href="https://huggingface.co"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 rounded-xl border border-border px-4 py-2.5 text-[13px] font-medium text-foreground shadow-soft hover:bg-muted dark:shadow-soft-dark"
          >
            <ExternalLink size={14} />
            huggingface.co
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-xl border border-border bg-muted/50 p-1">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition-all ${
              activeTab === tab.id
                ? "bg-card text-foreground shadow-soft dark:shadow-soft-dark"
                : "text-muted-foreground hover:text-foreground"
            }`}>
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* ══ OVERVIEW TAB ══ */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {overviewLoading && <LoadingSpinner />}
          {!overviewLoading && (
            <>
              {/* Stat cards */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground"><LayoutGrid size={14} /><span className="text-[11px] font-semibold uppercase tracking-widest">Models</span></div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{formatNumber(hfStats?.total_models || modelsTotal)}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">in database</p>
                </Card>
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground"><Cpu size={14} /><span className="text-[11px] font-semibold uppercase tracking-widest">Pipeline Tasks</span></div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{hfStats?.pipeline_distribution ? Object.keys(hfStats.pipeline_distribution).length : pipelineTags.length}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">categories</p>
                </Card>
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground"><Download size={14} /><span className="text-[11px] font-semibold uppercase tracking-widest">Total Downloads</span></div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{formatNumber(hfStats?.total_downloads || totalDownloads)}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">all models combined</p>
                </Card>
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground"><Heart size={14} /><span className="text-[11px] font-semibold uppercase tracking-widest">Total Likes</span></div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{formatNumber(hfStats?.total_likes || totalLikes)}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">all models combined</p>
                </Card>
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground"><FileText size={14} /><span className="text-[11px] font-semibold uppercase tracking-widest">Daily Papers</span></div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{papers.length}</p>
                  <p className="mt-0.5 text-[11px] text-muted-foreground">papers today</p>
                </Card>
              </div>

              {/* Charts row */}
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                {/* Pipeline tag distribution */}
                <Card>
                  <div className="flex items-center gap-2 mb-4"><Tag size={14} className="text-muted-foreground" /><h3 className="text-[13px] font-semibold text-foreground">Pipeline Task Distribution</h3></div>
                  {pipelineDistribution.length > 0 ? (
                    <div className="flex items-center gap-4">
                      <div className="h-[220px] w-[220px] shrink-0">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={pipelineDistribution} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={2} dataKey="value">
                              {pipelineDistribution.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [v, "Models"]} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex flex-col gap-1.5 overflow-hidden">
                        {pipelineDistribution.map((item, i) => {
                          const t = pipelineDistribution.reduce((s, d) => s + d.value, 0);
                          return (
                            <div key={item.name} className="flex items-center gap-2 text-[12px]">
                              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                              <span className="truncate text-foreground">{item.name}</span>
                              <span className="ml-auto tabular-nums text-muted-foreground">{t > 0 ? Math.round((item.value / t) * 100) : 0}%</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : <p className="text-[12px] text-muted-foreground">No data available</p>}
                </Card>

                {/* Top models by downloads */}
                <Card>
                  <div className="flex items-center gap-2 mb-4"><BarChart3 size={14} className="text-muted-foreground" /><h3 className="text-[13px] font-semibold text-foreground">Top Models by Downloads</h3></div>
                  {topModelsChart.length > 0 ? (
                    <div className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={topModelsChart} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 120 }}>
                          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                          <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => formatNumber(v)} />
                          <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={115} />
                          <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [formatNumber(v), "Downloads"]} />
                          <Bar dataKey="downloads" fill="#3b82f6" radius={[0, 6, 6, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : <p className="text-[12px] text-muted-foreground">No data available</p>}
                </Card>
              </div>

              {/* Top models by likes - horizontal bar */}
              <Card>
                <div className="flex items-center gap-2 mb-4"><Heart size={14} className="text-rose-500" /><h3 className="text-[13px] font-semibold text-foreground">Most Liked Models</h3></div>
                <div className="space-y-2">
                  {topByLikes.slice(0, 10).map((m: any, i: number) => {
                    const maxLikes = topByLikes[0]?.likes || 1;
                    return (
                      <a key={m.model_id} href={`https://huggingface.co/${m.model_id}`} target="_blank" rel="noopener noreferrer"
                        className="group flex items-center gap-3 rounded-xl px-3 py-2 transition-colors hover:bg-muted/50">
                        <span className="w-5 text-[12px] font-bold text-muted-foreground">{i + 1}</span>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center justify-between">
                            <span className="text-[13px] font-medium text-foreground group-hover:text-primary truncate">{m.model_id}</span>
                            <span className="ml-2 flex shrink-0 items-center gap-1 text-[12px] font-medium text-rose-500 dark:text-rose-400">
                              <Heart size={11} /> {formatNumber(m.likes)}
                            </span>
                          </div>
                          <div className="mt-1 h-1.5 rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full bg-rose-500/70 transition-all" style={{ width: `${(m.likes / maxLikes) * 100}%` }} />
                          </div>
                        </div>
                      </a>
                    );
                  })}
                </div>
              </Card>

              {/* Keyword trends from daily papers */}
              {keywords.length > 0 && (
                <Card>
                  <div className="flex items-center gap-2 mb-4"><TrendingUp size={14} className="text-muted-foreground" /><h3 className="text-[13px] font-semibold text-foreground">Today&apos;s Paper Keywords</h3></div>
                  <div className="flex flex-wrap gap-2">
                    {keywords.map((kw: any, i: number) => {
                      const mx = keywords[0]?.count || 1;
                      const r = kw.count / mx;
                      return (
                        <span key={kw.keyword} className="rounded-lg px-2.5 py-1 font-medium hover:opacity-80"
                          style={{ fontSize: `${11 + Math.round(r * 10)}px`, backgroundColor: `${CHART_COLORS[i % CHART_COLORS.length]}18`, color: CHART_COLORS[i % CHART_COLORS.length], opacity: 0.5 + r * 0.5 }}>
                          {kw.keyword}<span className="ml-1 text-[10px] opacity-60">{kw.count}</span>
                        </span>
                      );
                    })}
                  </div>
                </Card>
              )}

              {/* Pipeline tags browsing */}
              <Card>
                <div className="flex items-center gap-2 mb-4"><Cpu size={14} className="text-muted-foreground" /><h3 className="text-[13px] font-semibold text-foreground">Browse by Pipeline Task</h3></div>
                <div className="flex flex-wrap gap-2">
                  {pipelineTags.map((tag) => (
                    <button key={tag} onClick={() => { setSelectedTask(tag); setActiveTab("models"); }}
                      className="rounded-xl bg-muted px-3 py-1.5 text-[12px] font-medium text-muted-foreground transition-all hover:bg-primary/10 hover:text-primary">
                      {tag}
                    </button>
                  ))}
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ══ MODELS TAB ══ */}
      {activeTab === "models" && (
        <div className="space-y-6">
          {/* Search */}
          <div className="flex items-center gap-3 rounded-2xl border border-border bg-card p-2 shadow-soft focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10 dark:shadow-soft-dark">
            <Search size={16} className="ml-3 shrink-0 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search HuggingFace models..."
              value={searchInput}
              onChange={(e) => { setSearchInput(e.target.value); setModelsPage(0); }}
              className="flex-1 bg-transparent py-2 text-[14px] text-foreground placeholder:text-muted-foreground/50 outline-none"
            />
            {searchInput && (
              <button onClick={() => { setSearchInput(""); setSearchQuery(""); setModelsPage(0); }}
                className="rounded-xl px-3 py-1.5 text-[12px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground">Clear</button>
            )}
          </div>

          {/* Pipeline tag filter */}
          {pipelineTags.length > 0 && (
            <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Pipeline Task</span>
                {pipelineTags.length > 20 && (
                  <button onClick={() => setShowTagModal(true)} className="flex items-center gap-1 text-[11px] font-medium text-primary hover:opacity-80">
                    View All ({pipelineTags.length}) <ChevronRight size={12} />
                  </button>
                )}
              </div>
              <div className="mt-2.5 flex flex-wrap gap-2">
                <Pill active={!selectedTask} onClick={() => { setSelectedTask(null); setModelsPage(0); }}>All</Pill>
                {visibleTags.map((tag) => (
                  <Pill key={tag} active={selectedTask === tag}
                    onClick={() => { setSelectedTask(selectedTask === tag ? null : tag); setModelsPage(0); }}>
                    {tag}
                  </Pill>
                ))}
                {pipelineTags.length > 20 && (
                  <button onClick={() => setShowTagModal(true)} className="self-center text-[11px] font-medium text-primary hover:opacity-80">
                    +{pipelineTags.length - 20} more
                  </button>
                )}
              </div>
              <FilterModal
                open={showTagModal}
                onClose={() => setShowTagModal(false)}
                title="All Pipeline Tasks"
                items={pipelineTags}
                selected={selectedTask ? [selectedTask] : []}
                onToggle={(tag) => { setSelectedTask(selectedTask === tag ? null : tag); setModelsPage(0); }}
                onClear={() => { setSelectedTask(null); setModelsPage(0); }}
              />
            </div>
          )}

          {/* Controls: view mode + sort */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1 rounded-xl border border-border p-1">
                <button onClick={() => setViewMode("grid")}
                  className={`flex h-8 w-8 items-center justify-center rounded-lg ${viewMode === "grid" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                  <LayoutGrid size={15} />
                </button>
                <button onClick={() => setViewMode("table")}
                  className={`flex h-8 w-8 items-center justify-center rounded-lg ${viewMode === "table" ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                  <List size={15} />
                </button>
              </div>
              <div className="flex items-center gap-1 rounded-xl border border-border p-1">
                <button onClick={() => handleSort("downloads")}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium ${sortBy === "downloads" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                  <Download size={12} /> Downloads
                </button>
                <button onClick={() => handleSort("likes")}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium ${sortBy === "likes" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
                  <Heart size={12} /> Likes
                </button>
              </div>
            </div>
            <span className="text-[12px] text-muted-foreground">
              {formatNumber(modelsTotal)} models found
            </span>
          </div>

          {modelsLoading && <LoadingSpinner />}

          {/* Grid View */}
          {!modelsLoading && viewMode === "grid" && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {models.length === 0 && (
                <p className="col-span-full py-12 text-center text-sm text-muted-foreground">No models found.</p>
              )}
              {models.map((m: any, i: number) => {
                const author = m.model_id?.includes("/") ? m.model_id.split("/")[0] : null;
                return (
                  <a key={m.model_id} href={`https://huggingface.co/${m.model_id}`} target="_blank" rel="noopener noreferrer"
                    className="group rounded-2xl border border-border bg-card p-5 shadow-soft transition-all duration-200 hover:shadow-soft-lg hover:border-primary/20 dark:shadow-soft-dark dark:hover:shadow-soft-dark-lg">
                    <div className="flex items-start justify-between">
                      <h3 className="text-[14px] font-semibold tracking-tight text-foreground group-hover:text-primary line-clamp-1">{m.model_id}</h3>
                      <ExternalLink size={13} className="mt-0.5 shrink-0 text-muted-foreground/40 group-hover:text-primary" />
                    </div>
                    {author && <p className="mt-1 text-[12px] text-muted-foreground">by {author}</p>}
                    <div className="mt-3 flex items-center gap-4 text-[12px]">
                      <span className="flex items-center gap-1 font-medium text-blue-500 dark:text-blue-400">
                        <Download size={12} /> {formatNumber(m.downloads)}
                      </span>
                      <span className="flex items-center gap-1 font-medium text-rose-500 dark:text-rose-400">
                        <Heart size={12} /> {formatNumber(m.likes)}
                      </span>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {m.pipeline_tag && (
                        <span className="rounded-lg bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">{m.pipeline_tag}</span>
                      )}
                      {m.architecture && (
                        <span className="rounded-lg bg-muted px-2 py-0.5 text-[10px] font-medium text-foreground">{m.architecture}</span>
                      )}
                    </div>
                  </a>
                );
              })}
            </div>
          )}

          {/* Table View */}
          {!modelsLoading && viewMode === "table" && (
            <div className="overflow-hidden rounded-2xl border border-border shadow-soft dark:shadow-soft-dark">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground w-10">#</th>
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Model</th>
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Pipeline</th>
                    <th className="cursor-pointer px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-widest text-muted-foreground select-none" onClick={() => handleSort("downloads")}>
                      <span className="inline-flex items-center gap-1"><Download size={11} /> Downloads <SortIcon field="downloads" /></span>
                    </th>
                    <th className="cursor-pointer px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-widest text-muted-foreground select-none" onClick={() => handleSort("likes")}>
                      <span className="inline-flex items-center gap-1"><Heart size={11} /> Likes <SortIcon field="likes" /></span>
                    </th>
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">Architecture</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {models.length === 0 && (
                    <tr><td colSpan={6} className="px-5 py-12 text-center text-sm text-muted-foreground">No models found.</td></tr>
                  )}
                  {models.map((m: any, i: number) => (
                    <tr key={m.model_id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-5 py-3 text-muted-foreground">{modelsPage * PAGE_SIZE + i + 1}</td>
                      <td className="px-5 py-3">
                        <a href={`https://huggingface.co/${m.model_id}`} target="_blank" rel="noopener noreferrer"
                          className="font-medium text-foreground hover:text-primary">{m.model_id}</a>
                      </td>
                      <td className="px-5 py-3">
                        {m.pipeline_tag ? (
                          <span className="rounded-lg bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">{m.pipeline_tag}</span>
                        ) : <span className="text-muted-foreground">-</span>}
                      </td>
                      <td className="px-5 py-3 text-right font-medium tabular-nums text-blue-500 dark:text-blue-400">{formatNumber(m.downloads)}</td>
                      <td className="px-5 py-3 text-right font-medium tabular-nums text-rose-500 dark:text-rose-400">{formatNumber(m.likes)}</td>
                      <td className="px-5 py-3">
                        {m.architecture ? (
                          <span className="rounded-lg bg-muted px-1.5 py-0.5 text-[10px] font-medium text-foreground">{m.architecture}</span>
                        ) : <span className="text-muted-foreground">-</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!modelsLoading && totalModelPages > 1 && (
            <Pagination currentPage={modelsPage} totalPages={totalModelPages}
              onPageChange={(p) => loadModels(p, selectedTask, searchQuery || undefined, sortBy)} />
          )}
        </div>
      )}

      {/* ══ DAILY PAPERS TAB ══ */}
      {activeTab === "papers" && (
        <div className="space-y-6">
          {overviewLoading && <LoadingSpinner />}

          {!overviewLoading && papers.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
              <FileText size={32} className="mb-3 opacity-40" />
              <p className="text-[13px]">No daily papers available.</p>
            </div>
          )}

          {!overviewLoading && papers.length > 0 && (
            <>
              <div className="space-y-3">
                {papers.map((p: any, i: number) => (
                  <a key={p.arxiv_id || i}
                    href={p.arxiv_id ? `https://arxiv.org/abs/${p.arxiv_id}` : "#"}
                    target="_blank" rel="noopener noreferrer"
                    className="group flex items-start gap-4 rounded-2xl border border-border bg-card p-4 shadow-soft transition-all duration-200 hover:shadow-soft-lg hover:border-primary/20 dark:shadow-soft-dark dark:hover:shadow-soft-dark-lg">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-bold text-muted-foreground">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-[14px] font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors duration-150">
                        {p.title}
                      </h3>
                      <div className="mt-1.5 flex flex-wrap items-center gap-3 text-[12px]">
                        <span className="flex items-center gap-1 font-medium text-amber-500 dark:text-amber-400">
                          <TrendingUp size={12} /> {p.upvotes} upvotes
                        </span>
                        {p.authors?.length > 0 && (
                          <span className="text-muted-foreground line-clamp-1">
                            {p.authors.slice(0, 3).join(", ")}{p.authors.length > 3 ? ` +${p.authors.length - 3}` : ""}
                          </span>
                        )}
                        {p.arxiv_id && (
                          <span className="rounded-lg bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-medium text-blue-600 dark:text-blue-400">
                            arxiv:{p.arxiv_id}
                          </span>
                        )}
                      </div>
                    </div>
                    <ExternalLink size={14} className="shrink-0 text-muted-foreground/40 transition-colors group-hover:text-primary" />
                  </a>
                ))}
              </div>

              {/* Keyword Trends */}
              {keywords.length > 0 && (
                <div className="space-y-4">
                  <h2 className="text-lg font-semibold text-foreground">Keyword Trends</h2>
                  <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                    <div className="flex flex-wrap gap-2">
                      {keywords.map((kw: any) => (
                        <span key={kw.keyword}
                          className="inline-flex items-center gap-1.5 rounded-xl bg-primary/8 px-3 py-1.5 text-[12px] font-medium text-primary ring-1 ring-primary/15">
                          {kw.keyword}
                          <span className="rounded-md bg-primary/15 px-1.5 py-0.5 text-[10px] font-bold">{kw.count}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
