"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Star,
  GitFork,
  ExternalLink,
  RefreshCw,
  Download,
  LayoutGrid,
  List,
  ArrowUp,
  ArrowDown,
  Eye,
  AlertCircle,
  Search,
  BarChart3,
  Activity,
  TrendingUp,
  Database,
  Tag,
  X,
  ChevronRight,
  Check,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { fetchRepos, fetchRepoStats, fetchKnownTopics, triggerCollectRepos, triggerUpdateAllRepos } from "@/lib/api";
import { formatNumber } from "@/lib/utils";

type SortField = "stars_count" | "forks_count" | "watchers_count" | "open_issues_count" | "last_commit_at";
type ViewMode = "grid" | "table";
type PageTab = "overview" | "repos";

/* ── Pill button ── */
function Pill({
  active,
  onClick,
  children,
  variant = "blue",
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  variant?: "blue" | "purple";
}) {
  const colors = {
    blue: active
      ? "bg-primary/12 text-primary ring-1 ring-primary/20"
      : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
    purple: active
      ? "bg-[hsl(262_83%_58%/0.12)] text-[hsl(var(--accent))] ring-1 ring-[hsl(var(--accent)/0.2)]"
      : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
  };
  return (
    <button
      onClick={onClick}
      className={`rounded-xl px-3 py-1.5 text-[12px] font-medium transition-all duration-150 ${colors[variant]}`}
    >
      {children}
    </button>
  );
}

