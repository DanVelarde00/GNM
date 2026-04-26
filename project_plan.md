# GNM Project Plan
### Glen's Note Management Dashboard
**Client:** Glen (Calico Infrastructure Holdings)
**Owner:** Dan Velarde
**Last Updated:** 2026-04-17

---

## Intent

Glen captures notes with an Inq Smart Pen and records meetings via Otter.ai. Today those files sit in folders and require manual effort to organize, link, and act on. The goal is a fully automated pipeline that:

1. Pulls raw notes and transcripts into a structured Dropbox folder
2. Runs Claude to parse, summarize, tag, and route each file into an Obsidian vault — with automatic cross-links (e.g., any mention of "Calico" links to the Calico project node)
3. Produces a custom web dashboard where Glen can filter, browse, chat with his notes, and submit new notes directly for analysis
4. Auto-runs weekly per-project rollups every Friday: summary of the week, action items for the following week
5. Evolves into per-project AI PM agents that learn over time and can generate PowerPoints, due diligence checklists, action item trackers, etc.

> **Key insight from Glen** *(ref: Stakeholder Communications)*: The value is not Obsidian itself — it's that every link, tag, and cross-reference gets created automatically. Glen does not have time to manually link files. The automation has to handle 100% of that.

> **Sync note**: Glen uses Dropbox to sync across all his Macs. The agent always reads/writes from the same file structure. No need for Claude to access Dropbox directly — Dropbox handles sync.

---

## Proposed File Structure

```
~/Dropbox/
  NoteInbox/
    Inq/                          ← Raw Inq exports (transcript + optional PNG)
    Otter/                        ← Raw Otter.ai exports (.txt or .docx)
    Manual/                       ← Drop zone for ad-hoc notes from any source
    Processed/                    ← Source files moved here after processing

  GlenVault/                      ← Obsidian vault root
    Projects/
      Calico/
        Notes/                    ← Raw/lightly edited notes
        Transcripts/              ← Raw transcript files
        AI Analyzed Notes/
          2026/
            W16_Apr14-Apr20/
            W17_Apr21-Apr27/
            ...
        Action Items/
          2026/
            W16_Apr14-Apr20/
            W17_Apr21-Apr27/
        Weekly Reports/
          2026/
        People/                   ← One .md per person; auto-linked to their notes/AIs
      Zelestra/
        (same structure)
      ...
    Attachments/                  ← Page images from Inq
    Templates/                    ← Claude output templates
```

---

## Build Phases

### Phase 1 — Processing Pipeline (MVP)
**Goal:** Raw file in → structured `.md` in vault, zero manual steps.

Tasks:
- [ ] Confirm Glen's exact Dropbox vault path and Mac setup
- [ ] Define tag taxonomy (initial set: `#project-calico`, `#zelestra`, `#solar-tax-equity`, `#sce`, etc.)
- [ ] Write the Claude processing prompt/template
  - Extracts: date, participants, topic
  - Generates: 3–5 sentence summary, action items with owners, key decisions
  - Outputs: YAML frontmatter + structured markdown sections
  - Auto-detects project from content; creates new project folder if new name encountered
  - Maintains per-person `.md` files under `People/` with back-links
- [ ] Write processing script (Python recommended for robustness)
  - Uses `watchdog` (macOS file watcher) to monitor all three inbox folders: `Inq/`, `Otter/`, `Manual/`
  - Triggers immediately on new file drop — no need to wait for scheduled scan
  - Pipes each file through Claude
  - Routes output to correct vault subfolder
  - Moves source file to `Processed/`
- [ ] Test with 5–10 real Inq and Otter files; refine template
- [ ] Set up script to run as a persistent background process on Glen's Mac (launchd daemon)

**Deliverable:** Fully automated event-driven processing — any file dropped in any inbox folder is analyzed within seconds.

---

### Phase 2 — Dashboard (Query Interface)
**Goal:** Web UI where Glen can browse, query, and submit notes for analysis.

