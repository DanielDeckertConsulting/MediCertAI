/** Admin KPIs and audit logs API. Uses /api prefix (Vite proxy). */

const API = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function adminFetch(path: string, params?: Record<string, string | undefined>): Promise<Response> {
  const sp = new URLSearchParams();
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v != null && v !== "") sp.set(k, v);
    }
  }
  const q = sp.toString();
  const url = `${API}/admin${path}${q ? `?${q}` : ""}`;
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (res.status === 401 || res.status === 403) {
    window.location.href = "/login";
  }
  return res;
}

export interface KPISummary {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  request_count: number;
  chats_created_count: number;
}

export interface TokenBucket {
  bucket_start: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface ChatsBucket {
  bucket_start: string;
  chats_created: number;
}

export interface AssistModeRow {
  assist_mode: string | null;
  request_count: number;
  total_tokens: number;
}

export interface ModelRow {
  model_name: string;
  model_version: string | null;
  request_count: number;
  total_tokens: number;
}

export interface ActivitySummary {
  active_days_count: number;
  current_streak_days: number;
  avg_tokens_per_request: number;
}

export interface AuditLogRow {
  id: string;
  user_id: string;
  tenant_id: string;
  timestamp: string;
  action: string;
  assist_mode: string | null;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  model_name: string | null;
  model_version: string | null;
  entity_type: string | null;
  entity_id: string | null;
}

export interface AuditLogsResponse {
  items: AuditLogRow[];
  next_cursor: string | null;
}

export async function fetchKPISummary(params: {
  range?: string;
  scope?: "tenant" | "me";
}): Promise<KPISummary> {
  const res = await adminFetch("/kpis/summary", {
    range: params.range ?? "month",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchKPITokens(params: {
  granularity?: string;
  range?: string;
  scope?: "tenant" | "me";
}): Promise<TokenBucket[]> {
  const res = await adminFetch("/kpis/tokens", {
    granularity: params.granularity ?? "day",
    range: params.range ?? "last30d",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchKPIChatsCreated(params: {
  granularity?: string;
  range?: string;
  scope?: "tenant" | "me";
}): Promise<ChatsBucket[]> {
  const res = await adminFetch("/kpis/chats-created", {
    granularity: params.granularity ?? "day",
    range: params.range ?? "last30d",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchKPIAssistModes(params: {
  range?: string;
  scope?: "tenant" | "me";
}): Promise<AssistModeRow[]> {
  const res = await adminFetch("/kpis/assist-modes", {
    range: params.range ?? "month",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchKPIModels(params: {
  range?: string;
  scope?: "tenant" | "me";
}): Promise<ModelRow[]> {
  const res = await adminFetch("/kpis/models", {
    range: params.range ?? "month",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchKPIActivity(params: {
  range?: string;
  scope?: "tenant" | "me";
}): Promise<ActivitySummary> {
  const res = await adminFetch("/kpis/activity", {
    range: params.range ?? "month",
    scope: params.scope ?? "me",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchAuditLogs(params: {
  from?: string;
  to?: string;
  assist_mode?: string;
  action?: string;
  model_name?: string;
  user_id?: string;
  q?: string;
  limit?: number;
  cursor?: string;
  scope?: "tenant" | "me";
}): Promise<AuditLogsResponse> {
  const sp = new URLSearchParams();
  if (params.from) sp.set("from_ts", params.from + "T00:00:00Z");
  if (params.to) sp.set("to_ts", params.to + "T23:59:59Z");
  if (params.assist_mode) sp.set("assist_mode", params.assist_mode);
  if (params.action) sp.set("action", params.action);
  if (params.model_name) sp.set("model_name", params.model_name);
  if (params.user_id) sp.set("user_id", params.user_id);
  if (params.q) sp.set("q", params.q);
  if (params.limit) sp.set("limit", String(params.limit));
  if (params.cursor) sp.set("cursor", params.cursor);
  sp.set("scope", params.scope ?? "me");
  const res = await fetch(`${API}/admin/audit-logs?${sp.toString()}`, {
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
