/** Voice-to-text dictation using browser Web Speech API. No audio stored or uploaded. */
import { useCallback, useEffect, useRef, useState } from "react";

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

interface SpeechRecognitionInstance extends EventTarget {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((ev: SpeechRecognitionEvent) => void) | null;
  onerror: ((ev: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message?: string;
}

export type VoiceInputStatus =
  | "idle"
  | "recording"
  | "transcribing"
  | "unsupported"
  | "permission-denied"
  | "error";

export function VoiceInputButton({
  onResult,
  disabled,
  "aria-label": ariaLabel = "Diktieren",
}: {
  onResult: (text: string) => void;
  disabled?: boolean;
  "aria-label"?: string;
}) {
  const [status, setStatus] = useState<VoiceInputStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptsRef = useRef<string>("");
  const onResultRef = useRef(onResult);
  onResultRef.current = onResult;

  const getRecognition = useCallback((): SpeechRecognitionInstance | null => {
    if (typeof window === "undefined") return null;
    const Ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Ctor) return null;
    return new Ctor();
  }, []);

  const isSupported = getRecognition() !== null;

  const stopRecording = useCallback(() => {
    const rec = recognitionRef.current;
    if (rec) {
      try {
        rec.stop();
      } catch {
        // no-op if already stopped
      }
      recognitionRef.current = null;
    }
  }, []);

  const startRecording = useCallback(() => {
    if (!isSupported) {
      setStatus("unsupported");
      setErrorMessage("Spracherkennung wird in diesem Browser nicht unterstützt.");
      return;
    }

    setErrorMessage(null);
    setStatus("recording");
    transcriptsRef.current = "";

    const rec = getRecognition();
    if (!rec) return;

    rec.lang = "de-DE";
    rec.continuous = true;
    rec.interimResults = true;

    rec.onresult = (ev: SpeechRecognitionEvent) => {
      const results = ev.results;
      let full = "";
      for (let i = 0; i < results.length; i++) {
        full += results[i]?.[0]?.transcript ?? "";
      }
      transcriptsRef.current = full;
      if (full.trim()) setStatus("transcribing");
    };

    rec.onerror = (ev: SpeechRecognitionErrorEvent) => {
      if (ev.error === "not-allowed" || ev.error === "service-not-allowed") {
        setStatus("permission-denied");
        setErrorMessage("Mikrofon-Zugriff wurde abgelehnt.");
      } else if (ev.error === "no-speech") {
        setStatus("idle");
        setErrorMessage("Keine Sprache erkannt. Bitte erneut versuchen.");
      } else {
        setStatus("error");
        setErrorMessage(ev.message ?? `Fehler: ${ev.error}`);
      }
      recognitionRef.current = null;
    };

    rec.onend = () => {
      recognitionRef.current = null;
      const text = transcriptsRef.current.trim();
      if (text) {
        onResultRef.current(text);
      }
      setStatus("idle");
    };

    recognitionRef.current = rec;
    try {
      rec.start();
    } catch {
      setStatus("error");
      setErrorMessage("Aufnahme konnte nicht gestartet werden.");
      recognitionRef.current = null;
    }
  }, [isSupported, getRecognition]);

  const handleToggle = useCallback(() => {
    if (status === "recording" || status === "transcribing") {
      stopRecording();
      return;
    }
    startRecording();
  }, [status, startRecording, stopRecording]);

  useEffect(() => {
    if (errorMessage) {
      const t = setTimeout(() => setErrorMessage(null), 5000);
      return () => clearTimeout(t);
    }
  }, [errorMessage]);

  if (!isSupported) {
    return null;
  }

  const isRecording = status === "recording" || status === "transcribing";

  return (
    <div className="relative flex items-center gap-1">
      <button
        type="button"
        onClick={handleToggle}
        disabled={disabled}
        className={`min-h-touch min-w-touch shrink-0 rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 ${
          isRecording
            ? "bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400"
            : "text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600 dark:hover:text-gray-300"
        }`}
        aria-label={isRecording ? "Aufnahme beenden" : ariaLabel}
        aria-pressed={isRecording}
      >
        <MicrophoneIcon isRecording={isRecording} />
      </button>
      {isRecording && (
        <span className="text-xs text-gray-500 dark:text-gray-400">Aufnahme läuft…</span>
      )}
      {errorMessage && (
        <span
          className="absolute left-0 top-full z-10 mt-1 max-w-[200px] text-xs text-red-600 dark:text-red-400"
          role="alert"
        >
          {errorMessage}
        </span>
      )}
    </div>
  );
}

function MicrophoneIcon({ isRecording }: { isRecording: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-5 w-5"
      aria-hidden
    >
      {isRecording ? (
        <path d="M6 6h12v12H6V6z" />
      ) : (
        <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3zm0 14a5 5 0 0 0 5-5V9h2v2a7 7 0 0 1-14 0V9h2v2a5 5 0 0 0 5 5z" />
      )}
    </svg>
  );
}
