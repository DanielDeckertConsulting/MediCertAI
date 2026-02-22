/** Auth callback — OIDC/B2C redirect target. Renders briefly then redirects to app. */
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AuthCallbackPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<"processing" | "done" | "error">("processing");

  useEffect(() => {
    // Hash (e.g. #id_token=...) or query (e.g. ?code=...) from IdP
    const hash = window.location.hash || window.location.search;
    if (!hash) {
      setStatus("done");
      navigate("/", { replace: true });
      return;
    }
    // TODO: parse tokens/code and store in auth store; then redirect
    setStatus("done");
    navigate("/", { replace: true });
  }, [navigate]);

  return (
    <div className="flex min-h-screen min-w-0 flex-col items-center justify-center bg-gray-50 p-4 pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)] dark:bg-gray-900">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        {status === "processing" ? "Anmeldung wird abgeschlossen…" : status === "error" ? "Fehler." : "Weiterleitung…"}
      </p>
    </div>
  );
}
