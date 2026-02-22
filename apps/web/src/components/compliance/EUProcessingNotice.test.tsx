import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { EUProcessingNotice } from "./EUProcessingNotice";

describe("EUProcessingNotice", () => {
  const storage: Record<string, string> = {};
  const localStorageMock = {
    getItem: vi.fn((key: string) => storage[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete storage[key];
    }),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };

  beforeEach(() => {
    Object.defineProperty(window, "localStorage", {
      value: localStorageMock,
      writable: true,
    });
    Object.keys(storage).forEach((k) => delete storage[k]);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders banner with main text", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    expect(screen.getAllByText("Alle Daten werden innerhalb der EU verarbeitet.").length).toBeGreaterThanOrEqual(1);
  });

  it("renders Mehr erfahren link pointing to /privacy", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    const links = screen.getAllByRole("link", { name: /Mehr erfahren/i });
    expect(links.length).toBeGreaterThanOrEqual(1);
    expect(links[0]!.getAttribute("href")).toBe("/privacy");
  });

  it("renders Ausblenden button", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    const buttons = screen.getAllByRole("button", { name: /Ausblenden/i });
    expect(buttons.length).toBeGreaterThanOrEqual(1);
  });

  it("hides banner when Ausblenden is clicked", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    expect(screen.getAllByText("Alle Daten werden innerhalb der EU verarbeitet.").length).toBeGreaterThanOrEqual(1);

    screen.getAllByRole("button", { name: /Ausblenden/i }).forEach((btn) => fireEvent.click(btn));

    expect(screen.queryByText("Alle Daten werden innerhalb der EU verarbeitet.")).toBeNull();
  });

  it("persists dismissal in localStorage", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    const dismissBtn = screen.getAllByRole("button", { name: /Ausblenden/i })[0];
    if (dismissBtn) fireEvent.click(dismissBtn);

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      "mentalcarepilot.eu_processing_notice.dismissed.v1",
      "true"
    );
  });

  it("has role=status for accessibility", () => {
    render(
      <MemoryRouter>
        <EUProcessingNotice />
      </MemoryRouter>
    );
    const region = document.querySelector('[role="status"]');
    expect(region).toBeTruthy();
  });
});
