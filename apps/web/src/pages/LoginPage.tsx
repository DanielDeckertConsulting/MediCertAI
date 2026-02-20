import { EUProcessingNotice } from "../components/compliance/EUProcessingNotice";

/** Login screen — B2C redirect placeholder. */
export default function LoginPage() {
  return (
    <div className="flex min-h-screen min-w-0 flex-col items-center justify-center gap-4 bg-gray-50 p-4 dark:bg-gray-900 sm:p-8">
      <div className="min-w-0 w-full max-w-sm rounded-lg border border-gray-200 bg-white p-6 shadow dark:border-gray-700 dark:bg-gray-800 sm:p-8">
        <h1 className="mb-6 text-center text-xl font-semibold">ClinAI — Anmelden</h1>
        <p className="mb-6 text-center text-sm text-gray-600 dark:text-gray-400">
          Azure B2C-Anmeldung wird hier eingebunden.
        </p>
        <button
          type="button"
          className="min-h-touch min-w-touch w-full rounded-lg bg-primary-500 px-4 py-3 text-white hover:bg-primary-600"
          onClick={() => (window.location.href = "/")}
        >
          Zum Chat (Dev-Bypass)
        </button>
      </div>
      <div className="w-full max-w-sm">
        <EUProcessingNotice />
      </div>
    </div>
  );
}
