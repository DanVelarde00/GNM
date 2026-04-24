# Step 5 — Run the System

Everything's installed. Let's start the system and verify it works.

---

## 5.1 — What "running the system" means

There are two processes that make up GNM:

| Process | What it does | Port |
|---|---|---|
| **Backend (FastAPI)** | Watches your inbox, calls Claude, writes to the vault. Also serves the dashboard API. | 8000 |
| **Frontend (Next.js)** | The web UI you browse in Chrome/Safari | 3000 (dev) or served from 8000 (prod) |

The backend also manages a third thing: the **background processor** that polls Otter every 60 seconds and scans your inbox folders for new files. You'll start/stop that from the dashboard's Processor page.

---

## 5.2 — Start the server (dev mode)

Dev mode is the easiest way to run the system day-to-day. It starts both the backend and the frontend and auto-reloads when code changes.

```bash
cd ~/Projects/GNM
source venv/bin/activate
python server.py --dev
```

You'll see:

```
==================================================
  GNM Dashboard
  Mode: Development
  API:  http://localhost:8000
  UI:   http://localhost:3000
==================================================
[GNM] Next.js dev server starting on http://localhost:3000
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Give it 10–20 seconds to finish booting up.

---

## 5.3 — Open the dashboard

Open your browser to:

### **http://localhost:3000**

You should see the GNM dashboard with a sidebar listing: **Vault, Search, Chat, Action Items, Trackers, Processor, Submit**.

Click around — most pages will be empty since you haven't processed any notes yet. That's fine.

---

## 5.4 — Start the processor

Go to the **Processor** page in the sidebar.

Click **Start** (or **Restart** if it's already running).

You'll see a live log stream appear. It polls every 60 seconds for:

- New transcripts from Otter.ai (if you set credentials)
- New files in `~/Dropbox/NoteInbox/Inq/`
- New files in `~/Dropbox/NoteInbox/Manual/`
- New files in `~/Google Drive/My Drive/Otter/` (if you use the Google Drive integration)

The processor will run in the background as long as the server is running.

---

## 5.5 — Try it with a test file

Let's verify end-to-end processing with a quick test. In a **new** Terminal window (keep the server running in the first one):

```bash
cat > ~/Dropbox/NoteInbox/Manual/test-note.txt << 'EOF'
Meeting with Sarah from Calico about the substation permit on April 24, 2026.

We agreed:
- Dan to send revised site plan by Monday
- Sarah to schedule follow-up with Glen next week
- Need to confirm transformer specs with vendor

Sarah mentioned concerns about the timeline — the permit office is backed up 6 weeks.
EOF
```

Back in the dashboard, watch the Processor page. Within 60 seconds you'll see log lines about picking up `test-note.txt`, calling Claude, and writing files.

**Check what got created** — open Obsidian, navigate to `Projects/Calico/AI Analyzed Notes/2026/W17_Apr20-Apr26/` — you should see a new analyzed note with:

- Summary
- Participants: Sarah, Dan, Glen
- Action items (Dan → site plan, Sarah → follow-up, Dan → transformer specs)
- Tags like `#project-calico`, `#permit`
- Wiki-links to `[[Sarah]]`, `[[Dan]]`, `[[Glen]]`

Also check `Projects/Calico/People/` — a file for Sarah was auto-created.

If all that happened: **your system works end-to-end.** Congratulations.

---

## 5.6 — Stopping the server

In the Terminal running `python server.py --dev`, press `Ctrl + C`. Both the backend and the frontend will shut down. The background processor stops too.

To start again later, just re-run:

```bash
cd ~/Projects/GNM
source venv/bin/activate
python server.py --dev
```

---

## 5.7 — Alternative: Production mode (single URL)

Dev mode runs two URLs (3000 and 8000) and uses more RAM. If you prefer a single clean URL on port 8000 once things are working:

```bash
cd ~/Projects/GNM/dashboard
npm run build
cd ..
python server.py
```

Everything is served from http://localhost:8000. You only need to re-run `npm run build` when the dashboard code changes (i.e., when you pull updates).

---

## 5.8 — (Optional) Autostart on login

If you want GNM running all the time, you can set it to start when you log in to your Mac. Easiest way: use `crontab` with `@reboot`.

```bash
crontab -e
```

Add this line (press `i` to edit, `Esc` then `:wq` to save in vim):

```
@reboot cd /Users/glen/Projects/GNM && /Users/glen/Projects/GNM/venv/bin/python server.py > /Users/glen/Projects/GNM/server.log 2>&1
```

This runs the **production mode** server at boot. You'll need to have run `npm run build` at least once.

Skip this if you prefer to start it manually when you want it.

---

## Checkpoint

Your full system is running:

- Server on http://localhost:8000 (and http://localhost:3000 in dev mode)
- Processor watching inbox folders and pulling from Otter every 60s
- End-to-end test processed successfully

---

## Next

Learn how to use it day-to-day: [`06-daily-use.md`](06-daily-use.md).
