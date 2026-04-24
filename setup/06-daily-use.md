# Step 6 — Daily Workflow

Here's what using GNM looks like day-to-day.

---

## The one-command start

Every time you want to use GNM, open Terminal and:

```bash
cd ~/Projects/GNM && source venv/bin/activate && python server.py --dev
```

Leave that Terminal window open. Open http://localhost:3000 in your browser.

When you're done for the day, go back to the Terminal and press `Ctrl + C`.

---

## How notes get into the system

There are **four ways** a note or transcript enters the pipeline:

### 1. Otter.ai transcripts (fully automatic)

After you record a meeting in Otter, the transcript shows up in your Otter account within a few minutes. GNM's Otter auto-pull checks every 60 seconds and downloads anything new. No action needed from you.

### 2. Inq pen notes

When you take handwritten notes with the Inq pen, export them to `~/Dropbox/NoteInbox/Inq/`. The processor picks them up within 60 seconds.

### 3. Manual drops (typed notes, emails, docs)

Drop **any** `.txt`, `.md`, `.docx`, or `.pdf` file into `~/Dropbox/NoteInbox/Manual/`. It gets processed next poll cycle.

### 4. Drag-and-drop via dashboard

Open the **Submit** page in the dashboard → drag a file onto the drop zone → it lands in the inbox and processes immediately.

---

## What happens to a file once it's processed

For each new file, GNM:

1. Sends the content to Claude with a structured prompt
2. Gets back a JSON with: project, date, participants, summary, action items, decisions, tags
3. Writes three (or four) files into your vault:
   - **Analyzed note** → `Projects/<Project>/AI Analyzed Notes/YYYY/WNN/YYYY-MM-DD-topic.md`
   - **Action items** → `Projects/<Project>/Action Items/YYYY/WNN/...` (if any were found)
   - **Raw source** → `Projects/<Project>/Transcripts/...` or `.../Notes/...` (copy of original)
   - **People files** → `Projects/<Project>/People/<Name>.md` (created if new)
4. Moves the original file from `Inbox/` to `Inbox/Processed/` so it's not processed twice

---

## Using the dashboard

### Vault browser (`/vault`)

Click through the folder tree on the left. Click any `.md` file to view it. Click the pencil icon to edit — your changes save directly to the file on disk.

### Search (`/search`)

Full-text search across every note in your vault. Uses a Whoosh index that updates as new notes are added.

### AI Chat (`/chat`)

Ask questions about your notes. Example: *"What are my open action items on Calico this week?"* or *"When did Sarah mention the transformer specs?"*

Claude searches your vault, pulls the relevant notes, and answers with citations back to the source files.

### Action Items (`/action-items`)

Every action item from every project in one list. Check them off here — the checkboxes sync back to the original markdown files. Filter by project, by person, or by completed status.

### Trackers (`/trackers`)

You can define custom categories beyond action items. Example: create a tracker called **"Substations"** — from then on, Claude will extract any substation mentions from new notes and drop them in `Projects/<P>/Substations/`.

Each new tracker:
1. Creates a folder in every project
2. Restarts the processor with an updated prompt
3. Starts extracting from the next note processed

### Processor (`/processor`)

Start/stop/restart the background processor. Shows live log output. You'll mostly leave this alone after initial setup.

### Submit (`/submit`)

Drag-and-drop files into the inbox from the browser.

---

## Typical week

**Monday–Friday mornings:**
- GNM is already running, background processor is active
- You record meetings in Otter → transcripts flow in automatically
- You drop any extra notes/docs into Dropbox inbox
- You check the **Action Items** page for the day's todos

**Mid-week:**
- Ask the **Chat** something like *"summarize this week's Calico progress"*
- Browse the **Vault** to review analyzed notes

**Friday:**
- Weekly reports will land in `Projects/<P>/Weekly Reports/YYYY/` (Phase 1.5 — coming)
- Review action items, mark completed ones

---

## Updating GNM when Dan pushes code changes

```bash
cd ~/Projects/GNM
git pull
source venv/bin/activate
pip install -r requirements.txt       # if Python deps changed
cd dashboard && npm install && cd ..  # if Node deps changed
# If running in production mode:
cd dashboard && npm run build && cd ..
```

Then restart the server (Ctrl+C, then start it again).

---

## Checkpoint

You now know:

- How to start and stop the system
- The four ways notes enter the pipeline
- What each dashboard page does
- How to apply updates

---

## Optional reading

- [`architecture.md`](architecture.md) — How everything connects under the hood
- [`paths-cheatsheet.md`](paths-cheatsheet.md) — All paths the system uses, and which are safe to change
- [`troubleshooting.md`](troubleshooting.md) — Fixes for common issues
