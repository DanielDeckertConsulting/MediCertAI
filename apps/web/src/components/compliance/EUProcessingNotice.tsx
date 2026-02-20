/**
 * EU Processing Notice — visible compliance banner.
 * "Alle Daten werden innerhalb der EU verarbeitet."
 * Dismissible via localStorage; accessible; mobile-first.
 */
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

const STORAGE_KEY = "clinai.eu_processing_notice.dismissed.v1";

function getDismissed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function setDismissed(value: boolean): void {
  try {
    if (value) {
      window.localStorage.setItem(STORAGE_KEY, "true");
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // ignore
  }
}

export function EUProcessingNotice() {
  const [dismissed, setDismissedState] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setDismissedState(getDismissed());
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    setDismissedState(true);
  };

  if (!mounted || dismissed) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-slate-50 px-3 py-2.5 text-sm dark:border-gray-600 dark:bg-slate-800/50"
    >
      <span
        className="shrink-0 text-slate-500 dark:text-slate-400"
        aria-hidden
        title="Verarbeitung erfolgt in Azure Region Germany West Central."
      >
        ℹ️
      </span>
      <p
        className="min-w-0 flex-1 text-gray-700 dark:text-gray-300"
        title="Verarbeitung erfolgt in Azure Region Germany West Central."
      >
        Alle Daten werden innerhalb der EU verarbeitet.
      </p>
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <Link
          to="/privacy"
          className="min-h-touch min-w-touch inline-flex items-center rounded px-2 py-1.5 text-primary-600 underline decoration-primary-500/60 underline-offset-2 hover:bg-primary-50 hover:decoration-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:text-primary-400 dark:hover:bg-primary-900/30 dark:focus:ring-primary-400"
        >
          Mehr erfahren
        </Link>
        <button
          type="button"
          onClick={handleDismiss}
          className="min-h-touch min-w-touch rounded px-2 py-1.5 text-gray-600 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-400"
        >
          Ausblenden
        </button>
      </div>
    </div>
  );
}
