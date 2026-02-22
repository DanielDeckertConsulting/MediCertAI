import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ChatSummary, FolderOut } from "../api/client";
import * as api from "../api/client";
import ChatPage from "./ChatPage";

vi.mock("../api/client", () => ({
  createChat: vi.fn(),
  deleteChat: vi.fn(),
  exportChat: vi.fn(),
  finalizeChat: vi.fn(),
  generateCaseSummary: vi.fn(),
  getChat: vi.fn(),
  getStructuredDocument: vi.fn(),
  putStructuredDocument: vi.fn(),
  convertToStructuredDocument: vi.fn(),
  listChats: vi.fn(),
  listFolders: vi.fn(),
  listInterventions: vi.fn(),
  listPrompts: vi.fn(),
  patchChat: vi.fn(),
  STRUCTURED_DOC_FIELDS: [
    "session_context",
    "presenting_symptoms",
    "resources",
    "interventions",
    "homework",
    "risk_assessment",
    "progress_evaluation",
  ],
}));

vi.mock("../api/streamChat", () => ({
  streamChatMessage: vi.fn(),
}));

const foldersFixture: FolderOut[] = [
  { id: "folder-1", name: "Traumatherapie", created_at: "2026-02-01T10:00:00.000Z" },
];

const chatsFixture: ChatSummary[] = [
  {
    id: "chat-folder",
    title: "Therapie Notiz",
    updated_at: "2026-02-05T09:00:00.000Z",
    is_favorite: false,
    folder_id: "folder-1",
    status: "active",
  },
  {
    id: "chat-unfiled",
    title: "Unfiled Verlauf",
    updated_at: "2026-02-06T09:00:00.000Z",
    is_favorite: true,
    folder_id: null,
    status: "active",
  },
];

function renderChatPage(initialEntry = "/chat") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:conversationId" element={<ChatPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ChatPage desktop chat layout", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(api.listFolders).mockResolvedValue(foldersFixture);
    vi.mocked(api.listChats).mockResolvedValue(chatsFixture);
    vi.mocked(api.listPrompts).mockResolvedValue([]);
    vi.mocked(api.listInterventions).mockResolvedValue([]);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders desktop old chats as dedicated scroll container", async () => {
    renderChatPage();

    const oldChats = await screen.findByLabelText("Alte Chats");
    expect(oldChats.className.includes("overflow-y-auto")).toBe(true);
    expect(within(oldChats).getByText("Unfiled Verlauf")).toBeTruthy();
  });

  it("shows folder groups collapsed/expanded on desktop", async () => {
    renderChatPage();

    const folderGroup = await screen.findByLabelText("Ordnergruppe Traumatherapie");
    expect(within(folderGroup).getByText("Therapie Notiz")).toBeTruthy();

    fireEvent.click(within(folderGroup).getByRole("button", { name: /Ordner Traumatherapie einklappen/i }));

    expect(within(folderGroup).queryByText("Therapie Notiz")).toBeNull();
  });

  it("uses meatball menu actions instead of inline desktop icons", async () => {
    renderChatPage();

    const oldChats = await screen.findByLabelText("Alte Chats");
    expect(within(oldChats).queryByRole("button", { name: "Umbenennen" })).toBeNull();

    fireEvent.click(within(oldChats).getByRole("button", { name: /Aktionen für Unfiled Verlauf/i }));

    expect(await screen.findByRole("menuitem", { name: "Umbenennen" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Export als PDF" })).toBeTruthy();
  });

  it("keeps mobile inline actions available for regression safety", async () => {
    renderChatPage();

    await screen.findByText("Unfiled Verlauf");
    const mobileList = document.querySelector(".md\\:hidden");
    expect(mobileList).toBeTruthy();
    if (!mobileList) return;

    expect(within(mobileList as HTMLElement).getByRole("button", { name: "Umbenennen" })).toBeTruthy();
  });

  it("persists desktop folder collapse state in localStorage", async () => {
    const firstRender = renderChatPage();

    const folderGroup = await screen.findByLabelText("Ordnergruppe Traumatherapie");
    fireEvent.click(within(folderGroup).getByRole("button", { name: /Ordner Traumatherapie einklappen/i }));
    firstRender.unmount();

    renderChatPage();

    const folderGroupAfterReload = await screen.findByLabelText("Ordnergruppe Traumatherapie");
    expect(within(folderGroupAfterReload).queryByText("Therapie Notiz")).toBeNull();
  });
});
