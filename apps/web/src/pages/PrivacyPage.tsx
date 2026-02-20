/**
 * Datenschutz — minimal privacy page.
 * Factual only; no claims about unimplemented features.
 */
import { Link } from "react-router-dom";

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 px-4 py-8">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
        Datenschutz
      </h1>

      <section>
        <h2 className="mb-3 text-lg font-medium text-gray-800 dark:text-gray-200">
          Datenverarbeitung innerhalb der EU
        </h2>
        <ul className="list-disc space-y-2 pl-6 text-sm text-gray-700 dark:text-gray-300">
          <li>Verarbeitung erfolgt in Azure Region Germany West Central.</li>
          <li>Es wird nicht mit Kundendaten trainiert.</li>
          <li>Die Anonymisierungs-Option reduziert personenbezogene Angaben in eingegebenen Texten.</li>
          <li>Chat-Export (Textformat) und Löschen von Chats sind verfügbar.</li>
        </ul>
      </section>

      <p>
        <Link
          to="/chat"
          className="min-h-touch min-w-touch inline-flex items-center text-primary-600 underline hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
        >
          ← Zurück zum Chat
        </Link>
      </p>
    </div>
  );
}