/* ── Modal for viewing all items ── */
function FilterModal({
  open,
  onClose,
  title,
  items,
  selected,
  onToggle,
  onClear,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  items: string[];
  selected: string[];
  onToggle: (item: string) => void;
  onClear: () => void;
}) {
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  if (!open) return null;

  const filtered = search
    ? items.filter((item) => item.toLowerCase().includes(search.toLowerCase()))
    : items;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 flex max-h-[80vh] w-full max-w-lg flex-col rounded-2xl border border-border bg-card shadow-soft-lg dark:shadow-soft-dark-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h3 className="text-[15px] font-semibold text-foreground">{title}</h3>
            <p className="mt-0.5 text-[12px] text-muted-foreground">
              {selected.length > 0
                ? `${selected.length} selected`
                : `${items.length} available`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>

        {/* Search */}
        <div className="border-b border-border px-5 py-3">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3 py-2 transition-all focus-within:border-[hsl(var(--accent)/0.4)] focus-within:ring-2 focus-within:ring-[hsl(var(--accent)/0.1)]">
            <Search size={14} className="shrink-0 text-muted-foreground/60" />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground/40 outline-none"
              autoFocus
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="text-[10px] text-muted-foreground transition-colors hover:text-foreground"
              >
                <X size={12} />
              </button>
            )}
          </div>
        </div>

        {/* Selected badges */}
        {selected.length > 0 && (
          <div className="flex flex-wrap gap-1.5 border-b border-border px-5 py-3">
            {selected.map((item) => (
              <span
                key={item}
                className="inline-flex items-center gap-1 rounded-lg bg-[hsl(262_83%_58%/0.12)] px-2 py-1 text-[11px] font-medium text-[hsl(var(--accent))] ring-1 ring-[hsl(var(--accent)/0.2)]"
              >
                {item}
                <button
                  onClick={() => onToggle(item)}
                  className="ml-0.5 rounded-full p-0.5 transition-colors hover:bg-[hsl(var(--accent)/0.15)]"
                >
                  <X size={10} />
                </button>
              </span>
            ))}
            <button
              onClick={onClear}
              className="rounded-lg px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              Clear all
            </button>
          </div>
        )}

        {/* List */}
        <div className="flex-1 overflow-y-auto px-2 py-2">
          {filtered.length === 0 && (
            <p className="px-3 py-6 text-center text-[13px] text-muted-foreground/60">
              No matching items
            </p>
          )}
          {filtered.map((item) => {
            const isSelected = selected.includes(item);
            return (
              <button
                key={item}
                onClick={() => onToggle(item)}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[13px] transition-all duration-100 ${
                  isSelected
                    ? "bg-[hsl(262_83%_58%/0.08)] text-[hsl(var(--accent))]"
                    : "text-foreground hover:bg-muted"
                }`}
              >
                <span
                  className={`flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-md border transition-all ${
                    isSelected
                      ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))] text-white"
                      : "border-border"
                  }`}
                >
                  {isSelected && <Check size={10} />}
                </span>
                <span className="flex-1 truncate">{item}</span>
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-3">
          <button
            onClick={onClose}
            className="rounded-xl bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground transition-all hover:opacity-90"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── Topic filter with search + multi-select ── */
function TopicFilter({
  topics,
  activeTopics,
  onToggle,
  onClear,
  label = "Topic",
}: {
  topics: string[];
  activeTopics: string[];
  onToggle: (t: string) => void;
  onClear: () => void;
  label?: string;
}) {
  const [topicSearch, setTopicSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const filtered = topicSearch
    ? topics.filter((t) => t.toLowerCase().includes(topicSearch.toLowerCase()))
    : topics.slice(0, 20);

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
          {label}
        </span>
        {topics.length > 20 && (
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-1 text-[11px] font-medium text-[hsl(var(--accent))] transition-colors hover:opacity-80"
          >
            View All ({topics.length}) <ChevronRight size={12} />
          </button>
        )}
      </div>

      {/* Selected badges */}
      {activeTopics.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {activeTopics.map((t) => (
            <span
              key={t}
              className="inline-flex items-center gap-1 rounded-lg bg-[hsl(262_83%_58%/0.12)] px-2.5 py-1 text-[12px] font-medium text-[hsl(var(--accent))] ring-1 ring-[hsl(var(--accent)/0.2)]"
            >
              {t}
              <button
                onClick={() => onToggle(t)}
                className="ml-0.5 rounded-full p-0.5 transition-colors hover:bg-[hsl(var(--accent)/0.15)]"
              >
                <X size={10} />
              </button>
            </span>
          ))}
          <button
            onClick={onClear}
            className="rounded-lg px-2 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            Clear
          </button>
        </div>
      )}

      {/* Topic search input */}
      <div className="flex items-center gap-2 rounded-xl border border-border bg-background px-3 py-1.5 transition-all focus-within:border-[hsl(var(--accent)/0.4)] focus-within:ring-2 focus-within:ring-[hsl(var(--accent)/0.1)]">
        <Search size={13} className="shrink-0 text-muted-foreground/60" />
        <input
          type="text"
          placeholder="Search topics..."
          value={topicSearch}
          onChange={(e) => setTopicSearch(e.target.value)}
          className="flex-1 bg-transparent text-[12px] text-foreground placeholder:text-muted-foreground/40 outline-none"
        />
        {topicSearch && (
          <button
            onClick={() => setTopicSearch("")}
            className="text-[10px] text-muted-foreground transition-colors hover:text-foreground"
          >
            &times;
          </button>
        )}
      </div>

      {/* Pills */}
      <div className="flex flex-wrap gap-2">
        {!topicSearch && (
          <Pill active={activeTopics.length === 0} onClick={onClear} variant="purple">
            All
          </Pill>
        )}
        {filtered.map((t) => (
          <Pill
            key={t}
            active={activeTopics.includes(t)}
            onClick={() => onToggle(t)}
            variant="purple"
          >
            {t}
          </Pill>
        ))}
        {topicSearch && filtered.length === 0 && (
          <span className="text-[12px] text-muted-foreground/60 py-1">No matching topics</span>
        )}
        {!topicSearch && topics.length > 20 && (
          <button
            onClick={() => setShowModal(true)}
            className="self-center text-[11px] font-medium text-[hsl(var(--accent))] transition-colors hover:opacity-80"
          >
            +{topics.length - 20} more
          </button>
        )}
      </div>

      <FilterModal
        open={showModal}
        onClose={() => setShowModal(false)}
        title="All Topics"
        items={topics}
        selected={activeTopics}
        onToggle={onToggle}
        onClear={onClear}
      />
    </div>
  );
}

export default function ReposPage() {
  const [repos, setRepos] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState("");
  const [topics, setTopics] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [collecting, setCollecting] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [sortBy, setSortBy] = useState<SortField>("stars_count");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [stats, setStats] = useState<any>(null);
  const [knownTopics, setKnownTopics] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<PageTab>("overview");
  const debounceRef = useRef<NodeJS.Timeout>();

  const pageSize = viewMode === "grid" ? 21 : 20;
  const topicParam = topics.length > 0 ? topics.join(",") : undefined;

  const toggleTopic = (t: string) => {
    setPage(0);
    setTopics((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  };

  const clearTopics = () => {
    setPage(0);
    setTopics([]);
  };

  useEffect(() => {
    fetchKnownTopics().then(setKnownTopics).catch(() => { });
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setSearchQuery(searchInput);
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  useEffect(() => {
    setLoading(true);
    fetchRepos({
      skip: page * pageSize,
      limit: pageSize,
      language: language || undefined,
      topic: topicParam,
      search: searchQuery || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
    })
      .then((data) => {
        setRepos(data.items || []);
        setTotal(data.total || 0);
      })
      .catch(() => { })
      .finally(() => setLoading(false));
  }, [page, language, topicParam, sortBy, sortOrder, searchQuery, pageSize]);

  useEffect(() => {
    fetchRepoStats({
      language: language || undefined,
      topic: topicParam,
      search: searchQuery || undefined,
    })
      .then(setStats)
      .catch(() => { });
  }, [language, topicParam, searchQuery]);

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
    setPage(0);
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return <span className="w-3" />;
    return sortOrder === "desc" ? <ArrowDown size={12} /> : <ArrowUp size={12} />;
  };

  const LANG_COLORS = [
    "#3b82f6", "#f59e0b", "#10b981", "#ef4444",
    "#8b5cf6", "#ec4899", "#06b6d4", "#f97316",
  ];

  const TOPIC_COLORS = [
    "#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444",
    "#10b981", "#ec4899", "#3b82f6", "#f97316",
    "#a855f7", "#14b8a6", "#eab308", "#fb923c",
  ];

  const langData = stats
    ? (() => {
      const entries = Object.entries(stats.language_distribution as Record<string, number>);
      const top8 = entries.slice(0, 8);
      const otherCount = entries.slice(8).reduce((sum, [, v]) => sum + v, 0);
      const data = top8.map(([name, value]) => ({ name, value }));
      if (otherCount > 0) data.push({ name: "Other", value: otherCount });
      return data;
    })()
    : [];

  const topicEntries = stats
    ? Object.entries(stats.topic_distribution as Record<string, number>)
    : [];

  const topicData = topicEntries.slice(0, 12).map(([name, value]) => ({ name, value }));

  const totalPages = Math.ceil(total / pageSize);

  const Pagination = () =>
    total > pageSize ? (
      <div className="flex items-center justify-between">
        <p className="text-[13px] text-muted-foreground">
          Showing {page * pageSize + 1}-{Math.min((page + 1) * pageSize, total)} of{" "}
          {formatNumber(total)}
        </p>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="rounded-xl border border-border px-4 py-2 text-[13px] font-medium text-foreground transition-all duration-150 hover:bg-muted disabled:opacity-40 disabled:hover:bg-transparent"
          >
            Previous
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) pageNum = i;
              else if (page < 3) pageNum = i;
              else if (page > totalPages - 4) pageNum = totalPages - 5 + i;
              else pageNum = page - 2 + i;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`flex h-8 w-8 items-center justify-center rounded-xl text-[13px] font-medium transition-all duration-150 ${page === pageNum
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                >
                  {pageNum + 1}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setPage(page + 1)}
            disabled={(page + 1) * pageSize >= total}
            className="rounded-xl border border-border px-4 py-2 text-[13px] font-medium text-foreground transition-all duration-150 hover:bg-muted disabled:opacity-40 disabled:hover:bg-transparent"
          >
            Next
          </button>
        </div>
      </div>
    ) : null;

  return (
    <div className="space-y-8">
      {/* ── Header ── */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tighter text-foreground">
            Repositories
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            {formatNumber(total)} repositories tracked
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={async () => {
              setCollecting(true);
              try { await triggerCollectRepos(); } catch { }
              finally { setCollecting(false); }
            }}
            disabled={collecting}
            className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-[13px] font-medium text-primary-foreground shadow-soft transition-all duration-150 hover:opacity-90 disabled:opacity-50 dark:shadow-soft-dark"
          >
            <Download size={14} />
            {collecting ? "Collecting..." : "Collect Repos"}
          </button>
          <button
            onClick={async () => {
              setUpdating(true);
              try { await triggerUpdateAllRepos(); } catch { }
              finally { setUpdating(false); }
            }}
            disabled={updating}
            className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-[13px] font-medium text-foreground shadow-soft transition-all duration-150 hover:bg-muted disabled:opacity-50 dark:shadow-soft-dark"
          >
            <RefreshCw size={14} className={updating ? "animate-spin" : ""} />
            {updating ? "Updating..." : "Update All"}
          </button>
        </div>
      </div>

      {/* ── Tab Switcher ── */}
      <div className="flex items-center gap-1 rounded-xl border border-border bg-muted/50 p-1">
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition-all duration-150 ${activeTab === "overview"
            ? "bg-card text-foreground shadow-soft dark:shadow-soft-dark"
            : "text-muted-foreground hover:text-foreground"
            }`}
        >
          <BarChart3 size={14} />
          Overview
        </button>
        <button
          onClick={() => setActiveTab("repos")}
          className={`flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition-all duration-150 ${activeTab === "repos"
            ? "bg-card text-foreground shadow-soft dark:shadow-soft-dark"
            : "text-muted-foreground hover:text-foreground"
            }`}
        >
          <Database size={14} />
          Repositories
        </button>
      </div>

      {/* ══════════════════════════════════════════════ */}
      {/* ── OVERVIEW TAB ── */}
      {/* ══════════════════════════════════════════════ */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Summary Cards */}
          {stats && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Database size={14} />
                  <span className="text-[11px] font-semibold uppercase tracking-widest">Total Repos</span>
                </div>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                  {formatNumber(stats.total_repos)}
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Star size={14} />
                  <span className="text-[11px] font-semibold uppercase tracking-widest">Total Stars</span>
                </div>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                  {formatNumber(stats.total_stars)}
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <TrendingUp size={14} />
                  <span className="text-[11px] font-semibold uppercase tracking-widest">Avg Stars</span>
                </div>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                  {formatNumber(Math.round(stats.avg_stars))}
                </p>
              </div>
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Activity size={14} />
                  <span className="text-[11px] font-semibold uppercase tracking-widest">Active Repos</span>
                </div>
                <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
                  {formatNumber(stats.active_repos)}
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">commits in 30d</p>
              </div>
            </div>
          )}

          {/* Charts */}
          {stats && (
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {/* Language Distribution Donut */}
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <h3 className="text-[13px] font-semibold text-foreground">Language Distribution</h3>
                {langData.length > 0 ? (
                  <div className="mt-4 flex items-center gap-4">
                    <div className="h-[220px] w-[220px] shrink-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={langData}
                            cx="50%"
                            cy="50%"
                            innerRadius={55}
                            outerRadius={85}
                            paddingAngle={2}
                            dataKey="value"
                          >
                            {langData.map((_, index) => (
                              <Cell key={index} fill={LANG_COLORS[index % LANG_COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip
                            contentStyle={{
                              backgroundColor: "hsl(var(--card))",
                              border: "1px solid hsl(var(--border))",
                              borderRadius: "12px",
                              fontSize: "12px",
                              color: "hsl(var(--foreground))",
                            }}
                            labelStyle={{ color: "hsl(var(--muted-foreground))" }}
                            formatter={(value: number) => [value, "Repos"]}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="flex flex-col gap-1.5 overflow-hidden">
                      {langData.map((item, index) => {
                        const langTotal = langData.reduce((s, d) => s + d.value, 0);
                        const pct = langTotal > 0 ? Math.round((item.value / langTotal) * 100) : 0;
                        return (
                          <div key={item.name} className="flex items-center gap-2 text-[12px]">
                            <span
                              className="h-2.5 w-2.5 shrink-0 rounded-full"
                              style={{ backgroundColor: LANG_COLORS[index % LANG_COLORS.length] }}
                            />
                            <span className="truncate text-foreground">{item.name}</span>
                            <span className="ml-auto tabular-nums text-muted-foreground">
                              {pct}%
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-[12px] text-muted-foreground">No language data</p>
                )}
              </div>

              {/* Topic Distribution Bar Chart */}
              <div className="rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
                <div className="flex items-center gap-2">
                  <Tag size={14} className="text-muted-foreground" />
                  <h3 className="text-[13px] font-semibold text-foreground">Topic Distribution</h3>
                </div>
                {topicData.length > 0 ? (
                  <div className="mt-4 h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={topicData}
                        layout="vertical"
                        margin={{ top: 0, right: 20, bottom: 0, left: 0 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 11 }}
                        />
                        <YAxis
                          type="category"
                          dataKey="name"
                          width={120}
                          tick={{ fontSize: 11 }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "hsl(var(--card))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "12px",
                            fontSize: "12px",
                            color: "hsl(var(--foreground))",
                          }}
                          labelStyle={{ color: "hsl(var(--muted-foreground))" }}
                          formatter={(value: number) => [value, "Repos"]}
                        />
                        <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                          {topicData.map((_, index) => (
                            <Cell key={index} fill={TOPIC_COLORS[index % TOPIC_COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <p className="mt-4 text-[12px] text-muted-foreground">No topic data</p>
                )}
              </div>
            </div>
          )}

          {/* Filters on overview tab */}
          <div className="space-y-5 rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
            <div className="space-y-2.5">
              <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Filter by Language
              </span>
              <div className="flex flex-wrap gap-2">
                <Pill active={language === ""} onClick={() => { setPage(0); setLanguage(""); }}>
                  All
                </Pill>
                {["Python", "JavaScript", "TypeScript", "Rust", "Go", "C++", "Java", "Julia"].map((lang) => (
                  <Pill
                    key={lang}
                    active={language === lang}
                    onClick={() => { setPage(0); setLanguage(language === lang ? "" : lang); }}
                  >
                    {lang}
                  </Pill>
                ))}
              </div>
            </div>
            <div className="border-t border-border" />
            <TopicFilter
              topics={knownTopics}
              activeTopics={topics}
              onToggle={toggleTopic}
              onClear={clearTopics}
              label="Filter by Topic"
            />
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════ */}
      {/* ── REPOSITORIES TAB ── */}
      {/* ══════════════════════════════════════════════ */}
      {activeTab === "repos" && (
        <div className="space-y-6">
          {/* ── Search ── */}
          <div className="flex items-center gap-3 rounded-2xl border border-border bg-card p-2 shadow-soft transition-all focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10 dark:shadow-soft-dark">
            <Search size={16} className="ml-3 shrink-0 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search repositories by name or description..."
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
                setPage(0);
              }}
              className="flex-1 bg-transparent py-2 text-[14px] text-foreground placeholder:text-muted-foreground/50 outline-none"
            />
            {searchInput && (
              <button
                onClick={() => { setSearchInput(""); setSearchQuery(""); setPage(0); }}
                className="rounded-xl px-3 py-1.5 text-[12px] font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              >
                Clear
              </button>
            )}
          </div>

          {/* ── Filters ── */}
          <div className="space-y-5 rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark">
            <div className="space-y-2.5">
              <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Language
              </span>
              <div className="flex flex-wrap gap-2">
                <Pill active={language === ""} onClick={() => { setPage(0); setLanguage(""); }}>
                  All
                </Pill>
                {["Python", "JavaScript", "TypeScript", "Rust", "Go", "C++", "Java", "Julia"].map((lang) => (
                  <Pill
                    key={lang}
                    active={language === lang}
                    onClick={() => { setPage(0); setLanguage(language === lang ? "" : lang); }}
                  >
                    {lang}
                  </Pill>
                ))}
              </div>
            </div>
            <div className="border-t border-border" />
            <TopicFilter
              topics={knownTopics}
              activeTopics={topics}
              onToggle={toggleTopic}
              onClear={clearTopics}
            />
          </div>

          {/* ── Toolbar ── */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 rounded-xl border border-border p-1">
              <button
                onClick={() => setViewMode("grid")}
                className={`flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150 ${viewMode === "grid"
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground"
                  }`}
                aria-label="Grid view"
              >
                <LayoutGrid size={15} />
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={`flex h-8 w-8 items-center justify-center rounded-lg transition-all duration-150 ${viewMode === "table"
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground"
                  }`}
                aria-label="Table view"
              >
                <List size={15} />
              </button>
            </div>
            <span className="text-[12px] text-muted-foreground">
              Sorted by <span className="font-medium text-foreground">{sortBy.replace(/_/g, " ")}</span> ({sortOrder})
            </span>
          </div>

          <Pagination />

          {/* ── Loading ── */}
          {loading && (
            <div className="flex items-center justify-center py-16">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
            </div>
          )}

          {/* ── Grid View ── */}
          {!loading && viewMode === "grid" && (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {repos.map((repo: any) => (
                <Link
                  key={repo.id}
                  href={`/repos/${repo.id}`}
                  className="group rounded-2xl border border-border bg-card p-5 shadow-soft transition-all duration-200 hover:shadow-soft-lg hover:border-primary/20 dark:shadow-soft-dark dark:hover:shadow-soft-dark-lg"
                >
                  <div className="flex items-start justify-between">
                    <h3 className="text-[14px] font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors duration-150">
                      {repo.full_name}
                    </h3>
                    <ExternalLink size={13} className="mt-0.5 shrink-0 text-muted-foreground/40 transition-colors group-hover:text-primary" />
                  </div>
                  {repo.description && (
                    <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground line-clamp-2">
                      {repo.description}
                    </p>
                  )}
                  <div className="mt-4 flex items-center gap-4 text-[12px]">
                    <span className="flex items-center gap-1 font-medium text-amber-500 dark:text-amber-400">
                      <Star size={12} /> {formatNumber(repo.stars_count)}
                    </span>
                    <span className="flex items-center gap-1 text-muted-foreground">
                      <GitFork size={12} /> {formatNumber(repo.forks_count)}
                    </span>
                    {repo.primary_language && (
                      <span className="rounded-lg bg-muted px-2 py-0.5 font-medium text-foreground">
                        {repo.primary_language}
                      </span>
                    )}
                  </div>
                  {repo.topics && repo.topics.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {repo.topics.slice(0, 4).map((t: string) => (
                        <span
                          key={t}
                          className="rounded-lg bg-[hsl(var(--accent)/0.08)] px-2 py-0.5 text-[10px] font-medium text-[hsl(var(--accent))]"
                        >
                          {t}
                        </span>
                      ))}
                      {repo.topics.length > 4 && (
                        <span className="px-1 text-[10px] text-muted-foreground">
                          +{repo.topics.length - 4}
                        </span>
                      )}
                    </div>
                  )}
                </Link>
              ))}
            </div>
          )}

          {/* ── Table View ── */}
          {!loading && viewMode === "table" && (
            <div className="overflow-hidden rounded-2xl border border-border shadow-soft dark:shadow-soft-dark">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Repository
                    </th>
                    <th className="px-5 py-3.5 text-left text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Lang
                    </th>
                    {(
                      [
                        { field: "stars_count" as SortField, icon: Star, label: "Stars" },
                        { field: "forks_count" as SortField, icon: GitFork, label: "Forks" },
                        { field: "watchers_count" as SortField, icon: Eye, label: "Watch" },
                        { field: "open_issues_count" as SortField, icon: AlertCircle, label: "Issues" },
                      ] as const
                    ).map(({ field, icon: Icon, label }) => (
                      <th
                        key={field}
                        className="cursor-pointer px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-widest text-muted-foreground transition-colors hover:text-foreground select-none"
                        onClick={() => handleSort(field)}
                      >
                        <span className="inline-flex items-center gap-1">
                          <Icon size={11} /> {label} <SortIcon field={field} />
                        </span>
                      </th>
                    ))}
                    <th
                      className="cursor-pointer px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-widest text-muted-foreground transition-colors hover:text-foreground select-none"
                      onClick={() => handleSort("last_commit_at")}
                    >
                      <span className="inline-flex items-center gap-1">
                        Commit <SortIcon field="last_commit_at" />
                      </span>
                    </th>
                    <th className="px-5 py-3.5 text-center text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Quality
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {repos.map((repo: any) => (
                    <tr
                      key={repo.id}
                      className="transition-colors duration-100 hover:bg-muted/30"
                    >
                      <td className="px-5 py-4">
                        <Link href={`/repos/${repo.id}`} className="block">
                          <span className="font-medium text-foreground hover:text-primary transition-colors duration-150">
                            {repo.full_name}
                          </span>
                          {repo.description && (
                            <p className="mt-0.5 text-[12px] text-muted-foreground line-clamp-1 max-w-lg">
                              {repo.description}
                            </p>
                          )}
                          {repo.topics && repo.topics.length > 0 && (
                            <div className="mt-1.5 flex flex-wrap gap-1">
                              {repo.topics.slice(0, 3).map((t: string) => (
                                <span
                                  key={t}
                                  className="rounded-lg bg-[hsl(var(--accent)/0.08)] px-1.5 py-0.5 text-[10px] font-medium text-[hsl(var(--accent))]"
                                >
                                  {t}
                                </span>
                              ))}
                              {repo.topics.length > 3 && (
                                <span className="text-[10px] text-muted-foreground">
                                  +{repo.topics.length - 3}
                                </span>
                              )}
                            </div>
                          )}
                        </Link>
                      </td>
                      <td className="px-5 py-4">
                        {repo.primary_language && (
                          <span className="rounded-lg bg-muted px-2 py-1 text-[11px] font-medium text-foreground">
                            {repo.primary_language}
                          </span>
                        )}
                      </td>
                      <td className="px-5 py-4 text-right font-medium tabular-nums text-amber-500 dark:text-amber-400">
                        {formatNumber(repo.stars_count)}
                      </td>
                      <td className="px-5 py-4 text-right tabular-nums text-muted-foreground">
                        {formatNumber(repo.forks_count)}
                      </td>
                      <td className="px-5 py-4 text-right tabular-nums text-muted-foreground">
                        {formatNumber(repo.watchers_count || 0)}
                      </td>
                      <td className="px-5 py-4 text-right tabular-nums text-muted-foreground">
                        {formatNumber(repo.open_issues_count)}
                      </td>
                      <td className="px-5 py-4 text-right text-[12px] text-muted-foreground">
                        {repo.last_commit_at
                          ? new Date(repo.last_commit_at).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                          })
                          : "-"}
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex items-center justify-center gap-1.5">
                          {repo.has_readme && (
                            <span className="rounded-lg bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600 dark:text-emerald-400">
                              README
                            </span>
                          )}
                          {repo.has_license && (
                            <span className="rounded-lg bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                              License
                            </span>
                          )}
                          {repo.has_docker && (
                            <span className="rounded-lg bg-cyan-500/10 px-1.5 py-0.5 text-[10px] font-medium text-cyan-600 dark:text-cyan-400">
                              Docker
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <Pagination />
        </div>
      )}
    </div>
  );
}