Tasks:
- [ ] Choose stack (lightweight: plain HTML/JS reading local vault files; or Next.js app for richer UX)
- [ ] Build file tree / folder browser — mirrors vault Projects structure
- [ ] Tag + participant filter panel
- [ ] Note viewer — renders markdown with frontmatter display
- [ ] AI chat panel — natural language queries across all notes (e.g., "all Project Calico meetings this quarter", "open action items across all meetings", "all notes mentioning David at Vistra")
- [ ] **Note submission panel** — Glen can type/paste a note directly in the dashboard OR drag-and-drop a file; submission writes it to `NoteInbox/Manual/` which auto-triggers the pipeline
- [ ] Refresh button — re-indexes vault changes
- [ ] User guide / help overlay explaining that edits to existing notes must go through Obsidian directly

**Deliverable:** Standalone dashboard app Glen can open on any of his Macs.

---

### Phase 3 — Weekly Rollup Automation
**Goal:** Every Friday, per-project AI runs a week-in-review and produces next-week action items automatically.

Tasks:
- [ ] Build weekly rollup script
  - Collects all new AI Analyzed Notes for the current week, per project
  - Prompts Claude to summarize the week and draft action items for the following week
  - Writes output to `Weekly Reports/YYYY/` and `Action Items/YYYY/WNN.../`
- [ ] Ensure weekly outputs are cross-linked to their source notes
- [ ] Schedule via launchd to run every Friday at 5 PM (confirm time with Glen)

**Deliverable:** Automated weekly report + action item file per active project, every Friday.

---

### Phase 4 — Per-Project AI PM Agents *(future)*
**Goal:** Each project has a dedicated agent with memory, context, and generative output capabilities.

Design considerations (to build toward now):
- Agent knows the project's people, history, decisions, and open items from the vault
- Generates on demand: PowerPoints, due diligence checklists, action item trackers
- Learns from each weekly rollup — memory grows over time
- Scoped: Calico PM knows Calico, not Zelestra

**No code in this phase yet** — but the vault structure and tagging schema must support agent handoff from Phase 1 forward.

---

## TODO — Backlog (added 2026-04-26)

### Dashboard / Frontend
- [x] **Delete transcript + all derived files** — `DELETE /api/files/note?path=...` reads `.meta.json` sidecar written at processing time and deletes analyzed note + action items + raw file. `deleteNote()` in `api.ts`.
- [x] **Copy-paste text in Submit tab** — SubmitPanel has Upload/Paste tab toggle. Paste tab has textarea + filename field → calls `/submit/text`.

### Processor / Claude Behavior
- [x] **Fix duplicate filenames across folders** — Action items files now get `-actions.md` suffix (e.g. `2026-04-26-data-center-actions.md`).
- [x] **Project tags in notes** — Tag taxonomy updated to short form: `#calico`, `#cobia`, etc.
- [x] **Skip meeting niceties** — SYSTEM_PROMPT updated to instruct Claude to ignore opening/closing small talk.

### Automation / Ops
- [x] **"Start my day" terminal command** — `start-my-day.sh` at repo root. Starts `python server.py --dev`, polls until API is ready, opens `http://localhost:3000`. Glen can alias it in his `.zshrc`.

---

## Key Decisions & Open Questions

| # | Question | Status |
|---|---|---|
| 1 | Exact Dropbox vault path on Glen's Mac | **Need from Glen** |
| 2 | Confirm full tag taxonomy | **Need from Glen** |
| 3 | Does Glen want Obsidian installed, or is vault purely for the dashboard? | **Need from Glen** |
| 4 | Dashboard stack preference (simple vs. full web app) | To propose |
| 5 | Weekly rollup time preference (Friday — what time?) | To confirm |

---

## Reference Files

| File | Location |
|---|---|
| Process spec | `C:\Users\danve\Projects\GNM\process_summary.txt` |
| Process diagram | `C:\Users\danve\Projects\GNM\process_map.pdf` |
| System overview & vault structure proposal | `C:\Users\danve\obsidian\DVSB\Projects\In Progress\Glen's Note Dashboard\System Overview.md` |
| Stakeholder communications (Glen's words) | `C:\Users\danve\obsidian\DVSB\Projects\In Progress\Glen's Note Dashboard\Stakeholder Communications.md` |
| Token usage tracker | `C:\Users\danve\Projects\GNM\token_usage.md` |
