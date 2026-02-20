/** Safety indicator below AI responses. Small muted text, non-alarming. */
export function AIConfidenceBadge({ confidence }: { confidence?: number }) {
  const hasConfidence = confidence != null && confidence >= 0 && confidence <= 1;
  const label = hasConfidence
    ? `KI-Entwurf (Modellvertrauen: ${Math.round(confidence * 100)}%) – fachliche Prüfung erforderlich.`
    : "KI-Entwurf – fachliche Prüfung erforderlich.";
  return (
    <p
      className="mt-2 text-xs text-gray-500 dark:text-gray-400"
      role="status"
      aria-live="polite"
    >
      {label}
    </p>
  );
}
