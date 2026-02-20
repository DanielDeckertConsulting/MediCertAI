/** Admin — KPIs and searchable audit logs. Mobile-first. */
import { useCallback, useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchKPISummary,
  fetchKPITokens,
  fetchKPIChatsCreated,
  fetchKPIAssistModes,
  fetchKPIModels,
  fetchKPIActivity,
  fetchAuditLogs,
  type KPISummary,
  type AuditLogRow,
} from "../api/admin";

type Tab = "kpis" | "logs";
type Scope = "me" | "tenant";
type Granularity = "day" | "week" | "month" | "year";

function formatDate(s: string): string {
  try {
    const d = new Date(s);
    return d.toLocaleDateString(undefined, { dateStyle: "short" });
  } catch {
    return s;
  }
}

function formatDateTime(s: string): string {
  try {
    const d = new Date(s);
    return d.toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" });
  } catch {
    return s;
  }
}

function KPICard({ title, value, sub }: { title: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-600 dark:bg-gray-800">
      <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
      <p className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{sub}</p>}
    </div>
  );
}

function BarChart({ data, maxVal, labelKey, valKey }: { data: { [k: string]: unknown }[]; maxVal: number; labelKey: string; valKey: string }) {
  return (
    <div className="space-y-2">
      {data.map((d, i) => {
        const label = String(d[labelKey] ?? "");
        const val = Number(d[valKey] ?? 0);
        const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
        return (
          <div key={i} className="flex flex-col gap-1">
            <div className="flex justify-between text-xs">
              <span className="truncate text-gray-600 dark:text-gray-400">{label || "—"}</span>
              <span className="shrink-0 font-medium">{val.toLocaleString()}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded bg-gray-100 dark:bg-gray-700">
              <div
                className="h-full rounded bg-primary-500 transition-all"
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function KPITab({ scope }: { scope: Scope }) {
  const [granularity, setGranularity] = useState<Granularity>("day");
  const range = "last30d";

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["admin", "kpis", "summary", scope, range],
    queryFn: () => fetchKPISummary({ range, scope }),
  });

  const { data: tokens } = useQuery({
    queryKey: ["admin", "kpis", "tokens", scope, granularity, range],
    queryFn: () => fetchKPITokens({ granularity, range, scope }),
  });

  const { data: chatsCreated } = useQuery({
    queryKey: ["admin", "kpis", "chats", scope, granularity, range],
    queryFn: () => fetchKPIChatsCreated({ granularity, range, scope }),
  });

  const { data: assistModes } = useQuery({
    queryKey: ["admin", "kpis", "assist-modes", scope, range],
    queryFn: () => fetchKPIAssistModes({ range, scope }),
  });

  const { data: models } = useQuery({
    queryKey: ["admin", "kpis", "models", scope, range],
    queryFn: () => fetchKPIModels({ range, scope }),
  });

  const { data: activity } = useQuery({
    queryKey: ["admin", "kpis", "activity", scope, range],
    queryFn: () => fetchKPIActivity({ range, scope }),
  });

  const maxTokens = Math.max(1, ...(tokens?.map((t) => t.total_tokens) ?? []));
  const maxChats = Math.max(1, ...(chatsCreated?.map((c) => c.chats_created) ?? []));

  if (summaryLoading) {
    return (
      <div className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
        Lade KPIs…
      </div>
    );
  }

  const s = summary as KPISummary | undefined;
  const avgTokens = s && s.request_count > 0 ? Math.round(s.total_tokens / s.request_count) : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KPICard title="Tokens (Eingabe)" value={s?.input_tokens?.toLocaleString() ?? "0"} />
        <KPICard title="Tokens (Ausgabe)" value={s?.output_tokens?.toLocaleString() ?? "0"} />
        <KPICard title="Tokens gesamt" value={s?.total_tokens?.toLocaleString() ?? "0"} />
        <KPICard title="Anfragen" value={s?.request_count?.toLocaleString() ?? "0"} sub={`Ø ${avgTokens} Tokens/Anfrage`} />
        <KPICard title="Chats erstellt" value={s?.chats_created_count?.toLocaleString() ?? "0"} />
        {activity && (
          <KPICard
            title="Aktive Tage"
            value={activity.active_days_count}
            sub={`Streak: ${activity.current_streak_days} Tage`}
          />
        )}
      </div>

      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Granularität</label>
          <select
            value={granularity}
            onChange={(e) => setGranularity(e.target.value as Granularity)}
            className="min-h-touch rounded border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          >
            <option value="day">Tag</option>
            <option value="week">Woche</option>
            <option value="month">Monat</option>
            <option value="year">Jahr</option>
          </select>
        </div>
        <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Tokens über Zeit</h3>
        {tokens && tokens.length > 0 ? (
          <BarChart
            data={tokens.map((t) => ({ label: formatDate(t.bucket_start), value: t.total_tokens }))}
            maxVal={maxTokens}
            labelKey="label"
            valKey="value"
          />
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">Keine Daten</p>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Chats erstellt</h3>
        {chatsCreated && chatsCreated.length > 0 ? (
          <BarChart
            data={chatsCreated.map((c) => ({ label: formatDate(c.bucket_start), value: c.chats_created }))}
            maxVal={maxChats}
            labelKey="label"
            valKey="value"
          />
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">Keine Daten</p>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Assistenzmodus</h3>
        {assistModes && assistModes.length > 0 ? (
          <BarChart
            data={assistModes.map((a) => ({
              label: a.assist_mode ?? "—",
              value: a.request_count,
            }))}
            maxVal={Math.max(1, ...assistModes.map((a) => a.request_count))}
            labelKey="label"
            valKey="value"
          />
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">Keine Daten</p>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Modell-Nutzung</h3>
        {models && models.length > 0 ? (
          <BarChart
            data={models.map((m) => ({
              label: `${m.model_name}${m.model_version ? ` (${m.model_version})` : ""}`,
              value: m.request_count,
            }))}
            maxVal={Math.max(1, ...models.map((m) => m.request_count))}
            labelKey="label"
            valKey="value"
          />
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">Keine Daten</p>
        )}
      </div>
    </div>
  );
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function LogsTab({ scope }: { scope: Scope }) {
  const [q, setQ] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [assistMode, setAssistMode] = useState("");
  const [action, setAction] = useState("");
  const [modelName, setModelName] = useState("");
  const [cursor, setCursor] = useState<string | null>(null);

  const debouncedQ = useDebounce(q, 300);

  useEffect(() => {
    setCursor(null);
  }, [debouncedQ, fromDate, toDate, assistMode, action, modelName]);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [
      "admin",
      "audit-logs",
      scope,
      debouncedQ,
      fromDate,
      toDate,
      assistMode,
      action,
      modelName,
      cursor,
    ],
    queryFn: () =>
      fetchAuditLogs({
        q: debouncedQ || undefined,
        from: fromDate || undefined,
        to: toDate || undefined,
        assist_mode: assistMode || undefined,
        action: action || undefined,
        model_name: modelName || undefined,
        scope,
        limit: 50,
        cursor: cursor ?? undefined,
      }),
  });

  const handlePrev = useCallback(() => {
    setCursor(null);
  }, []);

  const items = data?.items ?? [];
  const nextCursor = data?.next_cursor ?? null;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Suchen (Aktion, Modus, Modell…)"
          className="min-h-touch min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          aria-label="Logs durchsuchen"
        />
        <input
          type="date"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          className="min-h-touch rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          aria-label="Von Datum"
        />
        <input
          type="date"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          className="min-h-touch rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          aria-label="Bis Datum"
        />
        <input
          type="text"
          value={assistMode}
          onChange={(e) => setAssistMode(e.target.value)}
          placeholder="Assistenzmodus"
          className="min-h-touch w-40 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />
        <input
          type="text"
          value={action}
          onChange={(e) => setAction(e.target.value)}
          placeholder="Aktion"
          className="min-h-touch w-32 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />
        <input
          type="text"
          value={modelName}
          onChange={(e) => setModelName(e.target.value)}
          placeholder="Modell"
          className="min-h-touch w-32 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        />
      </div>

      {isError && (
        <div className="rounded bg-red-100 px-4 py-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-200">
          Fehler beim Laden.{" "}
          <button type="button" onClick={() => refetch()} className="underline">
            Erneut versuchen
          </button>
        </div>
      )}

      {isLoading ? (
        <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">Lade Logs…</p>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">Keine Logs gefunden.</p>
      ) : (
        <>
          <div className="overflow-x-auto -mx-4 px-4 sm:mx-0 sm:px-0">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800">
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Zeit</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">User</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Aktion</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Modus</th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400">Tokens</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400">Modell</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-600">
                {items.map((r: AuditLogRow) => (
                  <tr key={r.id} className="bg-white dark:bg-gray-900">
                    <td className="whitespace-nowrap px-3 py-2 text-xs text-gray-600 dark:text-gray-400">
                      {formatDateTime(r.timestamp)}
                    </td>
                    <td className="px-3 py-2 text-xs">
                      <span className="truncate max-w-[80px] sm:max-w-[120px] inline-block" title={r.user_id}>
                        {r.user_id.slice(0, 8)}…
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-700 dark:text-gray-300">{r.action}</td>
                    <td className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400">{r.assist_mode ?? "—"}</td>
                    <td className="whitespace-nowrap px-3 py-2 text-right text-xs">
                      {r.input_tokens}/{r.output_tokens} ({r.total_tokens})
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-600 dark:text-gray-400">
                      {r.model_name ?? "—"}
                      {r.model_version ? ` (${r.model_version})` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-between pt-2">
            <button
              type="button"
              onClick={handlePrev}
              disabled={!cursor}
              className="min-h-touch min-w-touch rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-800"
            >
              Zurück
            </button>
            <button
              type="button"
              onClick={() => nextCursor && setCursor(nextCursor)}
              disabled={!nextCursor}
              className="min-h-touch min-w-touch rounded px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 disabled:opacity-50 dark:text-primary-400"
            >
              Weiter
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function AdminPage() {
  const [tab, setTab] = useState<Tab>("kpis");
  const [scope, setScope] = useState<Scope>("me");

  return (
    <div className="min-w-0">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Admin</h2>
        <div className="flex gap-2">
          <label className="flex items-center gap-2 text-sm">
            <span className="text-gray-600 dark:text-gray-400">Bereich:</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as Scope)}
              className="min-h-touch rounded border border-gray-300 bg-white px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
            >
              <option value="me">Nur ich</option>
              <option value="tenant">Mandant (Admin)</option>
            </select>
          </label>
        </div>
      </div>

      <div className="mb-4 flex gap-1 border-b border-gray-200 dark:border-gray-600">
        <button
          type="button"
          onClick={() => setTab("kpis")}
          className={`min-h-touch min-w-touch px-4 py-2 text-sm font-medium ${
            tab === "kpis"
              ? "border-b-2 border-primary-500 text-primary-600 dark:text-primary-400"
              : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
          }`}
        >
          KPIs
        </button>
        <button
          type="button"
          onClick={() => setTab("logs")}
          className={`min-h-touch min-w-touch px-4 py-2 text-sm font-medium ${
            tab === "logs"
              ? "border-b-2 border-primary-500 text-primary-600 dark:text-primary-400"
              : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
          }`}
        >
          Logs
        </button>
      </div>

      {tab === "kpis" && <KPITab scope={scope} />}
      {tab === "logs" && <LogsTab scope={scope} />}
    </div>
  );
}
