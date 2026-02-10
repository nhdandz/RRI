"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Search, X, ChevronLeft, ChevronRight, ExternalLink, Download,
  ThumbsUp, MessageSquare, Hash, Globe, BarChart3, TrendingUp,
  Share2, RefreshCw,
} from "lucide-react";
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  fetchCommunityPosts, fetchCommunityFilters, fetchCommunityStats,
  fetchCommunityKeywords, triggerCollectCommunity,
} from "@/lib/api";
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

type Tab = "overview" | "feed" | "hackernews" | "devto" | "mastodon" | "lemmy";

const PLATFORM_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  hackernews: { bg: "bg-orange-500/10", text: "text-orange-600 dark:text-orange-400", label: "Hacker News" },
  devto: { bg: "bg-blue-500/10", text: "text-blue-600 dark:text-blue-400", label: "Dev.to" },
  mastodon: { bg: "bg-purple-500/10", text: "text-purple-600 dark:text-purple-400", label: "Mastodon" },
  lemmy: { bg: "bg-green-500/10", text: "text-green-600 dark:text-green-400", label: "Lemmy" },
};

const LoadingSpinner = () => (
  <div className="flex items-center justify-center py-16">
    <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
  </div>
);

const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`rounded-2xl border border-border bg-card p-5 shadow-soft dark:shadow-soft-dark ${className}`}>{children}</div>
);

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
            <button key={p} onClick={() => onPageChange(p as number)}
              className={`flex h-8 w-8 items-center justify-center rounded-xl text-[13px] font-medium ${currentPage === p ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}>{(p as number) + 1}</button>
          )
        )}
        <button onClick={() => onPageChange(currentPage + 1)} disabled={currentPage >= totalPages - 1}
          className="rounded-xl border border-border px-3 py-2 text-foreground hover:bg-muted disabled:opacity-40"><ChevronRight size={14} /></button>
      </div>
    </div>
  );
}

function PlatformBadge({ platform }: { platform: string }) {
  const style = PLATFORM_STYLES[platform] || { bg: "bg-muted", text: "text-muted-foreground", label: platform };
  return (
    <span className={`rounded-lg px-2 py-0.5 text-[10px] font-medium ${style.bg} ${style.text}`}>
      {style.label}
    </span>
  );
}

function PostCard({ post }: { post: any }) {
  return (
    <a
      href={post.url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-start gap-4 rounded-2xl border border-border bg-card p-4 shadow-soft transition-all duration-200 hover:shadow-soft-lg hover:border-primary/20 dark:shadow-soft-dark dark:hover:shadow-soft-dark-lg"
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2 mb-1">
          <PlatformBadge platform={post.platform} />
          {post.published_at && (
            <span className="text-[11px] text-muted-foreground">
              {new Date(post.published_at).toLocaleDateString()}
            </span>
          )}
        </div>
        <h3 className="text-[14px] font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors line-clamp-2">
          {post.title || "(No title)"}
        </h3>
        {post.author && (
          <p className="mt-1 text-[12px] text-muted-foreground">by {post.author}</p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-3 text-[12px]">
          <span className="flex items-center gap-1 font-medium text-amber-500 dark:text-amber-400">
            <ThumbsUp size={12} /> {formatNumber(post.score)}
          </span>
          <span className="flex items-center gap-1 text-muted-foreground">
            <MessageSquare size={12} /> {post.comments_count}
          </span>
          {post.shares_count > 0 && (
            <span className="flex items-center gap-1 text-muted-foreground">
              <Share2 size={12} /> {post.shares_count}
            </span>
          )}
        </div>
        {post.tags && post.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {post.tags.slice(0, 5).map((tag: string) => (
              <span key={tag} className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">
                {tag}
              </span>
            ))}
            {post.tags.length > 5 && (
              <span className="text-[10px] text-muted-foreground">+{post.tags.length - 5}</span>
            )}
          </div>
        )}
      </div>
      <ExternalLink size={14} className="mt-1 shrink-0 text-muted-foreground/40 group-hover:text-primary" />
    </a>
  );
}

function PostList({ platform, sort = "score" }: { platform?: string; sort?: string }) {
  const [posts, setPosts] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState(sort);
  const debounceRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => setSearchQuery(searchInput), 400);
    return () => clearTimeout(debounceRef.current);
  }, [searchInput]);

  const loadPosts = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { skip: page * PAGE_SIZE, limit: PAGE_SIZE, sort: sortBy, sort_order: "desc" };
      if (platform) params.platform = platform;
      if (searchQuery) params.search = searchQuery;
      const data = await fetchCommunityPosts(params);
      setPosts(data.items || []);
      setTotal(data.total || 0);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, [page, platform, searchQuery, sortBy]);

  useEffect(() => { loadPosts(); }, [loadPosts]);

  useEffect(() => { setPage(0); }, [searchQuery, sortBy]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex flex-1 items-center gap-2 rounded-2xl border border-border bg-card px-4 py-2 shadow-soft focus-within:border-primary/40 focus-within:ring-2 focus-within:ring-primary/10 dark:shadow-soft-dark">
          <Search size={14} className="shrink-0 text-muted-foreground" />
          <input type="text" placeholder="Search posts..." value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="flex-1 bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground/50 outline-none" />
          {searchInput && (
            <button onClick={() => { setSearchInput(""); setSearchQuery(""); }}
              className="text-muted-foreground hover:text-foreground"><X size={14} /></button>
          )}
        </div>
        <div className="flex items-center gap-1 rounded-xl border border-border p-1">
          <button onClick={() => setSortBy("score")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium ${sortBy === "score" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            <ThumbsUp size={12} /> Score
          </button>
          <button onClick={() => setSortBy("published_at")}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[12px] font-medium ${sortBy === "published_at" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
            <TrendingUp size={12} /> Recent
          </button>
        </div>
        <span className="text-[12px] text-muted-foreground">{formatNumber(total)} posts</span>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && posts.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
          <Globe size={32} className="mb-3 opacity-40" />
          <p className="text-[13px]">No posts found.</p>
        </div>
      )}

      {!loading && posts.length > 0 && (
        <div className="space-y-3">
          {posts.map((post: any) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}

      {!loading && totalPages > 1 && (
        <Pagination currentPage={page} totalPages={totalPages} onPageChange={setPage} />
      )}
    </div>
  );
}

export default function CommunityPage() {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [stats, setStats] = useState<any>(null);
  const [keywords, setKeywords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchCommunityStats().catch(() => null),
      fetchCommunityKeywords({ limit: 20 }).catch(() => []),
    ]).then(([s, k]) => {
      setStats(s);
      setKeywords(k);
      setLoading(false);
    });
  }, []);

  const platformChartData = stats?.platform_counts
    ? Object.entries(stats.platform_counts as Record<string, number>)
        .sort((a, b) => (b[1] as number) - (a[1] as number))
        .map(([name, value]) => ({ name: PLATFORM_STYLES[name]?.label || name, value: value as number }))
    : [];

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "overview", label: "Overview", icon: <BarChart3 size={14} /> },
    { id: "feed", label: "Feed", icon: <Globe size={14} /> },
    { id: "hackernews", label: "Hacker News", icon: <Hash size={14} /> },
    { id: "devto", label: "Dev.to", icon: <Hash size={14} /> },
    { id: "mastodon", label: "Mastodon", icon: <Hash size={14} /> },
    { id: "lemmy", label: "Lemmy", icon: <Hash size={14} /> },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tighter text-foreground">Community</h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            AI & Tech discussions from Hacker News, Dev.to, Mastodon, and Lemmy
          </p>
        </div>
        <button
          onClick={async () => {
            setCollecting(true);
            try { await triggerCollectCommunity(); } finally { setCollecting(false); }
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
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 rounded-xl border border-border bg-muted/50 p-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex shrink-0 items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition-all ${
              activeTab === tab.id
                ? "bg-card text-foreground shadow-soft dark:shadow-soft-dark"
                : "text-muted-foreground hover:text-foreground"
            }`}>
            {tab.icon}{tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {loading && <LoadingSpinner />}
          {!loading && (
            <>
              {/* Stat cards */}
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Globe size={14} />
                    <span className="text-[11px] font-semibold uppercase tracking-widest">Total Posts</span>
                  </div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{formatNumber(stats?.total_posts || 0)}</p>
                </Card>
                <Card>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <ThumbsUp size={14} />
                    <span className="text-[11px] font-semibold uppercase tracking-widest">Avg Score</span>
                  </div>
                  <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{stats?.avg_score || 0}</p>
                </Card>
                {Object.entries((stats?.platform_counts || {}) as Record<string, number>).map(([platform, count]) => (
                  <Card key={platform}>
                    <div className="flex items-center gap-2">
                      <PlatformBadge platform={platform} />
                    </div>
                    <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{formatNumber(count)}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">posts</p>
                  </Card>
                ))}
              </div>

              {/* Charts */}
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                {/* Platform distribution */}
                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <BarChart3 size={14} className="text-muted-foreground" />
                    <h3 className="text-[13px] font-semibold text-foreground">Platform Distribution</h3>
                  </div>
                  {platformChartData.length > 0 ? (
                    <div className="flex items-center gap-4">
                      <div className="h-[220px] w-[220px] shrink-0">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={platformChartData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={2} dataKey="value">
                              {platformChartData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => [v, "Posts"]} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                      <div className="flex flex-col gap-1.5">
                        {platformChartData.map((item, i) => {
                          const t = platformChartData.reduce((s, d) => s + d.value, 0);
                          return (
                            <div key={item.name} className="flex items-center gap-2 text-[12px]">
                              <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }} />
                              <span className="text-foreground">{item.name}</span>
                              <span className="ml-auto tabular-nums text-muted-foreground">{t > 0 ? Math.round((item.value / t) * 100) : 0}%</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ) : <p className="text-[12px] text-muted-foreground">No data available</p>}
                </Card>

                {/* Keywords */}
                <Card>
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp size={14} className="text-muted-foreground" />
                    <h3 className="text-[13px] font-semibold text-foreground">Keyword Trends</h3>
                  </div>
                  {keywords.length > 0 ? (
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
                  ) : <p className="text-[12px] text-muted-foreground">No data available</p>}
                </Card>
              </div>

              {/* Browse by platform */}
              <Card>
                <div className="flex items-center gap-2 mb-4">
                  <Globe size={14} className="text-muted-foreground" />
                  <h3 className="text-[13px] font-semibold text-foreground">Browse by Platform</h3>
                </div>
                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  {(["hackernews", "devto", "mastodon", "lemmy"] as const).map((p) => {
                    const style = PLATFORM_STYLES[p];
                    const count = stats?.platform_counts?.[p] || 0;
                    return (
                      <button key={p} onClick={() => setActiveTab(p as Tab)}
                        className="flex items-center gap-3 rounded-xl border border-border p-4 transition-all hover:bg-muted/50 hover:border-primary/20">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${style.bg}`}>
                          <Hash size={16} className={style.text} />
                        </div>
                        <div className="text-left">
                          <p className="text-[13px] font-medium text-foreground">{style.label}</p>
                          <p className="text-[11px] text-muted-foreground">{formatNumber(count)} posts</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* Feed Tab */}
      {activeTab === "feed" && <PostList />}

      {/* Platform-specific tabs */}
      {activeTab === "hackernews" && <PostList platform="hackernews" />}
      {activeTab === "devto" && <PostList platform="devto" />}
      {activeTab === "mastodon" && <PostList platform="mastodon" />}
      {activeTab === "lemmy" && <PostList platform="lemmy" />}
    </div>
  );
}
