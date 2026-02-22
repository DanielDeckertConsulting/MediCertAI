import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Layout from "./Layout";

describe("Layout", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders mobile header with hamburger button", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    );
    const hamburger = screen.getByRole("button", { name: /Menü öffnen/i });
    expect(hamburger).toBeTruthy();
  });

  it("renders nav links (Chat appears in sidebar)", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    );
    const chatLinks = screen.getAllByRole("link", { name: /^Chat$/ });
    expect(chatLinks.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /Ordner/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /Assistenzmodus/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /Admin/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: /Ping/ }).length).toBeGreaterThanOrEqual(1);
  });

  it("app brand visible", () => {
    render(
      <MemoryRouter>
        <Layout />
      </MemoryRouter>
    );
    expect(screen.getAllByText("MentalCarePilot").length).toBeGreaterThanOrEqual(1);
  });
});
