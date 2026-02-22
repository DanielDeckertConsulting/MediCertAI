/** Chat list item: mobile inline icons, desktop meatball menu. */
import { useEffect, useRef, useState } from "react";
import type { ChatSummary, ExportFormat, FolderOut } from "../../api/client";

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

/** Meatball menu (⋯) for desktop: rename, favorite, move, export, delete. */
function MeatballMenu({
  chat,
  folders,
  onRename,
  onFavorite,
  onMoveToFolder,
  onExport,
  onDelete,
  exportLoading,
}: {
  chat: ChatSummary;
  folders: FolderOut[];
  onRename: () => void;
  onFavorite: (e: React.MouseEvent) => void;
  onMoveToFolder: (folderId: string | null) => void;
  onExport: (format: ExportFormat, e: React.MouseEvent) => void;
  onDelete: (e: React.MouseEvent) => void;
  exportLoading: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setMoveOpen(false);
      }
    }
    if (open) document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [open]);

  if (chat.status === "finalized") {
    return (
      <span
        className="shrink-0 rounded px-2 py-1 text-xs font-medium text-amber-700 bg-amber-100 dark:bg-amber-900/40 dark:text-amber-300"
        title="Abgeschlossen – keine Änderungen möglich"
      >
        🔒
      </span>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="min-h-touch min-w-touch flex items-center justify-center rounded p-2 text-gray-500 hover:bg-gray-200 hover:text-gray-700 dark:hover:bg-gray-600"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Chat-Aktionen"
      >
        ⋯
      </button>
      {open && (
        <ul
          role="menu"
          className="absolute right-0 top-full z-50 mt-1 min-w-[180px] overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800 dark:text-white"
        >
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                onRename();
                setOpen(false);
              }}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Umbenennen
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                onFavorite(e);
                setOpen(false);
              }}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {chat.is_favorite ? "★ Favorit entfernen" : "☆ Als Favorit markieren"}
            </button>
          </li>
          <li role="none" className="relative">
            <button
              type="button"
              role="menuitem"
              onClick={() => setMoveOpen(!moveOpen)}
              className="flex min-h-[44px] w-full items-center justify-between px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              In Ordner verschieben
              <span aria-hidden>{moveOpen ? "▴" : "▾"}</span>
            </button>
            {moveOpen && (
              <ul
                role="menu"
                className="border-t border-gray-200 dark:border-gray-600"
              >
                <li role="none">
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      onMoveToFolder(null);
                      setOpen(false);
                    }}
                    className="flex min-h-[44px] w-full items-center px-6 py-2 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    Nicht zugeordnet
                  </button>
                </li>
                {folders.map((f) => (
                  <li key={f.id} role="none">
                    <button
                      type="button"
                      role="menuitem"
                      onClick={() => {
                        onMoveToFolder(f.id);
                        setOpen(false);
                      }}
                      className="flex min-h-[44px] w-full items-center px-6 py-2 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      {f.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                onExport("txt", e);
                setOpen(false);
              }}
              disabled={exportLoading}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Export als TXT
            </button>
          </li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                onExport("pdf", e);
                setOpen(false);
              }}
              disabled={exportLoading}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              Export als PDF
            </button>
          </li>
          <li role="none" className="border-t border-gray-200 dark:border-gray-600">
            <button
              type="button"
              role="menuitem"
              onClick={(e) => {
                if (window.confirm("Chat wirklich löschen?")) {
                  onDelete(e);
                  setOpen(false);
                }
              }}
              className="flex min-h-[44px] w-full items-center px-4 py-3 text-left text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30"
            >
              Löschen
            </button>
          </li>
        </ul>
      )}
    </div>
  );
}

export function ChatListItem({
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
  onMoveToFolder,
  folders,
  exportLoading,
}: {
  chat: ChatSummary;
  isSelected: boolean;
  isEditing: boolean;
  editingTitle: string;
  onSelect: () => void;
  onRename: () => void;
  onEditingChange: (id: string | null, title: string) => void;
  onFavorite: (c: ChatSummary, e: React.MouseEvent) => void;
  onExport: (id: string, format: ExportFormat, e: React.MouseEvent) => void;
  onDelete: (id: string, e: React.MouseEvent) => void;
  onMoveToFolder?: (id: string, folderId: string | null) => void;
  folders?: FolderOut[];
  exportLoading?: boolean;
}) {
  return (
    <li
      className={`flex min-h-touch items-center gap-2 rounded-lg px-3 py-2 md:px-2 md:py-2 ${
        isSelected ? "bg-primary-100 text-primary-800 dark:bg-primary-100 dark:text-gray-900" : "hover:bg-gray-100 dark:hover:bg-gray-700"
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
          {/* Mobile: inline icons */}
          <div className="flex shrink-0 items-center gap-0.5 md:hidden">
            {chat.status === "finalized" ? (
              <span
                className="shrink-0 rounded px-2 py-1 text-xs font-medium text-amber-700 bg-amber-100 dark:bg-amber-900/40 dark:text-amber-300"
                title="Abgeschlossen – keine Änderungen möglich"
              >
                🔒
              </span>
            ) : (
              <>
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
                  onClick={(e) => onDelete(chat.id, e)}
                  className="min-h-touch min-w-touch rounded p-2 text-red-500 hover:bg-red-100 hover:text-red-700 dark:hover:bg-red-900/30"
                  aria-label="Löschen"
                >
                  🗑
                </button>
              </>
            )}
            <ExportDropdown
              chatId={chat.id}
              onExport={onExport}
              disabled={exportLoading}
            />
          </div>
          {/* Desktop: meatball menu only */}
          <div className="hidden md:block">
            <MeatballMenu
              chat={chat}
              folders={folders ?? []}
              onRename={() => onEditingChange(chat.id, chat.title)}
              onFavorite={(e) => onFavorite(chat, e)}
              onMoveToFolder={onMoveToFolder ? (folderId) => onMoveToFolder(chat.id, folderId) : () => {}}
              onExport={(format, e) => onExport(chat.id, format, e)}
              onDelete={(e) => onDelete(chat.id, e)}
              exportLoading={exportLoading ?? false}
            />
          </div>
        </>
      )}
    </li>
  );
}
