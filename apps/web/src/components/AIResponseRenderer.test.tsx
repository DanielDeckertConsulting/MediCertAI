import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import AIResponseRenderer from "./AIResponseRenderer";

const blocks = [
  { type: "heading", content: "Test Heading", level: 2 },
  { type: "paragraph", content: "Some paragraph text." },
  { type: "list", items: ["item 1", "item 2"] },
  { type: "action", label: "Do It", command: "do_it", confidence: 0.9 },
];

describe("AIResponseRenderer", () => {
  it("renders heading", () => {
    render(<AIResponseRenderer blocks={[blocks[0]!]} />);
    expect(screen.getByText("Test Heading")).toBeTruthy();
  });

  it("renders paragraph", () => {
    render(<AIResponseRenderer blocks={[blocks[1]!]} />);
    expect(screen.getByText("Some paragraph text.")).toBeTruthy();
  });

  it("renders list items", () => {
    render(<AIResponseRenderer blocks={[blocks[2]!]} />);
    expect(screen.getByText("item 1")).toBeTruthy();
    expect(screen.getByText("item 2")).toBeTruthy();
  });

  it("renders action button", () => {
    render(<AIResponseRenderer blocks={[blocks[3]!]} />);
    expect(screen.getByRole("button", { name: /Do It/i })).toBeTruthy();
  });

  it("shows confidence badge when < 1", () => {
    render(<AIResponseRenderer blocks={[]} confidence={0.85} />);
    expect(screen.getByText(/85%/)).toBeTruthy();
  });

  it("shows needs review badge when flagged", () => {
    render(
      <AIResponseRenderer blocks={[]} confidence={0.8} needsReview />
    );
    expect(screen.getByText(/Review empfohlen/)).toBeTruthy();
  });
});
