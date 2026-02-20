/** Chat — streaming interface with assist modes and anonymization. Mobile-first: cards on small screens, sidebar on md+. */
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  createChat,
  deleteChat,
  getChat,
  listChats,
  listPrompts,
  patchChat,
  type ChatSummary,
  type MessageOut,
  type PromptSummary,
} from "../api/client";
import { exportChat } from "../api/client";
import { streamChatMessage } from "../api/streamChat";
import { ChatMessageMarkdown } from "../components/ChatMessageMarkdown";

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
                  p.key === value ? "bg-primary-100 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300" : ""
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

const ASSIST_DEFAULTS: PromptSummary[] = [
  { key: "CHAT_WITH_AI", display_name: "Chat with AI", version: 1 },
  { key: "SESSION_SUMMARY", display_name: "Session Summary", version: 1 },
  { key: "STRUCTURED_DOC", display_name: "Structured Documentation", version: 1 },
  { key: "THERAPY_PLAN", display_name: "Therapy Plan Draft", version: 1 },
  { key: "RISK_ANALYSIS", display_name: "Risk Analysis", version: 1 },
  { key: "CASE_REFLECTION", display_name: "Case Reflection", version: 1 },
];

/** Chat list as cards for mobile, compact list for desktop. */
function ChatList({
  chats,
  chatId,
  titleFilter,
  onFilterChange,
  onCreateChat,
  onSelectChat,
  onRename,
  onFavorite,
  onExport,
  onDelete,
  editingId,
  editingTitle,
  onEditingChange,
  isLoading,
}: {
  chats: ChatSummary[];
  chatId: string | null;
  titleFilter: string;
  onFilterChange: (v: string) => void;
  onCreateChat: () => void;
  onSelectChat: (id: string) => void;
  onRename: (id: string) => void;
  onFavorite: (c: ChatSummary, e: React.MouseEvent) => void;
  onExport: (id: string, e: React.MouseEvent) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  editingId: string | null;
  editingTitle: string;
  onEditingChange: (id: string | null, title: string) => void;
  isLoading?: boolean;
}) {
  return (
    <div className="flex flex-col rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="border-b border-gray-200 p-3 dark:border-gray-600">
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
      <div className="flex-1 overflow-y-auto p-2 min-w-0">
        {isLoading ? (
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Laden...</p>
        ) : chats.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
            Keine Chats. Erstellen Sie einen neuen.
          </p>
        ) : (
          <ul className="space-y-2">
            {chats.map((c) => (
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
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function ChatListItem({
  chat,
  isSelected,
  isEditing,
  editingTitle,
  onSelect,
  onRename,
  onEditingChange,
  onFavorite,
  onExport,
  onDelete,
}: {
  chat: ChatSummary;
  isSelected: boolean;
  isEditing: boolean;
  editingTitle: string;
  onSelect: () => void;
  onRename: () => void;
  onEditingChange: (id: string | null, title: string) => void;
  onFavorite: (c: ChatSummary, e: React.MouseEvent) => void;
  onExport: (id: string, e: React.MouseEvent) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
}) {
  return (
    <li
      className={`flex min-h-touch items-center gap-2 rounded-lg px-3 py-2 md:px-2 md:py-2 ${
        isSelected ? "bg-primary-100 dark:bg-primary-900/30" : "hover:bg-gray-100 dark:hover:bg-gray-700"
      }`}
    >
      {isEditing ? (
        <input
          type="text"
          value={editingTitle}
          onChange={(e) => onEditingChange(chat.id, e.target.value)}
          onBlur={() => onRename()}
          onKeyDown={(e) => {
            if (e.key === "Enter") onRename();
            if (e.key === "Escape") onEditingChange(null, "");
          }}
          className="min-h-touch min-w-0 flex-1 rounded border border-gray-300 px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700"
          autoFocus
          aria-label="Chat umbenennen"
        />
      ) : (
        <>
          <button
            type="button"
            onClick={onSelect}
            className="min-h-touch min-w-0 flex-1 truncate text-left text-sm"
          >
            {chat.title}
          </button>
          <div className="flex shrink-0 gap-0.5">
            <button
              type="button"
              onClick={() => onEditingChange(chat.id, chat.title)}
              className="min-h-touch min-w-touch rounded p-2 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600"
              aria-label="Umbenennen"
            >
              ✏️
            </button>
            <button
              type="button"
              onClick={(e) => onFavorite(chat, e)}
              className="min-h-touch min-w-touch rounded p-2 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600"
              aria-label={chat.is_favorite ? "Favorit entfernen" : "Als Favorit markieren"}
            >
              {chat.is_favorite ? "★" : "☆"}
            </button>
            <button
              type="button"
              onClick={(e) => onExport(chat.id, e)}
              className="min-h-touch min-w-touch rounded p-2 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600"
              aria-label="Exportieren"
            >
              ⬇
            </button>
            <button
              type="button"
              onClick={(e) => onDelete(chat.id, e)}
              className="min-h-touch min-w-touch rounded p-2 text-red-500 hover:bg-red-100 hover:text-red-700 dark:hover:bg-red-900/30"
              aria-label="Löschen"
            >
              🗑
            </button>
          </div>
        </>
      )}
    </li>
  );
}

export default function ChatPage() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [titleFilter, setTitleFilter] = useState("");
  const [assistMode, setAssistMode] = useState<string>("CHAT_WITH_AI");
  const [anonymizationEnabled, setAnonymizationEnabled] = useState(true);
  const [input, setInput] = useState("");
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");

  const chatId = conversationId ?? null;

  const { data: chats = [], refetch: refetchChats, isError: chatsError, isLoading: chatsLoading } = useQuery({
    queryKey: ["chats"],
    queryFn: listChats,
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

  const handleExport = useCallback(
    async (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      const blob = await exportChat(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chat-export-${id.slice(0, 8)}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    },
    []
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
  }, [input, chatId, isStreaming, assistMode, anonymizationEnabled, navigate, refetchChats, refetchChat]);

  const handleEditingChange = useCallback((id: string | null, title: string) => {
    setEditingId(id);
    setEditingTitle(title);
  }, []);

  const messages: MessageOut[] = chatDetail?.messages ?? [];
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
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      {(chatsError || promptsError) && (
        <div className="rounded bg-amber-100 px-4 py-3 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
          API nicht erreichbar. Stellen Sie sicher, dass der Backend-Server unter http://localhost:8000 läuft.
        </div>
      )}
      <div className="flex min-h-0 flex-1 flex-col gap-4 md:flex-row">
        {/* Chat list: full width on mobile when no chat selected, sidebar on desktop */}
        <aside
          className={`flex w-full shrink-0 flex-col md:w-64 ${
            showListOnMobile ? "flex" : "hidden md:flex"
          }`}
        >
          <ChatList
            chats={filteredChats}
            chatId={chatId}
            isLoading={chatsLoading}
            titleFilter={titleFilter}
            onFilterChange={setTitleFilter}
            onCreateChat={handleCreateChat}
            onSelectChat={handleSelectChat}
            onRename={handleRename}
            onFavorite={handleFavorite}
            onExport={handleExport}
            onDelete={handleDeleteChat}
            editingId={editingId}
            editingTitle={editingTitle}
            onEditingChange={handleEditingChange}
          />
        </aside>

        {/* Main chat area */}
        <main
          className={`flex min-w-0 flex-1 flex-col rounded-lg border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 ${
            showDetailOnMobile ? "flex" : "hidden md:flex"
          }`}
        >
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
            <>
              {/* Mobile: back button to chat list */}
              <div className="flex shrink-0 items-center border-b border-gray-200 px-3 py-2 md:hidden">
                <button
                  type="button"
                  onClick={() => navigate("/chat")}
                  className="min-h-touch min-w-touch flex items-center gap-1 rounded px-2 py-1.5 text-sm text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
                >
                  ← Chats
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4">
                {displayMessages.length === 0 && !isStreaming ? (
                  <p className="py-8 text-center text-gray-500 dark:text-gray-400">
                    Schreiben Sie eine Nachricht, um zu beginnen.
                  </p>
                ) : (
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
                            <ChatMessageMarkdown content={m.content} />
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
                )}
              </div>

              {/* Sticky input area */}
              <div className="shrink-0 border-t border-gray-200 p-4 dark:border-gray-600">
                {!anonymizationEnabled && (
                  <p
                    className="mb-2 text-xs text-amber-600 dark:text-amber-400"
                    role="status"
                  >
                    Vermeiden Sie personenbezogene Angaben (z. B. Namen, Geburtsdaten).
                  </p>
                )}
                <div className="mb-3 flex flex-wrap gap-3">
                  <AssistModeSelect
                    value={assistMode}
                    options={ASSIST_OPTIONS}
                    onChange={setAssistMode}
                  />
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
                </div>
                <div className="flex gap-2">
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
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
