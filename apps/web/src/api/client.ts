/** API client. Attaches token, handles 401/403. */
const baseUrl =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? "" : "http://localhost:8000");
const apiPath = baseUrl ? "" : "/api";

async function getToken(): Promise<string | null> {
  // TODO: read from auth store / B2C
  return null;
}

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${baseUrl}${apiPath}${path}`, { ...init, headers });
  if (res.status === 401 || res.status === 403) {
    window.location.href = "/login";
  }
  return res;
}

/** Fetch for SSE streaming; does not parse JSON, returns raw Response. */
export async function apiFetchStream(path: string, init?: RequestInit): Promise<Response> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Accept": "text/event-stream",
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${baseUrl}${apiPath}${path}`, { ...init, headers });
  if (res.status === 401 || res.status === 403) {
    window.location.href = "/login";
  }
  return res;
}

export async function healthCheck(): Promise<{ status: string; version?: string }> {
  const res = await apiFetch("/health");
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

// --- Chats API ---
export interface ChatSummary {
  id: string;
  title: string;
  updated_at: string;
  is_favorite: boolean;
  folder_id?: string | null;
  status?: string;
}

export interface FolderOut {
  id: string;
  name: string;
  created_at: string;
}

export interface MessageOut {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface ChatDetail {
  id: string;
  title: string;
  is_favorite: boolean;
  folder_id?: string | null;
  status?: string;
  created_at: string;
  updated_at: string;
  messages: MessageOut[];
  /** Session context for Smart Context Banner */
  last_message_at?: string | null;
  first_message_at?: string | null;
  total_tokens_in_session?: number;
  /** Conversation metadata (e.g. safe_mode) */
  metadata?: Record<string, unknown> | null;
}

export interface PromptSummary {
  key: string;
  display_name: string;
  version: number;
}

export interface PromptDetail {
  key: string;
  display_name: string;
  version: number;
  body: string;
}

export async function createChat(title?: string): Promise<ChatSummary & { created_at: string }> {
  const res = await apiFetch("/chats", {
    method: "POST",
    body: JSON.stringify({ title: title ?? "New chat" }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listChats(params?: {
  folderId?: string | null;
  unfiledOnly?: boolean;
}): Promise<ChatSummary[]> {
  const sp = new URLSearchParams();
  if (params?.folderId) sp.set("folder_id", params.folderId);
  if (params?.unfiledOnly) sp.set("unfiled_only", "true");
  const q = sp.toString();
  const res = await apiFetch(`/chats${q ? `?${q}` : ""}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getChat(chatId: string): Promise<ChatDetail> {
  const res = await apiFetch(`/chats/${chatId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function patchChat(
  chatId: string,
  patch: { title?: string; is_favorite?: boolean; folder_id?: string | null; metadata?: Record<string, unknown> }
): Promise<ChatSummary & { updated_at: string }> {
  const res = await apiFetch(`/chats/${chatId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteChat(chatId: string): Promise<void> {
  const res = await apiFetch(`/chats/${chatId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function finalizeChat(chatId: string): Promise<{ status: string }> {
  const res = await apiFetch(`/chats/${chatId}/finalize`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listPrompts(): Promise<PromptSummary[]> {
  const res = await apiFetch("/prompts");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getPromptLatest(key: string): Promise<PromptDetail> {
  const res = await apiFetch(`/prompts/${encodeURIComponent(key)}/latest`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updatePrompt(key: string, body: string): Promise<PromptDetail> {
  const res = await apiFetch(`/prompts/${encodeURIComponent(key)}`, {
    method: "PATCH",
    body: JSON.stringify({ body }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Folders API ---
export async function listFolders(): Promise<FolderOut[]> {
  const res = await apiFetch("/folders");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createFolder(name: string): Promise<FolderOut> {
  const res = await apiFetch("/folders", {
    method: "POST",
    body: JSON.stringify({ name: name.trim() }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function patchFolder(folderId: string, name: string): Promise<FolderOut> {
  const res = await apiFetch(`/folders/${folderId}`, {
    method: "PATCH",
    body: JSON.stringify({ name: name.trim() }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteFolder(folderId: string): Promise<void> {
  const res = await apiFetch(`/folders/${folderId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export type ExportFormat = "txt" | "pdf";

export async function exportChat(chatId: string, format: ExportFormat = "txt"): Promise<Blob> {
  const res = await apiFetch(`/chats/${chatId}/export?format=${format}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Export failed: ${res.status}`);
  }
  return res.blob();
}

// --- AI Responses API (EPIC 13) ---
export interface StructuredBlock {
  type: string;
  content?: string;
  level?: number;
  items?: string[];
  label?: string;
  command?: string;
  confidence?: number;
  metadata?: Record<string, unknown>;
}

export interface AIResponseOut {
  id: string;
  entity_type: string;
  entity_id: string;
  raw_markdown: string;
  structured_blocks: StructuredBlock[];
  model: string;
  confidence: number;
  version: number;
  created_at: string;
}

export interface ProcessMarkdownResult {
  id: string;
  entity_type: string;
  entity_id: string;
  structured_blocks: StructuredBlock[];
  model: string;
  confidence: number;
  version: number;
  needs_review: boolean;
}

export async function processAIMarkdown(params: {
  raw_markdown: string;
  entity_type: string;
  entity_id: string;
  model?: string;
  confidence?: number;
}): Promise<ProcessMarkdownResult> {
  const res = await apiFetch("/ai-responses", {
    method: "POST",
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Process failed: ${res.status}`);
  }
  return res.json();
}

export async function listAIResponses(entityId: string): Promise<AIResponseOut[]> {
  const res = await apiFetch(`/ai-responses?entity_id=${encodeURIComponent(entityId)}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getAIResponse(responseId: string): Promise<AIResponseOut> {
  const res = await apiFetch(`/ai-responses/${responseId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function executeAIAction(params: {
  command: string;
  label: string;
  confidence: number;
  entity_type: string;
  entity_id: string;
}): Promise<{ ok: boolean; command: string }> {
  const res = await apiFetch("/ai-responses/actions/execute", {
    method: "POST",
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// --- Case Summary (Cross-Conversation) ---
export interface CaseSummaryOut {
  case_summary: string;
  trends: string[];
  treatment_evolution: string;
}

export async function generateCaseSummary(conversationIds: string[]): Promise<CaseSummaryOut> {
  const res = await apiFetch("/cases/summary", {
    method: "POST",
    body: JSON.stringify({ conversation_ids: conversationIds }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Fallzusammenfassung konnte nicht erstellt werden.");
  }
  return res.json();
}

// --- Structured Session Document (EPIC 14) ---
export const STRUCTURED_DOC_FIELDS = [
  "session_context",
  "presenting_symptoms",
  "resources",
  "interventions",
  "homework",
  "risk_assessment",
  "progress_evaluation",
] as const;

export type StructuredContent = Record<(typeof STRUCTURED_DOC_FIELDS)[number], string>;

export interface StructuredDocumentOut {
  id: string;
  conversation_id: string;
  version: number;
  content: StructuredContent;
  created_at: string;
  updated_at: string;
}

export async function getStructuredDocument(chatId: string): Promise<StructuredDocumentOut> {
  const res = await apiFetch(`/chats/${chatId}/structured-document`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("NOT_FOUND");
    throw new Error(await res.text());
  }
  return res.json();
}

export async function putStructuredDocument(
  chatId: string,
  content: StructuredContent
): Promise<StructuredDocumentOut> {
  const res = await apiFetch(`/chats/${chatId}/structured-document`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function convertToStructuredDocument(
  chatId: string
): Promise<{ document: StructuredDocumentOut; usage: Record<string, number> }> {
  const res = await apiFetch(`/chats/${chatId}/structured-document/convert`, {
    method: "POST",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Konvertierung fehlgeschlagen.");
  }
  return res.json();
}

// --- Intervention Library (EPIC 14) ---
export interface InterventionOut {
  id: string;
  category: string;
  title: string;
  description: string;
  evidence_level: string | null;
  references: string[] | null;
}

export async function listInterventions(category?: string): Promise<InterventionOut[]> {
  const q = category ? `?category=${encodeURIComponent(category)}` : "";
  const res = await apiFetch(`/interventions${q}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function recordInterventionViewed(interventionId: string): Promise<void> {
  const res = await apiFetch(`/interventions/${interventionId}/viewed`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
}
