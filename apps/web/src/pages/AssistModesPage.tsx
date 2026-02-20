/** Assistenzmodus — Systemprompt-Vorlagen anzeigen und bearbeiten. Mobile-first. */
import { useCallback, useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listPrompts,
  getPromptLatest,
  updatePrompt,
  type PromptDetail,
} from "../api/client";

function PromptCard({
  detail,
  onSaved,
}: {
  detail: PromptDetail;
  onSaved: () => void;
}) {
  const [body, setBody] = useState(detail.body);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const queryClient = useQueryClient();

  useEffect(() => {
    setBody(detail.body);
    setHasChanges(false);
  }, [detail.body]);

  const handleBodyChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setBody(e.target.value);
      setHasChanges(e.target.value !== detail.body);
    },
    [detail.body]
  );

  const handleSave = useCallback(async () => {
    if (!hasChanges || body.trim() === detail.body.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      await updatePrompt(detail.key, body.trim());
      setHasChanges(false);
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      queryClient.invalidateQueries({ queryKey: ["prompts-details"] });
      onSaved();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Fehler beim Speichern");
    } finally {
      setIsSaving(false);
    }
  }, [detail.key, detail.body, body, hasChanges, queryClient, onSaved]);

  const handleReset = useCallback(() => {
    setBody(detail.body);
    setHasChanges(false);
  }, [detail.body]);

  return (
    <article className="rounded-lg border border-gray-200 bg-white dark:border-gray-600 dark:bg-gray-800">
      <header className="border-b border-gray-200 px-4 py-3 dark:border-gray-600">
        <h3 className="text-base font-medium text-gray-900 dark:text-white">
          {detail.display_name}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Version {detail.version}
        </p>
      </header>
      <div className="p-4">
        <textarea
          value={body}
          onChange={handleBodyChange}
          rows={12}
          className="mb-3 w-full resize-y rounded border border-gray-300 bg-gray-50 px-3 py-2 text-sm font-mono leading-relaxed text-gray-900 placeholder-gray-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
          placeholder="Systemprompt eingeben…"
          aria-label={`${detail.display_name} bearbeiten`}
        />
        {error && (
          <p
            className="mb-3 text-sm text-red-600 dark:text-red-400"
            role="alert"
          >
            {error}
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={!hasChanges || isSaving || !body.trim()}
            className="min-h-touch min-w-touch rounded-lg bg-primary-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 disabled:hover:bg-primary-600 dark:bg-primary-500 dark:hover:bg-primary-600"
          >
            {isSaving ? "Speichern…" : "Speichern"}
          </button>
          {hasChanges && (
            <button
              type="button"
              onClick={handleReset}
              disabled={isSaving}
              className="min-h-touch min-w-touch rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Zurücksetzen
            </button>
          )}
        </div>
      </div>
    </article>
  );
}

export default function AssistModesPage() {
  const queryClient = useQueryClient();
  const handleSaved = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["prompts"] });
  }, [queryClient]);

  const {
    data: prompts = [],
    isLoading: listLoading,
    isError: listError,
  } = useQuery({
    queryKey: ["prompts"],
    queryFn: listPrompts,
  });

  const detailQueries = useQuery({
    queryKey: ["prompts-details", prompts.map((p) => p.key).join(",")],
    queryFn: async () => {
      const results = await Promise.all(
        prompts.map((p) => getPromptLatest(p.key))
      );
      return results;
    },
    enabled: prompts.length > 0,
  });

  if (listError || detailQueries.isError) {
    return (
      <div className="min-w-0">
        <h2 className="mb-4 text-lg font-semibold">Assistenzmodus</h2>
        <div
          className="rounded bg-amber-100 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-200"
          role="alert"
        >
          Vorlagen konnten nicht geladen werden. API prüfen.
        </div>
      </div>
    );
  }

  if (listLoading || !detailQueries.data) {
    return (
      <div className="min-w-0">
        <h2 className="mb-4 text-lg font-semibold">Assistenzmodus</h2>
        <p className="text-gray-500 dark:text-gray-400">Lade Vorlagen…</p>
      </div>
    );
  }

  const details: PromptDetail[] = detailQueries.data;

  if (details.length === 0) {
    return (
      <div className="min-w-0">
        <h2 className="mb-4 text-lg font-semibold">Assistenzmodus</h2>
        <p className="text-gray-500 dark:text-gray-400">
          Keine Vorlagen vorhanden.
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0">
      <h2 className="mb-4 text-lg font-semibold">Assistenzmodus</h2>
      <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
        Systemprompt-Vorlagen bearbeiten. Änderungen gelten für neue Chats.
      </p>
      <div className="flex flex-col gap-6">
        {details.map((d) => (
          <PromptCard key={d.key} detail={d} onSaved={handleSaved} />
        ))}
      </div>
    </div>
  );
}
