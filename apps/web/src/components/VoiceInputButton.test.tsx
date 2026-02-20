import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { VoiceInputButton } from "./VoiceInputButton";

describe("VoiceInputButton", () => {
  const mockOnResult = vi.fn();

  beforeEach(() => {
    mockOnResult.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns null when Web Speech API is not supported", () => {
    const origWebkit = (window as Window & { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition;
    const origStd = (window as Window & { SpeechRecognition?: unknown }).SpeechRecognition;
    delete (window as Window & { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition;
    delete (window as Window & { SpeechRecognition?: unknown }).SpeechRecognition;

    const { container } = render(<VoiceInputButton onResult={mockOnResult} />);
    expect(container.firstChild).toBeNull();

    if (origWebkit !== undefined) (window as Window & { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition = origWebkit;
    if (origStd !== undefined) (window as Window & { SpeechRecognition?: unknown }).SpeechRecognition = origStd;
  });
});
