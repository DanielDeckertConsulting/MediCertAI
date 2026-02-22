/** Chat — streaming interface with assist modes and anonymization. Mobile-first: cards on small screens, sidebar on md+. */
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  createChat,
  deleteChat,
  exportChat,
  finalizeChat,
  generateCaseSummary,
  getChat,
  getStructuredDocument,
  putStructuredDocument,
  convertToStructuredDocument,
  listChats,
  listFolders,
  listInterventions,
  listPrompts,
  patchChat,
  type CaseSummaryOut,
  type ChatSummary,
  type ExportFormat,
  type FolderOut,
  type MessageOut,
  type PromptSummary,
  type StructuredContent,
  type StructuredDocumentOut,
  STRUCTURED_DOC_FIELDS,
} from "../api/client";
import { streamChatMessage } from "../api/streamChat";
import { ChatMessageMarkdown } from "../components/ChatMessageMarkdown";
import { AIConfidenceBadge } from "../components/AIConfidenceBadge";
import { ChatListItem } from "../components/chat/ChatListItem";
import { FolderGroup } from "../components/chat/FolderGroup";
import { SmartContextBanner } from "../components/SmartContextBanner";
import { CaseSummaryModal } from "../components/CaseSummaryModal";
import { EUProcessingNotice } from "../components/compliance/EUProcessingNotice";
import { VoiceInputButton } from "../components/VoiceInputButton";

