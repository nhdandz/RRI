"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ExternalLink,
  Star,
  GitFork,
  Eye,
  BookOpen,
  AlertCircle,
  Calendar,
  Tag,
  Shield,
  FileText,
  Container,
  Bookmark,
} from "lucide-react";
import Link from "next/link";
import { fetchRepo } from "@/lib/api";
import { formatDate, formatNumber } from "@/lib/utils";
import { useAuth } from "@/components/AuthProvider";
import { BookmarkDialog } from "@/components/BookmarkDialog";

export default function RepoDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [repo, setRepo] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showBookmark, setShowBookmark] = useState(false);

  useEffect(() => {
    if (id) {
      fetchRepo(id as string)
        .then((data) => setRepo(data))
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

  if (!repo)
    return (
      <div className="py-32 text-center text-[15px] text-muted-foreground">
        Repository not found.
      </div>
    );

  const r = repo.repo || repo;

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      {/* Back */}
      <Link
        href="/repos"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft size={14} /> Back to repositories
      </Link>

      {/* Hero card */}
      <div className="rounded-2xl border border-border bg-card p-8 shadow-soft dark:shadow-soft-dark">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-semibold tracking-tighter text-foreground">
              {r.full_name}
            </h1>
            {r.description && (
              <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
                {r.description}
              </p>
            )}
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
            {r.html_url && (
              <a
                href={r.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-[13px] font-medium text-foreground shadow-soft transition-all duration-150 hover:bg-muted dark:shadow-soft-dark"
              >
                View on GitHub <ExternalLink size={13} />
              </a>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div className="mt-6 flex flex-wrap gap-6">
          <div className="flex items-center gap-2 text-[14px]">
            <Star size={15} className="text-amber-500 dark:text-amber-400" />
            <span className="font-semibold text-foreground">{formatNumber(r.stars_count || 0)}</span>
            <span className="text-muted-foreground">stars</span>
          </div>
          <div className="flex items-center gap-2 text-[14px]">
            <GitFork size={15} className="text-muted-foreground" />
            <span className="font-semibold text-foreground">{formatNumber(r.forks_count || 0)}</span>
            <span className="text-muted-foreground">forks</span>
          </div>
          <div className="flex items-center gap-2 text-[14px]">
            <Eye size={15} className="text-muted-foreground" />
            <span className="font-semibold text-foreground">{formatNumber(r.watchers_count || 0)}</span>
            <span className="text-muted-foreground">watchers</span>
          </div>
          <div className="flex items-center gap-2 text-[14px]">
            <AlertCircle size={15} className="text-muted-foreground" />
            <span className="font-semibold text-foreground">{r.open_issues_count || 0}</span>
            <span className="text-muted-foreground">issues</span>
          </div>
        </div>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Language & Topics */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            Language
          </h3>
          {r.primary_language ? (
            <span className="mt-3 inline-block rounded-xl bg-primary/10 px-3 py-1.5 text-[13px] font-medium text-primary">
              {r.primary_language}
            </span>
          ) : (
            <p className="mt-3 text-[13px] text-muted-foreground">Unknown</p>
          )}

          {r.topics && r.topics.length > 0 && (
            <>
              <h3 className="mt-6 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Topics
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {r.topics.map((t: string) => (
                  <span
                    key={t}
                    className="rounded-xl bg-[hsl(var(--accent)/0.1)] px-2.5 py-1 text-[12px] font-medium text-[hsl(var(--accent))]"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Metadata */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
            Details
          </h3>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-[13px] text-muted-foreground">
                <Calendar size={14} /> Created
              </span>
              <span className="text-[13px] font-medium text-foreground">
                {formatDate(r.created_at)}
              </span>
            </div>
            <div className="border-t border-border" />
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-[13px] text-muted-foreground">
                <Calendar size={14} /> Updated
              </span>
              <span className="text-[13px] font-medium text-foreground">
                {formatDate(r.updated_at)}
              </span>
            </div>
            <div className="border-t border-border" />
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-[13px] text-muted-foreground">
                <Tag size={14} /> Last Release
              </span>
              <span className="text-[13px] font-medium text-foreground">
                {r.last_release_tag || "-"}
              </span>
            </div>
            <div className="border-t border-border" />
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
                Quality
              </span>
              <div className="flex items-center gap-2">
                {r.has_readme && (
                  <span className="flex items-center gap-1 rounded-xl bg-emerald-500/10 px-2.5 py-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                    <FileText size={11} /> README
                  </span>
                )}
                {r.has_license && (
                  <span className="flex items-center gap-1 rounded-xl bg-primary/10 px-2.5 py-1 text-[11px] font-medium text-primary">
                    <Shield size={11} /> License
                  </span>
                )}
                {r.has_docker && (
                  <span className="flex items-center gap-1 rounded-xl bg-cyan-500/10 px-2.5 py-1 text-[11px] font-medium text-cyan-600 dark:text-cyan-400">
                    <Container size={11} /> Docker
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Summary */}
      {(repo.readme_summary || r.summary) && (
        <div className="rounded-2xl border border-primary/20 bg-primary/5 p-6">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-primary">
            AI Summary
          </h3>
          <p className="mt-3 text-[14px] leading-relaxed text-foreground">
            {repo.readme_summary || r.summary}
          </p>
        </div>
      )}

      {/* Linked Papers */}
      {repo.linked_papers?.length > 0 && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft dark:shadow-soft-dark">
          <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tighter text-foreground">
            <BookOpen size={18} /> Linked Papers
          </h2>
          <div className="mt-5 space-y-2">
            {repo.linked_papers.map((paper: any) => (
              <Link
                key={paper.id}
                href={`/papers/${paper.id}`}
                className="block rounded-xl border border-border p-4 transition-all duration-150 hover:bg-muted/50 hover:border-primary/20"
              >
                <p className="text-[13px] font-medium text-foreground">
                  {paper.title || paper.paper_id}
                </p>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Confidence: {((paper.confidence_score || 0) * 100).toFixed(0)}% | {paper.link_type}
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
          item_type: "repo",
          item_id: id as string,
          external_title: r.full_name,
        }}
      />
    </div>
  );
}
