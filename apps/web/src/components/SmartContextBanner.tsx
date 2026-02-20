/** Banner shown when opening an existing conversation to indicate context continuity. */
function formatTimeAgo(dateStr: string, now = new Date()): string {
  const then = new Date(dateStr);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMs / 3_600_000);
  const diffDays = Math.floor(diffMs / 86_400_000);

  if (diffMins < 1) return "weniger als 1 Minute";
  if (diffMins < 60) return `vor ${diffMins} Minute${diffMins === 1 ? "" : "n"}`;
  if (diffHours < 24) return `vor ${diffHours} Stunde${diffHours === 1 ? "" : "n"}`;
  if (diffDays === 1) return "vor 1 Tag";
  return `vor ${diffDays} Tagen`;
}

function sessionLengthDays(firstAt: string, lastAt: string): number {
  const first = new Date(firstAt);
  const last = new Date(lastAt);
  return Math.max(0, Math.floor((last.getTime() - first.getTime()) / 86_400_000));
}

export interface SmartContextBannerProps {
  lastMessageAt: string | null | undefined;
  firstMessageAt?: string | null;
  totalTokens?: number;
}

export function SmartContextBanner({
  lastMessageAt,
  firstMessageAt,
  totalTokens = 0,
}: SmartContextBannerProps) {
  if (!lastMessageAt) return null;

  const timeAgo = formatTimeAgo(lastMessageAt);
  const sessionDays =
    firstMessageAt && lastMessageAt ? sessionLengthDays(firstMessageAt, lastMessageAt) : null;

  return (
    <div
      className="mb-4 rounded-lg border border-primary-200 bg-primary-50 px-4 py-3 text-sm text-primary-800 dark:border-primary-800 dark:bg-primary-900/30 dark:text-primary-200"
      role="status"
      aria-live="polite"
    >
      <p className="font-medium">
        Letzte Aktivität {timeAgo} – Kontext wird fortgeführt.
      </p>
      {(sessionDays !== null || totalTokens > 0) && (
        <p className="mt-1 text-xs opacity-90">
          {sessionDays !== null && sessionDays > 0 && (
            <>Sitzung: {sessionDays} Tag{sessionDays === 1 ? "" : "e"}.</>
          )}
          {sessionDays !== null && sessionDays > 0 && totalTokens > 0 && " · "}
          {totalTokens > 0 && (
            <>Tokens in dieser Sitzung: {totalTokens.toLocaleString("de-DE")}</>
          )}
        </p>
      )}
    </div>
  );
}
