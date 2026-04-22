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

**Vault location:** `C:\Users\danve\obsidian\GlenVault\` (prototype on Dan's machine)
**Glen's vault:** TBD — will be on his Mac via Dropbox

**Active projects in vault:** Calico, Cobia, Goldstone (auto-created), Personal, Vistra, Zelestra

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

3. Routes output to vault:
   a. AI Analyzed Notes -> Projects/<Project>/AI Analyzed Notes/YYYY/WNN/ (always)
   b. Action Items -> Projects/<Project>/Action Items/YYYY/WNN/ (if any exist)
   c. Raw source -> Projects/<Project>/Transcripts/ OR Notes/ (based on detection)
   d. People -> Projects/<Project>/People/<Name>.md (created if new, with Dataview queries)

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

```
GlenVault/
  Projects/
    <ProjectName>/
      Notes/                      <- Raw notes (Inq, manual)
      Transcripts/                <- Raw transcripts (Otter) as .md
      AI Analyzed Notes/
        YYYY/
          WNN_MonDD-MonDD/        <- Claude-generated analysis
      Action Items/
        YYYY/
          WNN_MonDD-MonDD/        <- Extracted action items
      Weekly Reports/
        YYYY/
      People/                     <- Auto-created person files with Dataview
  Attachments/
  Templates/                      <- Analyzed Note, Action Items, Weekly Report, Person
  Home.md                         <- Dashboard with Dataview queries
```

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
- **Google Drive sync folder** also watched at `C:\Users\danve\drive\` as secondary input
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
GNM_VAULT_PATH=C:\Users\danve\obsidian\GlenVault
GNM_INBOX_PATH=C:\Users\danve\Dropbox\NoteInbox
GNM_OTTER_GDRIVE_PATH=C:\Users\danve\drive
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

File: `C:\Users\danve\Projects\GNM\token_usage.md`

---

## Reference Files

- `project_plan.md` — Full build plan with phases, tasks, and open questions
- `token_usage.md` — Running token usage and cost tracker
- `process_summary.txt` — Detailed workflow spec (Layers 1-3 + automation options)
- `process_map.pdf` — Visual process diagram
- `C:\Users\danve\obsidian\DVSB\Projects\In Progress\Glen's Note Dashboard\System Overview.md` — Original project brief
- `C:\Users\danve\obsidian\DVSB\Projects\In Progress\Glen's Note Dashboard\Stakeholder Communications.md` — Glen's direct messages
