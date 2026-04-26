# Architecture — How GNM Works

This document explains how every piece of GNM connects. You don't need to read this to use the system, but if you want to understand what's happening under the hood (or debug something weird), start here.

---

## The big picture

```
┌────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────┐
│ Sources            │     │ GNM Processor           │     │ Vault (Obsidian)     │
│                    │     │                         │     │                      │
│  Otter.ai API      │────▶│   otter_client.py       │     │  Projects/           │
│  Inq pen → Dropbox │────▶│   run.py (scanner)      │────▶│    Calico/           │
│  Manual files      │────▶│   processor.py          │     │      Notes/          │
│  Google Drive      │────▶│     ↓                   │     │      Transcripts/    │
│                    │     │   Claude API (Sonnet)   │     │      AI Analyzed/    │
└────────────────────┘     │     ↓                   │     │      Action Items/   │
                           │   Routes output to vault│     │      People/         │
                           └─────────────────────────┘     └──────────────────────┘
                                       ↕
                           ┌─────────────────────────┐
                           │ Dashboard               │     ┌──────────────────────┐
                           │                         │     │ You (browser)        │
                           │   FastAPI (server.py)   │────▶│                      │
                           │   Next.js UI (port 3000)│     │  http://localhost:   │
                           │                         │     │   3000 or 8000       │
                           └─────────────────────────┘     └──────────────────────┘
```

---

## Component map

### `config.py` — Single source of truth for paths + settings

Every other file imports from here. Reads `.env` for secrets. If you ever need to change where the vault or inbox lives, this is the first place to look (or override via `.env`).

### `setup_vault.py` — One-time vault creator

You run this once during setup. It prompts you for paths and project names, then creates the full folder tree, Obsidian config, Dataview plugin config, and starter templates. After that, it never runs again.

### `otter_client.py` — Otter.ai integration

Two classes:

- **`OtterClient`** — Handles login, fetches transcript list, downloads individual transcripts
- **`OtterPoller`** — Tracks which transcripts you've already pulled (via `.otter_state.json`) so it only downloads new ones

Uses Otter's unofficial web API (same endpoints the browser uses). Session token lives in memory only.

### `processor.py` — The brain

For each new file:

1. Reads the content (handles `.txt`, `.md`, `.docx`, `.pdf`)
2. Sends a structured prompt to Claude asking for JSON output
3. Parses Claude's response
4. Detects whether it's a transcript (timestamps + speakers) or a note
5. Writes the analyzed note, action items, person files, and raw source copy to the vault
6. Moves the original to `Inbox/Processed/`

Claude model used: **Sonnet 4.6** (`claude-sonnet-4-6`).

### `run.py` — The loop

- `python run.py` — Scan once, process everything pending, exit
- `python run.py --watch` — Poll every 60 seconds forever
- `python run.py path/to/file.txt` — Process one specific file

The dashboard's Processor page runs `run.py --watch` as a subprocess.

### `server.py` — The single entry point for the dashboard

- `python server.py` — Production mode: FastAPI on :8000, serves the pre-built Next.js static files
- `python server.py --dev` — Dev mode: FastAPI on :8000 + spawns `npm run dev` for Next.js on :3000

### `api/` — The FastAPI backend

```
api/
├── __init__.py          ← create_app() — assembles everything
├── routes/              ← HTTP endpoints (URLs)
│   ├── files.py             /api/files/*       — vault browsing, read, write
│   ├── search.py            /api/search/*      — Whoosh search
│   ├── chat.py              /api/chat/ws       — RAG chat (WebSocket)
│   ├── action_items.py      /api/action_items/* — consolidated action item list
│   ├── trackers.py          /api/trackers/*    — custom tracker CRUD
│   ├── processor.py         /api/processor/*   — start/stop, WebSocket log stream
│   └── submit.py            /api/submit/*      — file upload
└── services/            ← The logic behind the routes
    ├── vault_service.py         — Read/write files, build tree
    ├── search_service.py        — Whoosh index management
    ├── chat_service.py          — Retrieves notes → asks Claude → streams answer
    ├── tracker_service.py       — Tracker CRUD + prompt injection
    └── process_manager.py       — Spawns/kills the processor subprocess
```

### `dashboard/` — The Next.js frontend

Talks to the FastAPI backend via typed fetch calls (`src/lib/api.ts`). State managed by Zustand + TanStack Query.

---

## Key data flows

### Flow 1: A new Otter transcript becomes a vault note

