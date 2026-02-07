"use client";

import { useState, useEffect } from "react";
import {
  X,
  Search,
  FileText,
  GitBranch,
  Link as LinkIcon,
  FolderOpen,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  fetchFolders,
  createBookmark,
  search as searchApi,
} from "@/lib/api";

interface FolderOption {
  id: string;
  name: string;
  depth: number;
}

interface BookmarkDialogProps {
  open: boolean;
  onClose: () => void;
  prefill?: {
    item_type: string;
    item_id?: string;
    external_url?: string;
    external_title?: string;
  };
}

export function BookmarkDialog({ open, onClose, prefill }: BookmarkDialogProps) {
  const [tab, setTab] = useState<"system" | "external">(prefill?.item_id ? "system" : "external");
  const [folders, setFolders] = useState<FolderOption[]>([]);
  const [selectedFolderId, setSelectedFolderId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // System search
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [selectedItem, setSelectedItem] = useState<{
    item_type: string;
    item_id: string;
    title: string;
  } | null>(prefill?.item_id ? {
    item_type: prefill.item_type,
    item_id: prefill.item_id,
    title: prefill.external_title || "",
  } : null);

  // External URL
  const [externalUrl, setExternalUrl] = useState(prefill?.external_url || "");
  const [externalTitle, setExternalTitle] = useState(prefill?.external_title || "");
  const [note, setNote] = useState("");

  // Flatten folder tree
  const flattenFolders = (nodes: any[], depth = 0): FolderOption[] => {
    const result: FolderOption[] = [];
    for (const node of nodes) {
      result.push({ id: node.id, name: node.name, depth });
      if (node.children) {
        result.push(...flattenFolders(node.children, depth + 1));
      }
    }
    return result;
  };

  useEffect(() => {
    if (open) {
      fetchFolders().then((data) => {
        const flat = flattenFolders(data);
        setFolders(flat);
        if (flat.length > 0 && !selectedFolderId) {
          setSelectedFolderId(flat[0].id);
        }
      });
    }
  }, [open]);

  useEffect(() => {
    if (prefill?.item_id) setTab("system");
    else if (prefill?.external_url) setTab("external");
  }, [prefill]);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const data = await searchApi(query);
      setSearchResults(data.results || []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSave = async () => {
    if (!selectedFolderId) {
      setError("Please select a folder");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      if (tab === "system" && selectedItem) {
        await createBookmark({
          folder_id: selectedFolderId,
          item_type: selectedItem.item_type,
          item_id: selectedItem.item_id,
          external_title: selectedItem.title || undefined,
          note: note || undefined,
        });
      } else if (tab === "external") {
        if (!externalUrl.trim()) {
          setError("URL is required");
          setSubmitting(false);
          return;
        }
        await createBookmark({
          folder_id: selectedFolderId,
          item_type: "external",
          external_url: externalUrl,
          external_title: externalTitle || undefined,
          note: note || undefined,
        });
      }
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save bookmark");
    } finally {
      setSubmitting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-foreground">Save to Library</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="mb-4 flex gap-1 rounded-xl bg-muted p-1">
          <button
            onClick={() => setTab("system")}
            className={cn(
              "flex-1 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
              tab === "system"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            From System
          </button>
          <button
            onClick={() => setTab("external")}
            className={cn(
              "flex-1 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors",
              tab === "external"
                ? "bg-card text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            External URL
          </button>
        </div>

        {/* System search tab */}
        {tab === "system" && (
          <div className="space-y-3">
            <div className="flex gap-2">
              <div className="flex flex-1 items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 focus-within:border-primary/40">
                <Search size={14} className="text-muted-foreground" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="Search papers, repos..."
                  className="w-full bg-transparent text-[13px] text-foreground outline-none placeholder:text-muted-foreground/60"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searching}
                className="rounded-xl bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {searching ? <Loader2 size={14} className="animate-spin" /> : "Search"}
              </button>
            </div>

            {selectedItem && (
              <div className="flex items-center gap-2 rounded-xl border border-primary/30 bg-primary/5 px-3 py-2 text-[13px] text-foreground">
                {selectedItem.item_type === "paper" ? <FileText size={14} /> : <GitBranch size={14} />}
                <span className="flex-1 truncate">{selectedItem.title}</span>
                <button onClick={() => setSelectedItem(null)} className="text-muted-foreground hover:text-foreground">
                  <X size={14} />
                </button>
              </div>
            )}

            <div className="max-h-48 space-y-1 overflow-y-auto">
              {searchResults.map((r: any) => (
                <button
                  key={r.id}
                  onClick={() =>
                    setSelectedItem({
                      item_type: r.type === "paper" ? "paper" : "repo",
                      item_id: r.id,
                      title: r.title || r.full_name || "Untitled",
                    })
                  }
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] transition-colors hover:bg-muted",
                    selectedItem?.item_id === r.id && "bg-primary/10"
                  )}
                >
                  {r.type === "paper" ? (
                    <FileText size={14} className="shrink-0 text-blue-500" />
                  ) : (
                    <GitBranch size={14} className="shrink-0 text-orange-500" />
                  )}
                  <span className="flex-1 truncate text-foreground">{r.title || r.full_name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* External URL tab */}
        {tab === "external" && (
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-[12px] font-medium text-muted-foreground">URL</label>
              <div className="flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2 focus-within:border-primary/40">
                <LinkIcon size={14} className="text-muted-foreground" />
                <input
                  type="url"
                  value={externalUrl}
                  onChange={(e) => setExternalUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full bg-transparent text-[13px] text-foreground outline-none placeholder:text-muted-foreground/60"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
                Title (optional)
              </label>
              <input
                type="text"
                value={externalTitle}
                onChange={(e) => setExternalTitle(e.target.value)}
                placeholder="Give it a name"
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-[13px] text-foreground outline-none placeholder:text-muted-foreground/60 focus:border-primary/40"
              />
            </div>
          </div>
        )}

        {/* Folder selector + note */}
        <div className="mt-4 space-y-3">
          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Save to folder
            </label>
            <div className="flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-2">
              <FolderOpen size={14} className="text-primary" />
              <select
                value={selectedFolderId}
                onChange={(e) => setSelectedFolderId(e.target.value)}
                className="w-full bg-transparent text-[13px] text-foreground outline-none"
              >
                {folders.map((f) => (
                  <option key={f.id} value={f.id}>
                    {"  ".repeat(f.depth)}{f.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-[12px] font-medium text-muted-foreground">
              Note (optional)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={2}
              placeholder="Add a personal note..."
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-[13px] text-foreground outline-none placeholder:text-muted-foreground/60 focus:border-primary/40 resize-none"
            />
          </div>
        </div>

        {error && (
          <p className="mt-2 text-[12px] text-red-500">{error}</p>
        )}

        {/* Actions */}
        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-xl border border-border px-4 py-2 text-[13px] font-medium text-foreground transition-colors hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={submitting || (tab === "system" && !selectedItem) || folders.length === 0}
            className="rounded-xl bg-primary px-4 py-2 text-[13px] font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {submitting ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
