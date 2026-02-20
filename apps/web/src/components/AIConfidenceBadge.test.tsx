import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AIConfidenceBadge } from "./AIConfidenceBadge";

describe("AIConfidenceBadge", () => {
  it("shows static safety text when no confidence", () => {
    render(<AIConfidenceBadge />);
    expect(
      screen.getByText(/KI-Entwurf – fachliche Prüfung erforderlich\./)
    ).toBeTruthy();
    expect(screen.queryByText(/Modellvertrauen/)).toBeNull();
  });

  it("shows Modellvertrauen when confidence provided", () => {
    render(<AIConfidenceBadge confidence={0.82} />);
    expect(
      screen.getByText(/KI-Entwurf \(Modellvertrauen: 82%\) – fachliche Prüfung erforderlich\./)
    ).toBeTruthy();
  });

  it("rounds confidence to integer percentage", () => {
    render(<AIConfidenceBadge confidence={0.856} />);
    expect(screen.getByText(/86%/)).toBeTruthy();
  });
});
