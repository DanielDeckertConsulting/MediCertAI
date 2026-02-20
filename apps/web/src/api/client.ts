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
  created_at: string;
  updated_at: string;
  messages: MessageOut[];
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

export async function listChats(): Promise<ChatSummary[]> {
  const res = await apiFetch("/chats");
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
  patch: { title?: string; is_favorite?: boolean }
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

export async function exportChat(chatId: string): Promise<Blob> {
  const res = await apiFetch(`/chats/${chatId}/export.txt`);
  if (!res.ok) throw new Error(await res.text());
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