```
1. You record a meeting in Otter.ai
2. Otter finishes processing (2-5 min)
3. Processor wakes up (60s timer)
4. otter_client.py authenticates, lists transcripts
5. Sees new one, downloads .txt to ~/Dropbox/NoteInbox/Otter/
6. run.py scanner finds the new file
7. processor.py reads it, calls Claude
8. Claude returns JSON: { project: "Calico", summary, action_items, participants, ... }
9. processor.py writes:
     Projects/Calico/AI Analyzed Notes/2026/W17_Apr20-Apr26/2026-04-24-meeting.md
     Projects/Calico/Action Items/2026/W17_Apr20-Apr26/2026-04-24-actions.md
     Projects/Calico/Transcripts/2026-04-24-meeting.md
     Projects/Calico/People/Sarah.md (if new)
10. Original file moves to ~/Dropbox/NoteInbox/Processed/
11. Dashboard's search index updates
```

### Flow 2: You ask the chat a question

```
1. You type "What are my Calico action items this week?" in /chat
2. Frontend opens WebSocket to /api/chat/ws, sends message
3. chat_service.py runs full-text search on your question
4. Top N matching notes retrieved
5. chat_service.py sends question + retrieved notes to Claude API
6. Claude streams back answer token-by-token
7. Frontend renders streaming response with source citations
```

### Flow 3: You create a custom tracker

```
1. You go to /trackers, click "New Tracker", name it "Substations"
2. tracker_service.py:
     - Appends to data/trackers.json
     - Creates Projects/<P>/Substations/ in every project
     - Kills and restarts the processor subprocess with updated SYSTEM_PROMPT
3. Next time processor.py runs, its prompt includes:
     "If the note mentions anything about substations, extract them as items
      with fields: name, location, voltage, status. Output JSON as trackers.substations[]."
4. New notes from now on will have substation data extracted and written to
   Projects/<P>/Substations/<name>.md
```

---

## What's in Dropbox vs not

- **In Dropbox:** The inbox (`~/Dropbox/NoteInbox/`) — so you can drop files from any device
- **NOT in Dropbox:** The vault (`~/obsidian/GlenVault/`), the GNM code, the `.env` file, the Python venv, the search index

**Why?** Obsidian works best with a local vault. Syncing it via Dropbox can cause duplicate file conflicts. If you want your vault on multiple Macs, use Obsidian Sync ($4/mo) or iCloud.

---

## Where state lives

| State | Location | Purpose |
|---|---|---|
| API keys | `.env` | Never committed |
| Otter pull history | `.otter_state.json` | Which Otter transcripts already pulled |
| Custom trackers | `data/trackers.json` | Tracker definitions |
| Search index | `data/search_index/` | Whoosh full-text index (rebuilt if deleted) |
| Processed files | `~/Dropbox/NoteInbox/Processed/` | Originals after processing |
| Vault content | `~/obsidian/GlenVault/` | Actual knowledge — the valuable part |

---

## What's safe to delete

If something goes weird, these can all be deleted and the system will recreate them:

- `data/search_index/` — rebuilds on next search
- `.otter_state.json` — will re-pull recent transcripts (may create duplicates)
- `venv/` — rerun `python3.11 -m venv venv && pip install -r requirements.txt`
- `dashboard/node_modules/` — rerun `npm install`
- `dashboard/.next/` — Next.js build cache

**Don't delete:**

- `.env` — you'll lose your API keys
- `~/obsidian/GlenVault/` — your actual notes
- `~/Dropbox/NoteInbox/` — your inbox
- `data/trackers.json` — your custom tracker definitions

---

## Extending the system

Want to add a new input source (e.g., email)? Add a scanner function to `run.py` that drops files into `~/Dropbox/NoteInbox/<source>/` — the rest of the pipeline picks it up automatically.

Want to change what Claude extracts? Edit the `SYSTEM_PROMPT` in `processor.py`.

Want a new dashboard page? Add a route under `api/routes/` and a corresponding page in `dashboard/src/app/`.

---

## The build phases (from the project plan)

- **Phase 1 (in progress):** Processing pipeline — this is what you're installing now
- **Phase 2 (in progress):** Dashboard — you're getting this too
- **Phase 3 (future):** Per-project AI PM agents that can generate outputs (decks, trackers, checklists) autonomously

---

## Glossary

| Term | Meaning |
|---|---|
| **Vault** | Your Obsidian knowledge base — the output folder tree |
| **Inbox** | The Dropbox-synced drop-zone where new files land before processing |
| **Processor** | The Python loop that watches the inbox and calls Claude |
| **Dashboard** | The web UI at localhost:3000 or localhost:8000 |
| **Tracker** | A custom extraction category Claude watches for in notes |
| **Action item** | A todo extracted from a note (auto-detected by Claude) |
| **RAG** | Retrieval-Augmented Generation — chat searches vault first, then asks Claude |
| **Whoosh** | Python full-text search library, powers the search index |
| **Dataview** | Obsidian plugin that runs queries over your notes' frontmatter |