/** Custom dropdown for assist mode — avoids native select clipping on mobile. */
function AssistModeSelect({
  value,
  options,
  onChange,
}: {
  value: string;
  options: PromptSummary[];
  onChange: (key: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = options.find((p) => p.key === value);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="min-h-touch min-w-touch flex items-center gap-2 rounded border border-gray-300 bg-white px-3 py-2.5 text-left text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Assistenzmodus"
      >
        <span>{selected?.display_name ?? value}</span>
        <span className="ml-1 shrink-0 text-gray-500 dark:text-gray-400" aria-hidden>
          {open ? "▴" : "▾"}
        </span>
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute bottom-full left-0 z-50 mb-1 w-full min-w-[200px] overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          style={{ maxHeight: "min(280px, 50vh)" }}
        >
          {options.map((p) => (
            <li key={p.key} role="option" aria-selected={p.key === value}>
              <button
                type="button"
                onClick={() => {
                  onChange(p.key);
                  setOpen(false);
                }}
                className={`flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm leading-relaxed transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  p.key === value ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : ""
                }`}
              >
                {p.display_name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/** Export dropdown: TXT or PDF. */
function ExportDropdown({
  chatId,
  onExport,
  disabled,
}: {
  chatId: string;
  onExport: (id: string, format: ExportFormat, e: React.MouseEvent) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="min-h-touch min-w-touch rounded p-2 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600 disabled:opacity-50"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Exportieren"
      >
        ⬇
      </button>
      {open && (
        <ul
          role="menu"
          className="absolute right-0 bottom-full z-50 mb-1 min-w-[160px] overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800 dark:text-white"
        >
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                onExport(chatId, "txt", e);
                setOpen(false);
              }}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Export als TXT
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                onExport(chatId, "pdf", e);
                setOpen(false);
              }}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Export als PDF
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}

/** Folder select dropdown for assigning chat to folder. */
function FolderSelect({
  value,
  folders,
  onChange,
  disabled,
}: {
  value: string | null;
  folders: FolderOut[];
  onChange: (folderId: string | null) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selectedLabel =
    value === null || value === ""
      ? "Nicht zugeordnet"
      : folders.find((f) => f.id === value)?.name ?? "Nicht zugeordnet";

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    if (open) document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="min-h-touch min-w-touch flex items-center gap-2 rounded border border-gray-300 bg-white px-3 py-2.5 text-left text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white disabled:opacity-50"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Ordner auswählen"
      >
        <span className="truncate">{selectedLabel}</span>
        <span className="ml-1 shrink-0 text-gray-500 dark:text-gray-400" aria-hidden>
          {open ? "▴" : "▾"}
        </span>
      </button>
      {open && (
        <ul
          role="listbox"
          className="absolute bottom-full left-0 z-50 mb-1 w-full min-w-[200px] max-w-[280px] overflow-y-auto rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800 dark:text-white"
          style={{ maxHeight: "min(240px, 50vh)" }}
        >
          <li role="option" aria-selected={value === null || value === ""}>
            <button
              type="button"
              onClick={() => {
                onChange(null);
                setOpen(false);
              }}
              className={`flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 ${
                !value ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : ""
              }`}
            >
              Nicht zugeordnet
            </button>
          </li>
          {folders.map((f) => (
            <li key={f.id} role="option" aria-selected={value === f.id}>
              <button
                type="button"
                onClick={() => {
                  onChange(f.id);
                  setOpen(false);
                }}
                className={`flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 ${
                  value === f.id ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : ""
                }`}
              >
                {f.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const ASSIST_DEFAULTS: PromptSummary[] = [
  { key: "CHAT_WITH_AI", display_name: "Chat with AI", version: 1 },
  { key: "SESSION_SUMMARY", display_name: "Session Summary", version: 1 },
  { key: "STRUCTURED_DOC", display_name: "Structured Documentation", version: 1 },
  { key: "THERAPY_PLAN", display_name: "Therapy Plan Draft", version: 1 },
  { key: "RISK_ANALYSIS", display_name: "Risk Analysis", version: 1 },
  { key: "CASE_REFLECTION", display_name: "Case Reflection", version: 1 },
];

/** Chat list: mobile unchanged, desktop with collapsible folders and scrollable area. */
function ChatList({
  chats,
  chatId,
  titleFilter,
  onFilterChange,
  folders,
  selectedFolderId,
  onFolderSelect,
  onCreateChat,
  onSelectChat,
  onRename,
  onFavorite,
  onExport,
  onDelete,
  onMoveToFolder,
  onGenerateCaseSummary,
  editingId,
  editingTitle,
  onEditingChange,
  isLoading,
  exportLoading,
  caseSummaryLoading,
}: {
  chats: ChatSummary[];
  chatId: string | null;
  titleFilter: string;
  onFilterChange: (v: string) => void;
  folders: FolderOut[];
  selectedFolderId: string | null;
  onFolderSelect: (id: string | null) => void;
  onCreateChat: () => void;
  onSelectChat: (id: string) => void;
  onRename: (id: string) => void;
  onFavorite: (c: ChatSummary, e: React.MouseEvent) => void;
  onExport: (id: string, format: ExportFormat, e: React.MouseEvent) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onMoveToFolder: (id: string, folderId: string | null) => void;
  onGenerateCaseSummary?: () => void;
  editingId: string | null;
  editingTitle: string;
  onEditingChange: (id: string | null, title: string) => void;
  isLoading?: boolean;
  exportLoading?: boolean;
  caseSummaryLoading?: boolean;
}) {
  const renderChatItem = (c: ChatSummary) => (
    <ChatListItem
      key={c.id}
      chat={c}
      isSelected={chatId === c.id}
      isEditing={editingId === c.id}
      editingTitle={editingTitle}
      onSelect={() => onSelectChat(c.id)}
      onRename={() => onRename(c.id)}
      onEditingChange={onEditingChange}
      onFavorite={onFavorite}
      onExport={onExport}
      onDelete={onDelete}
      onMoveToFolder={onMoveToFolder}
      folders={folders}
      exportLoading={exportLoading ?? false}
    />
  );

  const showCollapsibleFolders = selectedFolderId === null && chats.length > 0;
  const chatsByFolder = showCollapsibleFolders
    ? folders.reduce<Record<string, ChatSummary[]>>((acc, f) => {
        acc[f.id] = chats.filter((c) => c.folder_id === f.id);
        return acc;
      }, {})
    : {};
  const unfiledChats = showCollapsibleFolders
    ? chats.filter((c) => !c.folder_id || c.folder_id === "")
    : [];
  const foldersWithChats = showCollapsibleFolders
    ? folders.filter((f) => (chatsByFolder[f.id]?.length ?? 0) > 0)
    : [];

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 md:flex md:flex-col md:overflow-hidden">
      <div className="shrink-0 border-b border-gray-200 p-2 dark:border-gray-600">
        <p className="mb-1 px-2 text-xs font-medium text-gray-500 dark:text-gray-400">Ordner</p>
        <div className="flex flex-wrap gap-1 overflow-y-auto">
          <button
            type="button"
            onClick={() => onFolderSelect(null)}
            className={`min-h-touch rounded px-2.5 py-1.5 text-left text-sm transition-colors ${
              selectedFolderId === null ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : "hover:bg-gray-100 dark:hover:bg-gray-700"
            }`}
          >
            Alle
          </button>
          <button
            type="button"
            onClick={() => onFolderSelect("unfiled")}
            className={`min-h-touch rounded px-2.5 py-1.5 text-left text-sm transition-colors ${
              selectedFolderId === "unfiled" ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : "hover:bg-gray-100 dark:hover:bg-gray-700"
            }`}
          >
            Nicht zugeordnet
          </button>
          {folders.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => onFolderSelect(f.id)}
              className={`min-h-touch rounded px-2.5 py-1.5 text-left text-sm transition-colors ${
                selectedFolderId === f.id ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : "hover:bg-gray-100 dark:hover:bg-gray-700"
              }`}
            >
              {f.name}
            </button>
          ))}
        </div>
        {selectedFolderId &&
          selectedFolderId !== "unfiled" &&
          chats.length > 0 &&
          onGenerateCaseSummary && (
          <div className="mt-2 px-2">
            <button
              type="button"
              onClick={onGenerateCaseSummary}
              disabled={caseSummaryLoading}
              className="min-h-touch w-full rounded border border-primary-500 bg-transparent px-3 py-2 text-sm font-medium text-primary-600 hover:bg-primary-50 dark:border-primary-400 dark:text-primary-400 dark:hover:bg-primary-900/30 disabled:opacity-50"
            >
              {caseSummaryLoading ? "Wird erstellt…" : "Fallzusammenfassung generieren"}
            </button>
          </div>
        )}
      </div>
      <div className="shrink-0 border-b border-gray-200 p-3 dark:border-gray-600">
        <button
          type="button"
          onClick={onCreateChat}
          className="min-h-touch min-w-touch w-full rounded-lg bg-primary-500 px-4 py-3 text-sm font-medium text-white hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
        >
          + Neuer Chat
        </button>
        <input
          type="search"
          placeholder="Chats durchsuchen..."
          value={titleFilter}
          onChange={(e) => onFilterChange(e.target.value)}
          className="mt-2 min-h-[44px] w-full rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          aria-label="Chat-Titel durchsuchen"
        />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-2">
        {isLoading ? (
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Laden...</p>
        ) : chats.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Keine Chats. Erstellen Sie einen neuen.
          </p>
        ) : showCollapsibleFolders ? (
          <div className="space-y-1">
            {foldersWithChats.map((f) => (
              <FolderGroup
                key={f.id}
                folder={f}
                chats={chatsByFolder[f.id] ?? []}
                renderChatItem={renderChatItem}
              />
            ))}
            {unfiledChats.length > 0 && (
              <div className="border-b border-gray-100 last:border-b-0 dark:border-gray-700">
                <p className="mb-1 px-2 py-1 text-xs font-medium text-gray-500 dark:text-gray-400">
                  Nicht zugeordnet
                </p>
                <ul className="space-y-0.5 pl-2 pr-1 pb-1">
                  {unfiledChats.map((c) => renderChatItem(c))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <ul className="space-y-2">
            {chats.map((c) => renderChatItem(c))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [titleFilter, setTitleFilter] = useState("");
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const [assistMode, setAssistMode] = useState<string>("CHAT_WITH_AI");
  const [anonymizationEnabled, setAnonymizationEnabled] = useState(true);
  const [safeMode, setSafeMode] = useState(false);
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [exportLoading, setExportLoading] = useState(false);
  const [caseSummaryOpen, setCaseSummaryOpen] = useState(false);
  const [caseSummaryLoading, setCaseSummaryLoading] = useState(false);
  const [caseSummaryData, setCaseSummaryData] = useState<CaseSummaryOut | null>(null);
  const [caseSummaryError, setCaseSummaryError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"chat" | "structured">("chat");
  const [structuredFormContent, setStructuredFormContent] = useState<StructuredContent>(() =>
    STRUCTURED_DOC_FIELDS.reduce((acc, k) => ({ ...acc, [k]: "" }), {} as StructuredContent)
  );
  const [structuredSaveLoading, setStructuredSaveLoading] = useState(false);
  const [convertLoading, setConvertLoading] = useState(false);
  const [interventionDrawerOpen, setInterventionDrawerOpen] = useState(false);

  const chatId = conversationId ?? null;

  const { data: folders = [] } = useQuery({
    queryKey: ["folders"],
    queryFn: listFolders,
  });

  const { data: chats = [], refetch: refetchChats, isError: chatsError, isLoading: chatsLoading } = useQuery({
    queryKey: ["chats", selectedFolderId],
    queryFn: () =>
      selectedFolderId === "unfiled"
        ? listChats({ unfiledOnly: true })
        : selectedFolderId
          ? listChats({ folderId: selectedFolderId })
          : listChats(),
  });

  const { data: prompts = [], isError: promptsError } = useQuery({
    queryKey: ["prompts"],
    queryFn: listPrompts,
  });

  const ASSIST_OPTIONS: PromptSummary[] =
    prompts.length > 0 ? prompts : ASSIST_DEFAULTS;

  const { data: chatDetail, refetch: refetchChat, isError: chatDetailError } = useQuery({
    queryKey: ["chat", chatId],
    queryFn: () => getChat(chatId!),
    enabled: !!chatId,
    retry: false,
  });

  const emptyStructuredContent = (): StructuredContent =>
    STRUCTURED_DOC_FIELDS.reduce((acc, k) => ({ ...acc, [k]: "" }), {} as StructuredContent);

  const {
    data: structuredDoc,
    refetch: refetchStructuredDoc,
    isFetching: structuredDocLoading,
  } = useQuery({
    queryKey: ["structured-document", chatId],
    queryFn: async (): Promise<StructuredDocumentOut | { content: StructuredContent; version: number }> => {
      try {
        return await getStructuredDocument(chatId!);
      } catch (e) {
        if ((e as Error).message === "NOT_FOUND")
          return { content: emptyStructuredContent(), version: 0 } as StructuredDocumentOut & { content: StructuredContent };
        throw e;
      }
    },
    enabled: !!chatId && viewMode === "structured",
    retry: false,
  });

  const { data: interventions = [] } = useQuery({
    queryKey: ["interventions"],
    queryFn: () => listInterventions(),
    enabled: interventionDrawerOpen,
  });

  // Redirect to chat list when loaded chat doesn't exist (404)
  useEffect(() => {
    if (chatId && chatDetailError) {
      navigate("/chat", { replace: true });
      refetchChats();
    }
  }, [chatId, chatDetailError, navigate, refetchChats]);

  const filteredChats = titleFilter
    ? chats.filter((c) => c.title.toLowerCase().includes(titleFilter.toLowerCase()))
    : chats;

  const handleCreateChat = useCallback(async () => {
    const created = await createChat();
    await refetchChats();
    navigate(`/chat/${created.id}`);
  }, [navigate, refetchChats]);

  const handleSelectChat = useCallback(
    (id: string) => {
      navigate(`/chat/${id}`);
    },
    [navigate]
  );

  const handleDeleteChat = useCallback(
    async (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      await deleteChat(id);
      await refetchChats();
      if (chatId === id) navigate("/chat");
    },
    [chatId, navigate, refetchChats]
  );

  const handleRename = useCallback(
    async (id: string) => {
      if (!editingTitle.trim()) {
        setEditingId(null);
        return;
      }
      await patchChat(id, { title: editingTitle.trim() });
      setEditingId(null);
      await refetchChats();
      if (chatId === id) await refetchChat();
    },
    [chatId, editingTitle, refetchChats, refetchChat]
  );

  const handleFavorite = useCallback(
    async (c: ChatSummary, e: React.MouseEvent) => {
      e.stopPropagation();
      await patchChat(c.id, { is_favorite: !c.is_favorite });
      await refetchChats();
      if (chatId === c.id) await refetchChat();
    },
    [chatId, refetchChats, refetchChat]
  );

  const handleFolderChange = useCallback(
    async (folderId: string | null) => {
      if (!chatId) return;
      await patchChat(chatId, { folder_id: folderId });
      await refetchChats();
      await refetchChat();
    },
    [chatId, refetchChats, refetchChat]
  );

  const handleMoveToFolder = useCallback(
    async (id: string, folderId: string | null) => {
      await patchChat(id, { folder_id: folderId });
      await refetchChats();
      if (chatId === id) await refetchChat();
    },
    [chatId, refetchChats, refetchChat]
  );

  const handleFinalize = useCallback(
    async (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await finalizeChat(id);
        await refetchChat();
        await refetchChats();
      } catch (err) {
        alert(err instanceof Error ? err.message : "Sperren fehlgeschlagen.");
      }
    },
    [refetchChat, refetchChats]
  );

  const handleExport = useCallback(
    async (id: string, format: ExportFormat, e: React.MouseEvent) => {
      e.stopPropagation();
      if (exportLoading) return;
      setExportLoading(true);
      try {
        const blob = await exportChat(id, format);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const date = new Date().toISOString().slice(0, 10);
        a.download = `clinai-chat-${id.slice(0, 8)}-${date}.${format}`;
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Export fehlgeschlagen.";
        alert(msg);
      } finally {
        setExportLoading(false);
      }
    },
    [exportLoading]
  );

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || !chatId || isStreaming) return;

    let currentChatId = chatId;
    if (!currentChatId) {
      const created = await createChat();
      currentChatId = created.id;
      await refetchChats();
      navigate(`/chat/${currentChatId}`);
    }

    setInput("");
    setIsStreaming(true);
    setStreamingContent("");

    await streamChatMessage(
      currentChatId,
      {
        assist_mode_key: assistMode,
        anonymization_enabled: anonymizationEnabled,
        safe_mode: safeMode,
        user_message: text,
      },
      {
        onToken: (t) => setStreamingContent((prev) => prev + t),
        onDone: () => {
          setIsStreaming(false);
          setStreamingContent("");
          refetchChat();
          refetchChats();
        },
        onError: (msg) => {
          setIsStreaming(false);
          setStreamingContent("");
          if (msg.toLowerCase().includes("chat not found")) {
            navigate("/chat");
            refetchChats();
          }
          alert(msg);
        },
      }
    );
  }, [input, chatId, isStreaming, assistMode, anonymizationEnabled, safeMode, navigate, refetchChats, refetchChat]);

  const handleEditingChange = useCallback((id: string | null, title: string) => {
    setEditingId(id);
    setEditingTitle(title);
  }, []);

  const handleGenerateCaseSummary = useCallback(async () => {
    const ids = filteredChats.map((c) => c.id);
    if (ids.length === 0) return;
    setCaseSummaryOpen(true);
    setCaseSummaryLoading(true);
    setCaseSummaryError(null);
    setCaseSummaryData(null);
    try {
      const result = await generateCaseSummary(ids);
      setCaseSummaryData(result);
    } catch (e) {
      setCaseSummaryError((e as Error).message);
    } finally {
      setCaseSummaryLoading(false);
    }
  }, [filteredChats]);

  const handleCloseCaseSummary = useCallback(() => {
    setCaseSummaryOpen(false);
    setCaseSummaryData(null);
    setCaseSummaryError(null);
  }, []);

  const handleConvertToStructured = useCallback(async () => {
    if (!chatId || convertLoading) return;
    setConvertLoading(true);
    try {
      await convertToStructuredDocument(chatId);
      await refetchStructuredDoc();
      setViewMode("structured");
    } catch (e) {
      alert((e as Error).message || "Konvertierung fehlgeschlagen.");
    } finally {
      setConvertLoading(false);
    }
  }, [chatId, convertLoading, refetchStructuredDoc]);

  const handleSaveStructured = useCallback(
    async (content: StructuredContent) => {
      if (!chatId || structuredSaveLoading) return;
      setStructuredSaveLoading(true);
      try {
        await putStructuredDocument(chatId, content);
        await refetchStructuredDoc();
      } catch (e) {
        alert((e as Error).message || "Speichern fehlgeschlagen.");
      } finally {
        setStructuredSaveLoading(false);
      }
    },
    [chatId, structuredSaveLoading, refetchStructuredDoc]
  );

  const handleSafeModeToggle = useCallback(
    async (checked: boolean) => {
      setSafeMode(checked);
      if (chatId) {
        try {
          await patchChat(chatId, { metadata: { safe_mode: checked } });
          await refetchChat();
        } catch {
          setSafeMode(!checked);
        }
      }
    },
    [chatId, refetchChat]
  );

  const messages: MessageOut[] = chatDetail?.messages ?? [];
  const isFinalized = chatDetail?.status === "finalized";

  // Initialize safe_mode from conversation metadata when chat loads
  useEffect(() => {
    if (!chatId) {
      setSafeMode(false);
    } else if (chatDetail?.id === chatId) {
      setSafeMode(!!chatDetail.metadata?.safe_mode);
    }
  }, [chatId, chatDetail?.id, chatDetail?.metadata]);

  // Sync structured form when document loads
  useEffect(() => {
    if (structuredDoc?.content) {
      const c = structuredDoc.content as StructuredContent;
      setStructuredFormContent((prev) =>
        STRUCTURED_DOC_FIELDS.reduce(
          (acc, k) => ({ ...acc, [k]: c[k] ?? prev[k] ?? "" }),
          {} as StructuredContent
        )
      );
    }
  }, [structuredDoc?.content, structuredDoc?.version]);
  const displayMessages = streamingContent
    ? [...messages, { id: "streaming", role: "assistant", content: streamingContent, created_at: "" }]
    : messages;

  useEffect(() => {
    if (editingId) {
      const c = chats.find((x) => x.id === editingId);
      setEditingTitle(c?.title ?? "");
    }
  }, [editingId, chats]);

  // Mobile: show list OR detail; desktop: show both
  const showListOnMobile = !chatId;
  const showDetailOnMobile = !!chatId;

  return (
    <>
    <div className="flex min-h-0 flex-1 flex-col gap-4 md:overflow-hidden">
      {(chatsError || promptsError) && (
        <div className="shrink-0 rounded bg-amber-100 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
          API nicht erreichbar. Stellen Sie sicher, dass der Backend-Server unter http://localhost:8000 läuft.
        </div>
      )}
      <div className="flex min-h-0 flex-1 flex-col gap-4 md:flex-row md:min-h-0 md:overflow-hidden">
        {/* Chat list: full width on mobile when no chat selected, sidebar on desktop */}
        <aside
          className={`flex min-h-0 w-full shrink-0 flex-col md:w-64 md:min-h-0 md:overflow-hidden ${
            showListOnMobile ? "flex" : "hidden md:flex"
          }`}
        >
          <ChatList
            chats={filteredChats}
            chatId={chatId}
            isLoading={chatsLoading}
            titleFilter={titleFilter}
            onFilterChange={setTitleFilter}
            folders={folders}
            selectedFolderId={selectedFolderId}
            onFolderSelect={setSelectedFolderId}
            onCreateChat={handleCreateChat}
            onSelectChat={handleSelectChat}
            onRename={handleRename}
            onFavorite={handleFavorite}
            onExport={handleExport}
            onDelete={handleDeleteChat}
            onMoveToFolder={handleMoveToFolder}
            onGenerateCaseSummary={handleGenerateCaseSummary}
            editingId={editingId}
            editingTitle={editingTitle}
            onEditingChange={handleEditingChange}
            exportLoading={exportLoading}
            caseSummaryLoading={caseSummaryLoading}
          />
        </aside>

        {/* Main chat area */}
        <main
          className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 ${
            showDetailOnMobile ? "flex" : "hidden md:flex"
          }`}
        >
          <div className="shrink-0 border-b border-gray-200 px-4 py-2 dark:border-gray-600">
            <EUProcessingNotice />
          </div>
          {!chatId ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 p-6 text-gray-500 dark:text-gray-400">
              <p className="text-center text-lg">Wählen Sie einen Chat oder erstellen Sie einen neuen.</p>
              <button
                type="button"
                onClick={handleCreateChat}
                className="min-h-touch min-w-touch rounded-lg border border-gray-300 px-6 py-3 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
              >
                Neuer Chat
              </button>
            </div>
          ) : (
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
              {/* Mobile: back button to chat list */}
              <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-gray-200 px-3 py-2 md:hidden">
                <button
                  type="button"
                  onClick={() => navigate("/chat")}
                  className="min-h-touch min-w-touch flex items-center gap-1 rounded px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                >
                  ← Chats
                </button>
                {isFinalized && (
                  <span className="rounded bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
                    🔒 Abgeschlossen
                  </span>
                )}
              </div>
              {/* Intervention drawer: evidence-informed ideas (non-prescriptive) */}
              {interventionDrawerOpen && (
                <div className="shrink-0 border-b border-gray-200 bg-gray-50 p-4 dark:border-gray-600 dark:bg-gray-800/50">
                  <p className="mb-2 text-xs font-medium text-gray-600 dark:text-gray-400">
                    Literaturgestützte Orientierungshilfen. Die fachliche Entscheidung liegt bei der Therapeut:in.
                  </p>
                  <ul className="max-h-48 space-y-2 overflow-y-auto">
                    {interventions.map((i) => (
                      <li key={i.id} className="rounded border border-gray-200 bg-white p-2 text-sm dark:border-gray-600 dark:bg-gray-800">
                        <span className="font-medium">{i.title}</span>
                        <span className="text-gray-500 dark:text-gray-400"> · {i.category}</span>
                        <p className="mt-1 text-gray-600 dark:text-gray-300">{i.description}</p>
                        {i.evidence_level && (
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{i.evidence_level}</p>
                        )}
                      </li>
                    ))}
                    {interventions.length === 0 && (
                      <li className="text-sm text-gray-500 dark:text-gray-400">Keine Einträge geladen.</li>
                    )}
                  </ul>
                </div>
              )}

              <div className="min-h-0 flex-1 overflow-y-auto p-4">
                {viewMode === "structured" ? (
                  /* Structured Session Documentation form */
                  <>
                    {structuredDocLoading ? (
                      <p className="py-8 text-center text-gray-500 dark:text-gray-400">Lade …</p>
                    ) : (
                      <div className="mx-auto max-w-2xl space-y-4">
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Strukturierte Sitzungsdokumentation. Alle Felder optional. Version: {structuredDoc?.version ?? 0}
                        </p>
                        {STRUCTURED_DOC_FIELDS.map((key) => (
                          <div key={key}>
                            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                              {key === "session_context" && "Sitzungskontext"}
                              {key === "presenting_symptoms" && "Vorstellende Symptome / Anliegen"}
                              {key === "resources" && "Ressourcen"}
                              {key === "interventions" && "Interventionen"}
                              {key === "homework" && "Hausaufgaben / Vereinbarungen"}
                              {key === "risk_assessment" && "Risikoeinschätzung"}
                              {key === "progress_evaluation" && "Verlaufsbewertung"}
                            </label>
                            <textarea
                              value={structuredFormContent[key] ?? ""}
                              onChange={(e) =>
                                setStructuredFormContent((prev) => ({ ...prev, [key]: e.target.value }))
                              }
                              disabled={isFinalized}
                              rows={3}
                              className="min-h-touch w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                            />
                          </div>
                        ))}
                        {!isFinalized && (
                          <button
                            type="button"
                            onClick={() => handleSaveStructured(structuredFormContent)}
                            disabled={structuredSaveLoading}
                            className="min-h-touch rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:opacity-50"
                          >
                            {structuredSaveLoading ? "Speichern …" : "Speichern"}
                          </button>
                        )}
                      </div>
                    )}
                  </>
                ) : displayMessages.length === 0 && !isStreaming ? (
                  <p className="py-8 text-center text-gray-500 dark:text-gray-400">
                    Schreiben Sie eine Nachricht, um zu beginnen.
                  </p>
                ) : (
                  <>
                    {chatDetail?.last_message_at && (
                      <SmartContextBanner
                        lastMessageAt={chatDetail.last_message_at}
                        firstMessageAt={chatDetail.first_message_at}
                        totalTokens={chatDetail.total_tokens_in_session ?? 0}
                      />
                    )}
                    <ul className="space-y-4">
                    {displayMessages.map((m) => (
                      <li
                        key={m.id}
                        className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                      >
                        <div
                          className={`max-w-[85%] break-words rounded-lg px-4 py-2 ${
                            m.role === "user"
                              ? "bg-primary-500 text-white"
                              : "bg-gray-100 dark:bg-gray-700 dark:text-gray-100"
                          }`}
                        >
                          {m.role === "assistant" ? (
                            <>
                              <ChatMessageMarkdown content={m.content} />
                              <AIConfidenceBadge />
                            </>
                          ) : (
                            <p className="whitespace-pre-wrap text-sm">{m.content}</p>
                          )}
                          {m.created_at && (
                            <p className="mt-1 text-xs opacity-70">
                              {new Date(m.created_at).toLocaleString("de-DE")}
                            </p>
                          )}
                        </div>
                      </li>
                    ))}
                    </ul>
                  </>
                )}
              </div>

              {/* Composer: always visible at bottom (desktop), no page scroll */}
              <div className="shrink-0 border-t border-gray-200 bg-white p-4 dark:border-gray-600 dark:bg-gray-800">
                {!isFinalized && !anonymizationEnabled && (
                  <p
                    className="mb-2 text-xs text-amber-600 dark:text-amber-400"
                    role="status"
                  >
                    Vermeiden Sie personenbezogene Angaben (z. B. Namen, Geburtsdaten).
                  </p>
                )}
                <div className="mb-3 flex flex-wrap items-center gap-3">
                  {/* View toggle: Chat | Structured */}
                  <div className="flex min-h-touch rounded-lg border border-gray-300 dark:border-gray-600" role="group" aria-label="Ansicht">
                    <button
                      type="button"
                      onClick={() => setViewMode("chat")}
                      className={`min-h-touch rounded-l-lg px-3 py-2 text-sm ${
                        viewMode === "chat"
                          ? "bg-primary-500 text-white"
                          : "bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                      }`}
                    >
                      📝 Chat
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewMode("structured")}
                      className={`min-h-touch rounded-r-lg px-3 py-2 text-sm ${
                        viewMode === "structured"
                          ? "bg-primary-500 text-white"
                          : "bg-white text-gray-700 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                      }`}
                    >
                      🗂 Struktur
                    </button>
                  </div>
                  {viewMode === "chat" && !isFinalized && messages.length > 0 && (
                    <button
                      type="button"
                      onClick={handleConvertToStructured}
                      disabled={convertLoading}
                      className="min-h-touch rounded-lg border border-primary-500 bg-primary-50 px-3 py-2 text-sm font-medium text-primary-800 hover:bg-primary-100 disabled:opacity-50 dark:bg-primary-900/30 dark:text-primary-200 dark:hover:bg-primary-900/50"
                    >
                      {convertLoading ? "…" : "✨ In Struktur umwandeln"}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setInterventionDrawerOpen((o) => !o)}
                    className="min-h-touch rounded-lg border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-700"
                    aria-expanded={interventionDrawerOpen}
                  >
                    💡 Interventionsideen
                  </button>
                  {isFinalized && (
                    <span className="rounded bg-amber-100 px-2.5 py-1.5 text-sm font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-200">
                      🔒 Abgeschlossen – keine Änderungen möglich
                    </span>
                  )}
                  {!isFinalized && (
                    <>
                      <AssistModeSelect
                        value={assistMode}
                        options={ASSIST_OPTIONS}
                        onChange={setAssistMode}
                      />
                      <label className="flex min-h-touch cursor-pointer items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={safeMode}
                          onChange={(e) => handleSafeModeToggle(e.target.checked)}
                          className="h-[22px] w-[22px] rounded border-gray-300"
                          aria-label="Strenger Sicherheitsmodus"
                        />
                        <span>Strenger Sicherheitsmodus</span>
                        {safeMode && (
                          <span
                            className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-200"
                            title="Konservative Formulierung, keine absoluten Aussagen"
                          >
                            Aktiv
                          </span>
                        )}
                      </label>
                      <FolderSelect
                        value={chatDetail?.folder_id ?? null}
                        folders={folders}
                        onChange={handleFolderChange}
                        disabled={!chatId}
                      />
                    </>
                  )}
                  <div className="flex items-center gap-1">
                    <span className="text-sm text-gray-600 dark:text-gray-400">Export:</span>
                    <ExportDropdown
                      chatId={chatId!}
                      onExport={handleExport}
                      disabled={!chatId || exportLoading}
                    />
                  </div>
                  {!isFinalized && (
                    <button
                      type="button"
                      onClick={(e) => handleFinalize(chatId!, e)}
                      className="min-h-touch rounded border border-amber-500 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800 hover:bg-amber-100 dark:border-amber-600 dark:bg-amber-900/30 dark:text-amber-200 dark:hover:bg-amber-900/50"
                      aria-label="Chat abschließen und sperren"
                    >
                      🔒 Abschließen
                    </button>
                  )}
                  {!isFinalized && (
                    <label className="flex min-h-touch cursor-pointer items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={anonymizationEnabled}
                        onChange={(e) => setAnonymizationEnabled(e.target.checked)}
                        className="h-[22px] w-[22px] rounded border-gray-300"
                        aria-label="Anonymisierung einschalten"
                      />
                      Anonymisieren
                    </label>
                  )}
                </div>
                {isFinalized ? (
                  <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
                    Dieser Chat wurde abgeschlossen. Export (TXT/PDF) ist weiterhin möglich.
                  </p>
                ) : (
                  <div className="flex items-center gap-2">
                    <VoiceInputButton
                      onResult={(text) =>
                        setInput((prev) => (prev.trim() ? `${prev} ${text}` : text))
                      }
                      disabled={isStreaming}
                      aria-label="Diktieren"
                    />
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSend();
                        }
                      }}
                      placeholder="Nachricht eingeben..."
                      disabled={isStreaming}
                      className="min-h-touch min-w-0 flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                      aria-label="Nachricht"
                    />
                    <button
                      type="button"
                      onClick={handleSend}
                      disabled={!input.trim() || isStreaming}
                      className="min-h-touch min-w-touch shrink-0 rounded-lg bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:opacity-50"
                    >
                      Senden
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
    <CaseSummaryModal
      isOpen={caseSummaryOpen}
      onClose={handleCloseCaseSummary}
      summary={caseSummaryData}
      isLoading={caseSummaryLoading}
      error={caseSummaryError}
    />
    </>
  );
}
