"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ArrowLeft, ExternalLink, BookOpen, GitBranch, Bookmark, Quote, Users, Calendar } from "lucide-react";
import Link from "next/link";
import { fetchPaper } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";
import { BookmarkDialog } from "@/components/BookmarkDialog";

export default function PaperDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [paper, setPaper] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showBookmark, setShowBookmark] = useState(false);

  useEffect(() => {
    if (id) {
      fetchPaper(id as string)
        .then((data) => setPaper(data))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading)
    return (
      <div className="flex items-center justify-center py-32">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-muted border-t-primary" />
      </div>
    );

  if (!paper)
    return (
      <div className="py-32 text-center text-[15px] text-muted-foreground">
        Paper not found.
      </div>
    );

  const p = paper.paper || paper;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Back */}
      <Link
        href="/papers"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft size={14} /> Back to papers
      </Link>

      {/* Hero card */}
      <div className="rounded-2xl border border-border bg-card p-8 shadow-soft dark:shadow-soft-dark">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex items-start gap-3">
              <BookOpen size={20} className="mt-1 shrink-0 text-primary" />
              <div>
                <h1 className="text-2xl font-semibold tracking-tighter text-foreground">
                  {p.title}
                </h1>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-[13px]">
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <Calendar size={13} /> {formatDate(p.published_date)}
                  </span>
                  {p.arxiv_id && (
                    <a
                      href={`https://arxiv.org/abs/${p.arxiv_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-primary hover:underline"
                    >
                      arxiv:{p.arxiv_id} <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {user && (
              <button
                onClick={() => setShowBookmark(true)}
                className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-[13px] font-medium text-foreground shadow-soft transition-all duration-150 hover:bg-muted hover:border-primary/30 dark:shadow-soft-dark"
              >
                <Bookmark size={13} /> Save
              </button>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div className="mt-6 flex flex-wrap gap-6">
          <div className="flex items-center gap-2 text-[14px]">
            <Quote size={15} className="text-primary" />
            <span className="font-semibold text-foreground">{p.citation_count || 0}</span>
            <span className="text-muted-foreground">citations</span>
          </div>
          <div className="flex items-center gap-2 text-[14px]">
            <Quote size={15} className="text-amber-500 dark:text-amber-400" />
            <span className="font-semibold text-foreground">{p.influential_citation_count || 0}</span>
            <span className="text-muted-foreground">influential</span>
          </div>
        </div>

        {/* Categories */}
        {p.categories && p.categories.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {p.categories.map((cat: string) => (
              <span
                key={cat}
                className="rounded-xl bg-primary/10 px-2.5 py-1 text-[12px] font-medium text-primary"
              >
                {cat}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Authors */}
        {p.authors && p.authors.length > 0 && (
          <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
            <h3 className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              <Users size={13} /> Authors
            </h3>
            <p className="mt-3 text-[14px] leading-relaxed text-foreground">
              {p.authors.map((a: any) => a.name).join(", ")}
            </p>
          </div>
        )}

        {/* Abstract */}
        {p.abstract && (
          <div className={`rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark ${!(p.authors && p.authors.length > 0) ? "md:col-span-2" : ""}`}>
            <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
              Abstract
            </h3>
            <p className="mt-3 text-[14px] leading-relaxed text-foreground">
              {p.abstract}
            </p>
          </div>
        )}
      </div>

      {/* AI Summary */}
      {p.summary && (
        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-6">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-primary">
            AI Summary
          </h3>
          <p className="mt-3 text-[14px] leading-relaxed text-foreground">
            {p.summary}
          </p>
        </div>
      )}

      {/* Linked Repos */}
      {paper.linked_repos?.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tighter text-foreground">
            <GitBranch size={18} /> Linked Repositories
          </h2>
          <div className="mt-5 space-y-2">
            {paper.linked_repos.map((repo: any) => (
              <Link
                key={repo.id}
                href={`/repos/${repo.id}`}
                className="block rounded-xl border border-border p-4 transition-all duration-150 hover:bg-muted/50 hover:border-primary/20"
              >
                <p className="text-[13px] font-medium text-foreground">
                  {repo.full_name || repo.repo_id}
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Confidence: {((repo.confidence_score || 0) * 100).toFixed(0)}% | {repo.link_type}
                </p>
              </Link>
            ))}
          </div>
        </div>
      )}

      <BookmarkDialog
        open={showBookmark}
        onClose={() => setShowBookmark(false)}
        prefill={{
          item_type: "paper",
          item_id: id as string,
          external_title: p.title,
        }}
      />
    </div>
  );
}
