/** Modal for cross-conversation case summary. Includes mandatory disclaimer. */
import type { CaseSummaryOut } from "../api/client";

const DISCLAIMER =
  "KI-gestützte Zusammenfassung – keine diagnostische Entscheidung.";

export function CaseSummaryModal({
  isOpen,
  onClose,
  summary,
  isLoading,
  error,
}: {
  isOpen: boolean;
  onClose: () => void;
  summary: CaseSummaryOut | null;
  isLoading: boolean;
  error: string | null;
}) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="case-summary-title"
    >
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800">
        <div className="shrink-0 border-b border-gray-200 px-4 py-3 dark:border-gray-600">
          <h2 id="case-summary-title" className="text-lg font-semibold">
            Fallzusammenfassung
          </h2>
          <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
            {DISCLAIMER}
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {isLoading && (
            <p className="py-8 text-center text-gray-500 dark:text-gray-400">
              Zusammenfassung wird erstellt…
            </p>
          )}
          {error && (
            <div className="rounded bg-red-100 px-4 py-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-200">
              {error}
            </div>
          )}
          {!isLoading && !error && summary && (
            <div className="space-y-4">
              {summary.case_summary && (
                <section>
                  <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Zusammenfassung
                  </h3>
                  <p className="whitespace-pre-wrap text-sm">{summary.case_summary}</p>
                </section>
              )}
              {summary.trends && summary.trends.length > 0 && (
                <section>
                  <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Beobachtete Trends (nicht-diagnostisch)
                  </h3>
                  <ul className="list-inside list-disc space-y-1 text-sm">
                    {summary.trends.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </section>
              )}
              {summary.treatment_evolution && (
                <section>
                  <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Dokumentierter Verlauf
                  </h3>
                  <p className="whitespace-pre-wrap text-sm">
                    {summary.treatment_evolution}
                  </p>
                </section>
              )}
            </div>
          )}
        </div>

        <div className="shrink-0 border-t border-gray-200 p-4 dark:border-gray-600">
          <button
            type="button"
            onClick={onClose}
            className="min-h-touch min-w-touch w-full rounded-lg bg-primary-500 px-4 py-3 text-sm font-medium text-white hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
          >
            Schließen
          </button>
        </div>
      </div>
    </div>
  );
}
