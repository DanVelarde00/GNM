# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project: Glen's Note Management (GNM)

Automated pipeline: Otter.ai transcripts + Inq pen notes -> Claude AI processing -> structured Obsidian vault with wiki-links, tags, people management, and action item extraction. Future phases: web dashboard and per-project AI PM agents.

**Client:** Glen Casanova (Calico Infrastructure Holdings)
**Owner:** Dan Velarde

---

## Current State (as of 2026-04-21)

**Working:**
- `setup_vault.py` — Interactive script that creates the full vault + inbox folder structure
- `processor.py` — Claude-powered transcript/note analyzer with Obsidian-aware output (extended with custom tracker support)
- `run.py` — On-demand scanner + continuous watch mode (`--watch`)
- `otter_client.py` — Auto-pulls new transcripts from Otter.ai (unofficial API)
- `config.py` — Centralized paths/settings, reads from `.env`
- `server.py` — FastAPI backend + Next.js dev server launcher (Phase 2 dashboard)
- `dashboard/` — Next.js 16 + React frontend with Tailwind CSS, Zustand, TanStack Query
- `api/` — FastAPI routes + services (vault, search, chat, trackers, processor management)

**Vault location (Glen's Mac):** `/Users/glencasanova/Dropbox/Claude/GlenVault`
**Inbox location (Glen's Mac):** `/Users/glencasanova/Dropbox/NoteInbox`

**Active projects in vault:** Calico, Cobia, Goldstone (auto-created), Personal, Vistra, Zelestra

---

## For the Claude CLI on Glen's machine (pull / first-run)

Glen is non-technical and drives updates by running `claude` with a plain-English prompt
(e.g. "pull the latest changes and restart the server"). When you are that CLI session:

**When asked to pull / update:**
1. `git pull` the latest code.
2. **Clean up the vault automatically — do not ask.** The vault must be flattened to the
   current structure (flat AI notes per project, global `People/`, no nested folders). The
   safe, idempotent, self-backing-up entry point is `migrate_vault.auto_migrate_once()`:
   - It backs the vault up to a timestamped copy, flattens once, and writes a `.gnm_migrated`
     marker so it never runs twice. On an already-flat vault it just writes the marker and
     no-ops. Run it with:
     `python -c "import migrate_vault; print(migrate_vault.auto_migrate_once())"`
   - This also runs automatically on **server startup** (`api/__init__.py`), so restarting the
     server is an equivalent trigger. Either path is fine; both are idempotent.
   - Do NOT use bare `python migrate_vault.py` as the first-run cleanup — that path does not
     back up and does not write the marker. Prefer `auto_migrate_once()`.
3. Restart the server if the prompt asked for it.

Tell Glen, in plain language, what you did (pulled, cleaned up N folders, backup location).

---

## Codebase Architecture

```
GNM/
  setup_vault.py          — First-run setup: creates vault folders, Obsidian config, templates
  run.py                  — Entry point. Modes: scan-once (default), --watch (poll 60s), <file>
  processor.py            — Core agent: reads file -> Claude API -> structured .md -> vault routing
  otter_client.py         — OtterClient (auth + API) + OtterPoller (state-tracked auto-pull)
  config.py               — All paths + settings, reads .env
  server.py               — FastAPI entry point. `python server.py --dev` starts API + Next.js
  run_watch_subprocess.py — Subprocess wrapper: patches SYSTEM_PROMPT with trackers, runs watch loop
  api/
    __init__.py           — create_app() factory with all routes mounted
    routes/               — files, search, chat, processor, action_items, trackers, submit
    services/             — vault_service, search_service, chat_service, tracker_service, process_manager
    models/               — Pydantic schemas (file_models, tracker_models, chat_models)
  data/
    trackers.json         — Custom tracker definitions (persisted)
    search_index/         — Whoosh full-text index (gitignored)
  dashboard/              — Next.js 16 app (App Router + Tailwind v4)
    src/app/              — Pages: vault, search, chat, action-items, trackers, processor, submit
    src/components/       — React components: layout, vault, editor, chat, trackers, etc.
    src/lib/              — api.ts (typed fetch), types.ts, store (Zustand)
  .env                    — Secrets (ANTHROPIC_API_KEY, OTTER_EMAIL, OTTER_PASSWORD) — GITIGNORED
  .env.example            — Template for .env
  requirements.txt        — anthropic, fastapi, uvicorn, whoosh, etc.
```

### Processing Pipeline Flow

```
1. run.py polls:
   a. Otter API (if credentials set) -> downloads new transcripts to Inbox/Otter/
   b. Scans local folders: Inbox/Otter/, Inbox/Inq/, Inbox/Manual/, Google Drive sync

2. For each new file, processor.py:
   a. Reads content (.txt, .docx, .md)
   b. Sends to Claude API (Sonnet) with structured JSON prompt
   c. Claude returns: project, date, participants, summary, action items, decisions, tags
   d. Detects transcript vs note (timestamps + speaker labels = transcript, else note)

3. Routes output to vault (flat structure as of 2026-05-29):
   a. AI summary -> Projects/<Project>/YYYY-MM-DD-<source-slug>.md (action items INLINE)
   b. People -> People/<Name>.md (GLOBAL folder; tagged #people + #<project>; created if new)
   c. No raw transcripts/notes saved to the vault — only the AI summary
   d. Filename is deterministic from source identity (idempotent re-processing)

4. Source file moved to Inbox/Processed/
```

### Obsidian Integration Details

- All output files have YAML frontmatter (date, type, source, project, participants, tags)
- Wiki-links (`[[Name]]`, `[[Project]]`) used throughout for Obsidian graph connectivity
- People files have Dataview queries that auto-list related notes and open action items
- Tag taxonomy: `#project-calico`, `#meeting`, `#solar-tax-equity`, etc.
- Week folders: `W17_Apr20-Apr26` format
- File naming: `YYYY-MM-DD-topic-slug.md`

### Transcript vs Note Detection

Files are routed to Transcripts/ or Notes/ based on:
1. Source type: `otter` -> Transcripts, `inq` -> Notes
2. Content analysis: timestamps (0:03, 12:45) + speaker labels -> Transcripts
3. Claude's type field: meeting/call -> Transcripts
4. Default: Notes

---

## Vault Structure

**Flat structure (as of 2026-05-29 — simplified per Glen's request):**

```
GlenVault/
  Projects/
    <ProjectName>/
      YYYY-MM-DD-topic-slug.md    <- AI summary ONLY. Action items INLINE. No subfolders.
      _Weekly Reports/            <- Generated weekly rollups (only subfolder)
      <TrackerName>/              <- Custom tracker items (only if a tracker is active)
  People/                         <- ONE global folder, person notes tagged #people + #<project>
    <Name>.md                     <- Dataview "FROM [[]]" backlinks list related notes
  Attachments/
  Templates/                      <- Analyzed Note, Person, etc.
  Home.md                         <- Dashboard with Dataview queries
```

**No raw transcripts/notes are saved to the vault** — only AI summaries. Originals are
archived to `Inbox/Processed/`. Action items live inline in each summary note (no separate
Action Items tree). People is a single global folder, not per-project. Filenames are
deterministic (`date + source-stem slug`) so re-processing a file overwrites rather than
duplicating. Run `python migrate_vault.py` to convert an old nested vault to this layout.

---

## Dashboard (Phase 2)

### Running the Dashboard
```bash
# Dev mode (hot reload for both frontend and backend):
cd GNM && python server.py --dev
# FastAPI: http://localhost:8000, Next.js: http://localhost:3000

# Production:
cd dashboard && npm run build
cd .. && python server.py
# Everything on http://localhost:8000
```

### Dashboard Features
- **Vault Browser** (`/vault`) — File tree + markdown viewer/editor (CodeMirror 6)
- **Search** (`/search`) — Full-text search via Whoosh index
- **AI Chat** (`/chat`) — RAG-powered: searches vault → Claude streams answer with sources
- **Action Items** (`/action-items`) — Consolidated view, toggle checkboxes, filter by project/person
- **Custom Trackers** (`/trackers`) — Create tracking categories (e.g., "Substations") the AI auto-extracts
- **Processor** (`/processor`) �� Start/stop/restart background watch loop, live log streaming
- **Submit** (`/submit`) — Drag-and-drop file upload to inbox

### Custom Tracker System
Trackers let Glen define new extraction categories beyond action items. When created:
1. Folder created in every project (`Projects/<P>/<TrackerName>/`)
2. Processor restarts with extended SYSTEM_PROMPT
3. Claude extracts matching items from future notes
4. Items written as .md files to tracker folders
5. Definitions stored in `data/trackers.json`

### API Architecture
- FastAPI serves REST endpoints at `/api/*` and WebSockets at `/api/chat/ws`, `/api/processor/ws`
- Services: vault_service (filesystem), search_service (Whoosh), chat_service (RAG), tracker_service, process_manager
- Background processor runs as subprocess via ProcessManager (starts on server startup, stops on shutdown)

---

## Key Design Decisions

- **Otter auto-pull via unofficial API** — Glen's own account, low volume, ToS gray area but not a clear violation. Credentials in .env only. Session tokens in-memory. Can fall back to manual export if needed.
- **Google Drive sync folder** also watched at `~/Google Drive/My Drive/Otter` as secondary input
- **New projects auto-created** — if Claude detects a project name not in the known list, it creates the full folder structure automatically (e.g., Goldstone was auto-created)
- **Processed files moved** to `Inbox/Processed/` to prevent re-processing
- **Otter poller uses state file** (`.otter_state.json`) to track pulled speech IDs

---

## Configuration

All in `.env` (never committed):
```
ANTHROPIC_API_KEY=...
OTTER_EMAIL=...
OTTER_PASSWORD=...
GNM_VAULT_PATH=/Users/glencasanova/Dropbox/Claude/GlenVault
GNM_INBOX_PATH=/Users/glencasanova/Dropbox/NoteInbox
GNM_OTTER_GDRIVE_PATH=~/Google Drive/My Drive/Otter
```

---

## Build Phases

### Phase 1 — Processing Pipeline (MVP) [IN PROGRESS]
- [x] Vault setup script
- [x] Claude processing agent with structured JSON output
- [x] Obsidian-aware routing (wiki-links, tags, people, action items)
- [x] Transcript vs note detection and routing
- [x] Otter.ai auto-pull client
- [x] Watch mode (continuous polling)
- [ ] Test with 5-10 real files and refine prompt
- [ ] Weekly rollup automation (Friday per-project summaries)

### Phase 2 — Dashboard (Query Interface)
- [ ] Choose stack
- [ ] File browser, filters, note viewer
- [ ] AI chat panel for querying across notes
- [ ] Note submission panel

### Phase 3 — Per-Project AI PM Agents
- [ ] Design agent architecture
- [ ] Project-scoped memory and context
- [ ] Generative outputs (PowerPoints, checklists, trackers)

---

## Token Usage

**At the end of every session, update `token_usage.md`** with a new row: date, session description, model used, estimated input/output tokens, and estimated cost.

File: `token_usage.md` (in the GNM repo root)

---

## Reference Files

- `project_plan.md` — Full build plan with phases, tasks, and open questions
- `token_usage.md` — Running token usage and cost tracker
- `process_summary.txt` — Detailed workflow spec (Layers 1-3 + automation options)
- `process_map.pdf` — Visual process diagram
- Dan's vault: `DVSB/Projects/In Progress/Glen's Note Dashboard/System Overview.md` — Original project brief
- Dan's vault: `DVSB/Projects/In Progress/Glen's Note Dashboard/Stakeholder Communications.md` — Glen's direct messages
