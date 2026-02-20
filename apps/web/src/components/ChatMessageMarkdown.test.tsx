import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatMessageMarkdown } from "./ChatMessageMarkdown";

describe("ChatMessageMarkdown", () => {
  it("renders **Headline** on own line as heading-style", () => {
    render(<ChatMessageMarkdown content="**Themen festlegen**\n- Überlege, welche Themen." />);
    expect(screen.getByText("Themen festlegen")).toBeTruthy();
    expect(screen.getByText(/Überlege/)).toBeTruthy();
  });

  it("renders N. **Headline**: as heading", () => {
    render(<ChatMessageMarkdown content="2. **Gedanken aufschreiben**:\n- Wenn dir etwas wichtig ist." />);
    expect(screen.getByText("Gedanken aufschreiben")).toBeTruthy();
  });

  it("renders bold inline", () => {
    const { container } = render(<ChatMessageMarkdown content="Das ist **wichtig** und normal." />);
    expect(screen.getByText("wichtig")).toBeTruthy();
    const strong = container.querySelector("strong");
    expect(strong?.textContent).toBe("wichtig");
  });

  it("renders bullet list", () => {
    render(
      <ChatMessageMarkdown
        content={`- Erster Punkt
- Zweiter Punkt`}
      />
    );
    expect(screen.getByText("Erster Punkt")).toBeTruthy();
    expect(screen.getByText("Zweiter Punkt")).toBeTruthy();
  });
});
