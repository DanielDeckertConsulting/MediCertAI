# PR: feat: Folder CRUD, chat assignment, filter by folder

## What changed

- **Backend**
  - New `folders` table (id, tenant_id, name, created_at) with RLS
  - Migration 009: folders + FK `chats.folder_id` → `folders.id` ON DELETE SET NULL
  - New router `/folders`: GET, POST, PATCH, DELETE
  - `chats` router: PATCH accepts `folder_id`, GET supports `folder_id` and `unfiled_only`
  - Domain events: folder.created, folder.renamed, folder.deleted, chat.folder_changed
  - Audit log entry on folder delete (folder_id only, no name — no PII)

- **Frontend**
  - FoldersPage: full CRUD (create, rename, delete) with loading/empty/error states
  - ChatPage: folder filter in sidebar (Alle, Nicht zugeordnet, folders), FolderSelect dropdown for chat assignment
  - API client: listFolders, createFolder, patchFolder, deleteFolder; listChats params

## How to test

1. **Backend**
   ```bash
   cd services/api && alembic upgrade head
   python -m pytest tests/test_folders.py -v
   ```

2. **Manual**
   - Start API and web app. Create folder on FoldersPage.
   - On Chat page: create chat, select folder from dropdown. Chat moves to folder.
   - Click folder in sidebar → chat list filters. Click "Nicht zugeordnet" → unfiled chats.
   - Delete folder → chats move to Unfiled.

## Assumptions

- One folder per chat (no multi-label)
- Flat folders only
- Auth bypass for local dev; RLS enforces tenant isolation

## Golden Path impact

**MEDIUM** — extends chat flow with folder assignment and filter.
