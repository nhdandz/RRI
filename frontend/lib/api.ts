import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

export async function fetchPapers(params?: Record<string, any>) {
  const { data } = await api.get("/papers", { params });
  return data;
}

export async function fetchPaper(id: string) {
  const { data } = await api.get(`/papers/${id}`);
  return data;
}

export async function fetchPaperStats(params?: Record<string, any>) {
  const { data } = await api.get("/papers/stats", { params });
  return data;
}

export async function fetchPaperCategories(): Promise<string[]> {
  const { data } = await api.get("/papers/categories");
  return data.categories;
}

export async function triggerCollectPapers() {
  const { data } = await api.post("/papers/collect");
  return data;
}

export async function triggerEnrichCitations() {
  const { data } = await api.post("/papers/enrich-citations");
  return data;
}

export async function fetchRepos(params?: Record<string, any>) {
  const { data } = await api.get("/repos", { params });
  return data;
}

export async function fetchKnownTopics(): Promise<string[]> {
  const { data } = await api.get("/repos/topics");
  return data.topics;
}

export async function fetchRepoStats(params?: Record<string, any>) {
  const { data } = await api.get("/repos/stats", { params });
  return data;
}

export async function fetchRepo(id: string) {
  const { data } = await api.get(`/repos/${id}`);
  return data;
}

export async function triggerCollectRepos() {
  const { data } = await api.post("/repos/collect");
  return data;
}

export async function triggerUpdateAllRepos() {
  const { data } = await api.post("/repos/update-all");
  return data;
}

export async function search(q: string, type?: string) {
  const { data } = await api.get("/search", { params: { q, type } });
  return data;
}

export async function fetchTrendingPapers(params?: Record<string, any>) {
  const { data } = await api.get("/trending/papers", { params });
  return data;
}

export async function fetchTrendingRepos(params?: Record<string, any>) {
  const { data } = await api.get("/trending/repos", { params });
  return data;
}

export async function fetchTechRadar() {
  const { data } = await api.get("/trending/tech-radar");
  return data;
}

export async function sendChatMessage(question: string, filters?: any) {
  const { data } = await api.post("/chat", { question, filters });
  return data;
}

// ── Conversations API ──

export async function fetchConversations() {
  const { data } = await api.get("/chat/conversations");
  return data;
}

export async function createConversation(title?: string, mode: string = "global") {
  const { data } = await api.post("/chat/conversations", { title, mode });
  return data;
}

export async function fetchConversation(id: string) {
  const { data } = await api.get(`/chat/conversations/${id}`);
  return data;
}

export async function deleteConversation(id: string) {
  await api.delete(`/chat/conversations/${id}`);
}

export async function sendConversationMessage(conversationId: string, question: string, filters?: any) {
  const { data } = await api.post(`/chat/conversations/${conversationId}/messages`, { question, filters });
  return data;
}

export async function fetchAlerts(params?: Record<string, any>) {
  const { data } = await api.get("/alerts", { params });
  return data;
}

export async function fetchWeeklyReport() {
  const { data } = await api.get("/reports/weekly");
  return data;
}

// ── Auth API ──

export async function loginUser(email: string, password: string) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export async function registerUser(email: string, username: string, password: string) {
  const { data } = await api.post("/auth/register", { email, username, password });
  return data;
}

export async function refreshToken(refresh_token: string) {
  const { data } = await api.post("/auth/refresh", { refresh_token });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

// ── Folders API ──

export async function fetchFolders() {
  const { data } = await api.get("/folders");
  return data;
}

export async function createFolder(body: {
  name: string;
  parent_id?: string | null;
  icon?: string | null;
  position?: number;
}) {
  const { data } = await api.post("/folders", body);
  return data;
}

export async function updateFolder(
  id: string,
  body: { name?: string; parent_id?: string | null; icon?: string | null; position?: number }
) {
  const { data } = await api.patch(`/folders/${id}`, body);
  return data;
}

export async function deleteFolder(id: string) {
  await api.delete(`/folders/${id}`);
}

// ── Bookmarks API ──

export async function fetchBookmarks(folderId: string) {
  const { data } = await api.get(`/bookmarks/folder/${folderId}`);
  return data;
}

export async function createBookmark(body: {
  folder_id: string;
  item_type: string;
  item_id?: string | null;
  external_url?: string | null;
  external_title?: string | null;
  external_metadata?: Record<string, any> | null;
  note?: string | null;
}) {
  const { data } = await api.post("/bookmarks", body);
  return data;
}

export async function updateBookmark(
  id: string,
  body: { folder_id?: string; note?: string }
) {
  const { data } = await api.patch(`/bookmarks/${id}`, body);
  return data;
}

export async function deleteBookmark(id: string) {
  await api.delete(`/bookmarks/${id}`);
}

// ── Folder Contents API (Drive-like) ──

export async function fetchFolderContents(folderId: string) {
  const { data } = await api.get(`/folders/${folderId}/contents`);
  return data;
}

// ── Documents API ──

export async function uploadDocument(
  folderId: string,
  file: File,
  onProgress?: (percent: number) => void
) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/documents/upload/${folderId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
}

export async function downloadDocument(id: string) {
  const response = await api.get(`/documents/${id}/download`, {
    responseType: "blob",
  });
  return response;
}

export async function updateDocument(
  id: string,
  body: { folder_id?: string; note?: string }
) {
  const { data } = await api.patch(`/documents/${id}`, body);
  return data;
}

export async function deleteDocument(id: string) {
  await api.delete(`/documents/${id}`);
}

// ── Document Chat API ──

export async function fetchDocumentLibrary() {
  const { data } = await api.get("/chat/documents/library");
  return data;
}

export async function embedDocuments(documentIds: string[], paperIds: string[] = []) {
  const { data } = await api.post("/chat/documents/embed", {
    document_ids: documentIds,
    paper_ids: paperIds,
  });
  return data;
}

export async function fetchEmbedStatus(documentIds: string[]) {
  const { data } = await api.get("/chat/documents/embed-status", {
    params: { document_ids: documentIds.join(",") },
  });
  return data;
}

export async function setConversationDocuments(conversationId: string, documentIds: string[]) {
  const { data } = await api.put(`/chat/conversations/${conversationId}/documents`, {
    document_ids: documentIds,
  });
  return data;
}

export async function fetchConversationDocuments(conversationId: string) {
  const { data } = await api.get(`/chat/conversations/${conversationId}/documents`);
  return data;
}

export default api;
