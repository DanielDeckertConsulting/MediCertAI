/** Folders — CRUD for organizing chats. Mobile-first. */
import { useCallback, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listFolders,
  createFolder,
  patchFolder,
  deleteFolder,
  type FolderOut,
} from "../api/client";

export default function FoldersPage() {
  const queryClient = useQueryClient();
  const [newName, setNewName] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState("");

  const { data: folders = [], isLoading, isError, refetch } = useQuery({
    queryKey: ["folders"],
    queryFn: listFolders,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => createFolder(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folders"] });
      setNewName("");
    },
  });

  const patchMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => patchFolder(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folders"] });
      setEditingId(null);
      setEditingName("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteFolder(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folders"] });
      queryClient.invalidateQueries({ queryKey: ["chats"] });
    },
  });

  const handleCreate = useCallback(() => {
    const name = newName.trim();
    if (!name) return;
    createMutation.mutate(name);
  }, [newName, createMutation]);

  const handleStartEdit = useCallback((f: FolderOut) => {
    setEditingId(f.id);
    setEditingName(f.name);
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (!editingId || !editingName.trim()) {
      setEditingId(null);
      return;
    }
    patchMutation.mutate({ id: editingId, name: editingName.trim() });
  }, [editingId, editingName, patchMutation]);

  const handleDelete = useCallback(
    (id: string) => {
      if (window.confirm("Ordner löschen? Chats werden in „Nicht zugeordnet“ verschoben.")) {
        deleteMutation.mutate(id);
      }
    },
    [deleteMutation]
  );

  return (
    <div className="min-w-0">
      <h2 className="mb-4 text-lg font-semibold">Ordner</h2>

      {isError && (
        <div className="mb-4 rounded bg-red-100 px-4 py-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-200">
          Fehler beim Laden.{" "}
          <button
            type="button"
            onClick={() => refetch()}
            className="underline focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Erneut versuchen
          </button>
        </div>
      )}

      <div className="mb-4 flex gap-2">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          placeholder="Neuer Ordner"
          className="min-h-touch min-w-0 flex-1 rounded border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-white"
          aria-label="Ordnername"
        />
        <button
          type="button"
          onClick={handleCreate}
          disabled={!newName.trim() || createMutation.isPending}
          className="min-h-touch min-w-touch shrink-0 rounded bg-primary-500 px-4 py-2 text-sm font-medium text-white hover:bg-primary-600 disabled:opacity-50"
        >
          Erstellen
        </button>
      </div>

      {createMutation.isError && (
        <p className="mb-2 text-sm text-red-600 dark:text-red-400">
          {(createMutation.error as Error).message}
        </p>
      )}

      {isLoading ? (
        <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Laden...</p>
      ) : folders.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Noch keine Ordner. Erstellen Sie einen neuen.
        </p>
      ) : (
        <ul className="space-y-2">
          {folders.map((f) => (
            <li
              key={f.id}
              className="flex min-h-touch items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-gray-600 dark:bg-gray-800"
            >
              {editingId === f.id ? (
                <>
                  <input
                    type="text"
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSaveEdit();
                      if (e.key === "Escape") setEditingId(null);
                    }}
                    className="min-h-touch min-w-0 flex-1 rounded border border-gray-300 px-2 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-700"
                    autoFocus
                    aria-label="Ordner umbenennen"
                  />
                  <button
                    type="button"
                    onClick={handleSaveEdit}
                    className="min-h-touch min-w-touch rounded px-2 py-1.5 text-sm text-primary-600 hover:bg-primary-50 dark:text-primary-400"
                  >
                    Speichern
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingId(null)}
                    className="min-h-touch min-w-touch rounded px-2 py-1.5 text-sm text-gray-500 hover:bg-gray-100"
                  >
                    Abbrechen
                  </button>
                </>
              ) : (
                <>
                  <span className="min-w-0 flex-1 truncate text-sm">{f.name}</span>
                  <button
                    type="button"
                    onClick={() => handleStartEdit(f)}
                    className="min-h-touch min-w-touch rounded p-2 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-600"
                    aria-label="Umbenennen"
                  >
                    ✏️
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDelete(f.id)}
                    className="min-h-touch min-w-touch rounded p-2 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30"
                    aria-label="Löschen"
                  >
                    🗑
                  </button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
