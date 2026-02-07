"use client";

import { useState, useEffect, useCallback } from "react";
import {
  X,
  ChevronRight,
  ChevronDown,
  Folder,
  FileText,
  File,
  FileSpreadsheet,
  Presentation,
  Check,
  Loader2,
  AlertCircle,
  Trash2,
  BookOpen,
  Download,
} from "lucide-react";
import { fetchDocumentLibrary, embedDocuments, fetchEmbedStatus } from "@/lib/api";

interface LibraryDocument {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  created_at: string;
}

interface LibraryPaper {
  paper_id: string;
  title: string;
  pdf_url: string | null;
  arxiv_id: string | null;
  source: string | null;
  has_local_pdf: boolean;
  document_id: string | null;
  folder_id: string;
}

interface LibraryFolder {
  id: string;
  name: string;
  parent_id: string | null;
  documents: LibraryDocument[];
  papers: LibraryPaper[];
  children: LibraryFolder[];
}

interface LibraryResponse {
  folders: LibraryFolder[];
  root_documents: LibraryDocument[];
}

interface EmbedStatusItem {
  document_id: string;
  status: string;
  chunk_count: number;
  error_message: string | null;
}

// Track selection: either a document or a paper
interface SelectedItem {
  type: "document" | "paper";
  id: string; // document_id or paper_id
  label: string;
  contentType?: string;
  paper?: LibraryPaper;
}

interface DocumentPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (documentIds: string[]) => void;
  initialDocumentIds?: string[];
}

