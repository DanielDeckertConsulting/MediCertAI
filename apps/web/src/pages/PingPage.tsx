/** Minimal ping: calls /health and shows result. */
import { useQuery } from "@tanstack/react-query";
import { healthCheck } from "../api/client";

export default function PingPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: healthCheck,
  });

  return (
    <div className="min-w-0 max-w-full">
      <h2 className="mb-4 text-lg font-semibold">Health Check</h2>
      {isLoading && <p className="text-gray-500">Laden...</p>}
      {error && (
        <p className="text-red-600">Fehler: {(error as Error).message}</p>
      )}
      {data && (
        <pre className="max-w-full overflow-x-auto break-words rounded border border-gray-200 bg-gray-50 p-4 text-sm dark:border-gray-700 dark:bg-gray-800">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
