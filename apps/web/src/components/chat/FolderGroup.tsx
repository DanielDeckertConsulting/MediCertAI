/** Collapsible folder group for desktop chat list. State persisted in localStorage. */
import { useCallback, useEffect, useState } from "react";
import type { ChatSummary } from "../../api/client";
import type { FolderOut } from "../../api/client";

const STORAGE_KEY = "clinai_chat_folder_collapsed";

function getStorageKey(): string {
  return STORAGE_KEY;
}

function loadCollapsed(folderId: string): boolean {
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (!raw) return false;
    const parsed = JSON.parse(raw) as Record<string, boolean>;
    return !!parsed[folderId];
  } catch {
    return false;
  }
}

function saveCollapsed(folderId: string, collapsed: boolean): void {
  try {
    const raw = localStorage.getItem(getStorageKey());
    const parsed = (raw ? JSON.parse(raw) : {}) as Record<string, boolean>;
    parsed[folderId] = collapsed;
    localStorage.setItem(getStorageKey(), JSON.stringify(parsed));
  } catch {
    // ignore
  }
}

export function FolderGroup({
  folder,
  chats,
  renderChatItem,
}: {
  folder: FolderOut;
  chats: ChatSummary[];
  renderChatItem: (chat: ChatSummary) => React.ReactNode;
}) {
  const [collapsed, setCollapsedState] = useState(() => loadCollapsed(folder.id));

  const setCollapsed = useCallback((next: boolean) => {
    setCollapsedState(next);
    saveCollapsed(folder.id, next);
  }, [folder.id]);

  useEffect(() => {
    setCollapsedState(loadCollapsed(folder.id));
  }, [folder.id]);

  const hasChats = chats.length > 0;
  const isCollapsible = hasChats;
  const isExpanded = !collapsed;

  return (
    <div className="border-b border-gray-100 last:border-b-0 dark:border-gray-700">
      <button
        type="button"
        onClick={() => isCollapsible && setCollapsed(!collapsed)}
        disabled={!isCollapsible}
        className={`flex min-h-touch w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition-colors ${
          isCollapsible
            ? "hover:bg-gray-100 dark:hover:bg-gray-700"
            : "cursor-default opacity-60"
        }`}
        aria-expanded={isCollapsible ? isExpanded : undefined}
      >
        <span
          className={`shrink-0 transition-transform ${!isExpanded && isCollapsible ? "-rotate-90" : ""}`}
          aria-hidden
        >
          {isCollapsible ? "▾" : "—"}
        </span>
        <span className="min-w-0 flex-1 truncate font-medium">{folder.name}</span>
        <span className="shrink-0 rounded bg-gray-200 px-1.5 py-0.5 text-xs dark:bg-gray-600">
          {chats.length}
        </span>
      </button>
      {isExpanded && hasChats && (
        <ul className="space-y-0.5 pl-2 pr-1 pb-1">
          {chats.map((c) => renderChatItem(c))}
        </ul>
      )}
    </div>
  );
}