function getFileIcon(contentType: string) {
  if (contentType === "application/pdf") return <FileText size={14} className="text-red-500" />;
  if (contentType === "text/csv") return <FileSpreadsheet size={14} className="text-green-500" />;
  if (contentType.includes("presentation")) return <Presentation size={14} className="text-orange-500" />;
  if (contentType.includes("wordprocessingml")) return <FileText size={14} className="text-blue-500" />;
  return <File size={14} className="text-muted-foreground" />;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function FolderNode({
  folder,
  selectedItems,
  onToggleDoc,
  onTogglePaper,
}: {
  folder: LibraryFolder;
  selectedItems: Map<string, SelectedItem>;
  onToggleDoc: (id: string) => void;
  onTogglePaper: (paper: LibraryPaper) => void;
}) {
  const [expanded, setExpanded] = useState(true);
  const totalItems = folder.documents.length + folder.papers.length;
  const hasContent = totalItems > 0 || folder.children.length > 0;

  if (!hasContent) return null;

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-foreground hover:bg-muted"
      >
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        <Folder size={14} className="text-primary" />
        <span className="truncate">{folder.name}</span>
        {totalItems > 0 && (
          <span className="ml-auto text-xs text-muted-foreground">{totalItems}</span>
        )}
      </button>

      {expanded && (
        <div className="ml-4 border-l border-border pl-2">
          {/* Documents */}
          {folder.documents.map((doc) => (
            <label
              key={`doc-${doc.id}`}
              className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-muted"
            >
              <input
                type="checkbox"
                checked={selectedItems.has(`doc:${doc.id}`)}
                onChange={() => onToggleDoc(doc.id)}
                className="h-3.5 w-3.5 rounded border-border accent-primary"
              />
              {getFileIcon(doc.content_type)}
              <span className="flex-1 truncate text-foreground/90">{doc.original_filename}</span>
              <span className="shrink-0 text-[11px] text-muted-foreground">
                {formatFileSize(doc.file_size)}
              </span>
            </label>
          ))}

          {/* Bookmarked Papers */}
          {folder.papers.map((paper) => (
            <label
              key={`paper-${paper.paper_id}`}
              className={`flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-muted ${
                !paper.pdf_url && !paper.has_local_pdf ? "opacity-50" : ""
              }`}
            >
              <input
                type="checkbox"
                checked={selectedItems.has(`paper:${paper.paper_id}`)}
                onChange={() => onTogglePaper(paper)}
                disabled={!paper.pdf_url && !paper.has_local_pdf}
                className="h-3.5 w-3.5 rounded border-border accent-primary"
              />
              <BookOpen size={14} className="shrink-0 text-purple-500" />
              <span className="flex-1 truncate text-foreground/90" title={paper.title}>
                {paper.title}
              </span>
              {paper.has_local_pdf ? (
                <span className="shrink-0 text-[10px] text-green-600">PDF</span>
              ) : paper.pdf_url ? (
                <span className="flex shrink-0 items-center gap-0.5 text-[10px] text-blue-500">
                  <Download size={10} /> Auto
                </span>
              ) : (
                <span className="shrink-0 text-[10px] text-muted-foreground">No PDF</span>
              )}
            </label>
          ))}

          {/* Sub-folders */}
          {folder.children.map((child) => (
            <FolderNode
              key={child.id}
              folder={child}
              selectedItems={selectedItems}
              onToggleDoc={onToggleDoc}
              onTogglePaper={onTogglePaper}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocumentPickerModal({
  isOpen,
  onClose,
  onConfirm,
  initialDocumentIds = [],
}: DocumentPickerModalProps) {
  const [library, setLibrary] = useState<LibraryResponse | null>(null);
  // Map key: "doc:{id}" or "paper:{id}"
  const [selectedItems, setSelectedItems] = useState<Map<string, SelectedItem>>(new Map());
  const [embedStatuses, setEmbedStatuses] = useState<Map<string, EmbedStatusItem>>(new Map());
  const [loading, setLoading] = useState(false);
  const [embedding, setEmbedding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLibrary = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchDocumentLibrary();
      setLibrary(data);
    } catch {
      setError("Failed to load library");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadLibrary();
      // Restore initial document selections
      const initial = new Map<string, SelectedItem>();
      for (const id of initialDocumentIds) {
        initial.set(`doc:${id}`, { type: "document", id, label: id });
      }
      setSelectedItems(initial);
      setEmbedStatuses(new Map());
      setError(null);
    }
  }, [isOpen, loadLibrary, initialDocumentIds]);

  // Load embed status for selected documents
  useEffect(() => {
    const docIds = Array.from(selectedItems.values())
      .filter((item) => item.type === "document")
      .map((item) => item.id);
    if (docIds.length === 0) return;

    const loadStatus = async () => {
      try {
        const data = await fetchEmbedStatus(docIds);
        const map = new Map<string, EmbedStatusItem>();
        for (const item of data.results) {
          map.set(item.document_id, item);
        }
        setEmbedStatuses(map);
      } catch {
        // silently fail
      }
    };
    loadStatus();
  }, [selectedItems]);

  const toggleDoc = (id: string) => {
    setSelectedItems((prev) => {
      const next = new Map(prev);
      const key = `doc:${id}`;
      if (next.has(key)) {
        next.delete(key);
      } else {
        // Find doc info from library
        let label = id;
        const findDoc = (folders: LibraryFolder[]): LibraryDocument | undefined => {
          for (const f of folders) {
            const d = f.documents.find((d) => d.id === id);
            if (d) return d;
            const found = findDoc(f.children);
            if (found) return found;
          }
          return undefined;
        };
        const doc = library ? findDoc(library.folders) : undefined;
        next.set(key, {
          type: "document",
          id,
          label: doc?.original_filename || id,
          contentType: doc?.content_type,
        });
      }
      return next;
    });
  };

  const togglePaper = (paper: LibraryPaper) => {
    setSelectedItems((prev) => {
      const next = new Map(prev);
      const key = `paper:${paper.paper_id}`;
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.set(key, {
          type: "paper",
          id: paper.paper_id,
          label: paper.title,
          contentType: "application/pdf",
          paper,
        });
      }
      return next;
    });
  };

  const removeItem = (key: string) => {
    setSelectedItems((prev) => {
      const next = new Map(prev);
      next.delete(key);
      return next;
    });
  };

  const handleConfirm = async () => {
    if (selectedItems.size === 0) return;

    setEmbedding(true);
    setError(null);

    try {
      const items = Array.from(selectedItems.values());
      const documentIds = items.filter((i) => i.type === "document").map((i) => i.id);
      const paperIds = items.filter((i) => i.type === "paper").map((i) => i.id);

      // Trigger embedding (papers will be auto-downloaded)
      const embedResult = await embedDocuments(documentIds, paperIds);

      // Update statuses
      const map = new Map<string, EmbedStatusItem>();
      for (const item of embedResult.results) {
        map.set(item.document_id, item);
      }
      setEmbedStatuses(map);

      // Check for failures
      const failures = embedResult.results.filter((r: EmbedStatusItem) => r.status === "failed");
      if (failures.length > 0 && failures.length === embedResult.results.length) {
        setError("All items failed to embed");
        setEmbedding(false);
        return;
      }

      // Get successfully embedded document IDs
      const successIds = embedResult.results
        .filter((r: EmbedStatusItem) => r.status === "completed")
        .map((r: EmbedStatusItem) => r.document_id);

      onConfirm(successIds);
    } catch {
      setError("Failed to embed documents");
    } finally {
      setEmbedding(false);
    }
  };

  if (!isOpen) return null;

  const selectedCount = selectedItems.size;
  const paperCount = Array.from(selectedItems.values()).filter((i) => i.type === "paper").length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="flex h-[80vh] w-[900px] max-w-[95vw] flex-col rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">Select Sources</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Choose documents and saved papers from your library to chat with
            </p>
          </div>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left — Library Browser */}
          <div className="flex w-[55%] flex-col border-r border-border">
            <div className="px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Library
              </p>
            </div>
            <div className="flex-1 overflow-y-auto px-3 pb-3">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={20} className="animate-spin text-muted-foreground" />
                </div>
              ) : library && library.folders.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  No supported documents or papers found in your library
                </p>
              ) : (
                library?.folders.map((folder) => (
                  <FolderNode
                    key={folder.id}
                    folder={folder}
                    selectedItems={selectedItems}
                    onToggleDoc={toggleDoc}
                    onTogglePaper={togglePaper}
                  />
                ))
              )}
            </div>

            {/* Legend */}
            <div className="border-t border-border px-4 py-2">
              <div className="flex items-center gap-4 text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FileText size={11} className="text-red-500" /> Documents
                </span>
                <span className="flex items-center gap-1">
                  <BookOpen size={11} className="text-purple-500" /> Saved Papers
                </span>
                <span className="flex items-center gap-1">
                  <Download size={11} className="text-blue-500" /> Auto-download PDF
                </span>
              </div>
            </div>
          </div>

          {/* Right — Selected Sources */}
          <div className="flex w-[45%] flex-col">
            <div className="px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Selected Sources ({selectedCount})
                {paperCount > 0 && (
                  <span className="ml-1 font-normal text-blue-500">
                    ({paperCount} paper{paperCount > 1 ? "s" : ""} will auto-download)
                  </span>
                )}
              </p>
            </div>
            <div className="flex-1 overflow-y-auto px-3 pb-3">
              {selectedCount === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  No items selected
                </p>
              ) : (
                Array.from(selectedItems.entries()).map(([key, item]) => {
                  const status = item.type === "document" ? embedStatuses.get(item.id) : null;
                  return (
                    <div
                      key={key}
                      className="mb-1.5 flex items-center gap-2 rounded-lg border border-border bg-background/50 px-3 py-2"
                    >
                      {item.type === "paper" ? (
                        <BookOpen size={14} className="shrink-0 text-purple-500" />
                      ) : item.contentType ? (
                        getFileIcon(item.contentType)
                      ) : (
                        <File size={14} />
                      )}
                      <span className="flex-1 truncate text-sm text-foreground/90">
                        {item.label}
                      </span>

                      {/* Status badge */}
                      {item.type === "paper" ? (
                        item.paper?.has_local_pdf ? (
                          <span className="flex items-center gap-1 text-[11px] text-green-600">
                            <Check size={12} /> PDF ready
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-[11px] text-blue-500">
                            <Download size={12} /> Will download
                          </span>
                        )
                      ) : status?.status === "completed" ? (
                        <span className="flex items-center gap-1 text-[11px] text-green-600">
                          <Check size={12} /> Cached
                        </span>
                      ) : status?.status === "processing" ? (
                        <span className="flex items-center gap-1 text-[11px] text-primary">
                          <Loader2 size={12} className="animate-spin" /> Embedding
                        </span>
                      ) : status?.status === "failed" ? (
                        <span className="flex items-center gap-1 text-[11px] text-red-500" title={status.error_message || ""}>
                          <AlertCircle size={12} /> Failed
                        </span>
                      ) : (
                        <span className="text-[11px] text-muted-foreground">Pending</span>
                      )}

                      <button
                        onClick={() => removeItem(key)}
                        className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-muted-foreground hover:bg-red-500/10 hover:text-red-500"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-6 py-4">
          <div>
            {error && (
              <p className="text-xs text-red-500">{error}</p>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="rounded-xl border border-border px-4 py-2 text-sm text-foreground transition-colors hover:bg-muted"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedCount === 0 || embedding}
              className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2 text-sm font-medium text-primary-foreground transition-all hover:brightness-110 disabled:opacity-40"
            >
              {embedding ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  {paperCount > 0 ? "Downloading & Embedding..." : "Embedding..."}
                </>
              ) : (
                `Confirm & Embed${paperCount > 0 ? ` (${paperCount} download)` : ""}`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
