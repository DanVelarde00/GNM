# Step 4 — Create Your Vault and Inbox

This is where the system's actual data will live. We'll run a one-time setup script that:

1. Creates your **Obsidian vault** folder with the right structure
2. Creates your **Dropbox inbox** folder with subfolders for each source
3. Writes starter templates and a Home dashboard
4. Pre-configures Obsidian's settings + the Dataview plugin

---

## 4.1 — Pre-flight checks

Make sure **Dropbox** is installed and syncing on this Mac. Check that you have a `~/Dropbox` folder:

```bash
ls ~/Dropbox
```

If that errors, install Dropbox first from https://www.dropbox.com/install and sign in. Then come back.

Make sure you're in the project folder with the virtual environment active:

```bash
cd ~/Projects/GNM
source venv/bin/activate
```

Your prompt should show `(venv)`.

---

## 4.2 — Run the vault setup script

```bash
python setup_vault.py
```

The script will ask you three things. Here's what they mean and what to answer:

### Question 1: Obsidian vault location

```
Obsidian vault location [~/obsidian/GlenVault]:
```

**Recommended answer:** Press Enter to accept the default (`~/obsidian/GlenVault`).

This folder is **local only** — not in Dropbox. Obsidian works best on a local disk. You'll open it in the Obsidian app to browse your notes.

If you want a custom location, type a full path and press Enter. Example: `/Users/glen/Documents/GlenVault`.

### Question 2: Note inbox location (Dropbox)

```
Note inbox location (Dropbox) [~/Dropbox/NoteInbox]:
```

**Recommended answer:** Press Enter to accept the default (`~/Dropbox/NoteInbox`).

This folder **must be inside Dropbox**. That's how notes from your phone or from Inq pen get synced to your Mac for processing.

### Question 3: Initial projects

```
Initial projects (comma-separated) [Calico, Cobia, Personal, Vistra, Zelestra]:
```

**Recommended answer:** Press Enter to accept the defaults.

These are the projects you're actively working on. Each becomes a subfolder in the vault with its own Notes, Transcripts, AI Analyzed Notes, Action Items, and People folders.

> Don't worry about getting this list perfect. If you mention a new project in a note later (e.g., "Goldstone"), the system will auto-create the folder structure for it.

---

## 4.3 — Confirm and let it run

The script will show a summary:

```
  Vault:    /Users/glen/obsidian/GlenVault
  Inbox:    /Users/glen/Dropbox/NoteInbox
  Projects: Calico, Cobia, Personal, Vistra, Zelestra

Proceed? [Y/n]:
```

Press **Y** and Enter. It'll create all the folders and print a success message.

---

## 4.4 — What just got created

### Your vault (`~/obsidian/GlenVault/`)

```
GlenVault/
├── .obsidian/              ← Obsidian settings (Dataview plugin pre-enabled)
├── Attachments/            ← Where images/PDFs you paste into notes go
├── Templates/              ← Starter templates for analyzed notes, action items, etc.
├── Home.md                 ← Your dashboard — opens automatically in Obsidian
└── Projects/
    ├── Calico/
    │   ├── Notes/              ← Raw notes (from Inq pen)
    │   ├── Transcripts/        ← Raw transcripts (from Otter)
    │   ├── AI Analyzed Notes/  ← Claude's output, organized by year + week
    │   ├── Action Items/       ← Extracted todos, organized by year + week
    │   ├── Weekly Reports/     ← Friday rollups (Phase 1.5)
    │   └── People/             ← Auto-created person files with Dataview queries
    ├── Cobia/        (same structure)
    ├── Personal/     (same structure)
    ├── Vistra/       (same structure)
    └── Zelestra/     (same structure)
```

### Your inbox (`~/Dropbox/NoteInbox/`)

```
NoteInbox/
├── Inq/         ← Drop Inq pen scans here (exports from the Inq app)
├── Otter/       ← Optional extra landing for Otter files (auto-pull uses this)
├── Manual/      ← Drop anything else here (meeting notes you typed, emails, etc.)
└── Processed/   ← Files move here automatically after they're processed
```

---

## 4.5 — Open the vault in Obsidian

1. Download Obsidian from https://obsidian.md if you don't have it
2. Open Obsidian
3. Click **"Open folder as vault"**
4. Navigate to `~/obsidian/GlenVault` (you can type `Cmd + Shift + G` then `~/obsidian/GlenVault`)
5. Click **Open**
6. When Obsidian asks about "Restricted mode" or community plugins, **turn off Restricted mode** and **enable Dataview** when prompted

You should now see the Home note with empty Dataview queries (they'll fill in as you process notes).

---

## Checkpoint

You now have:

- A fully structured Obsidian vault at `~/obsidian/GlenVault`
- A synced Dropbox inbox at `~/Dropbox/NoteInbox`
- Obsidian installed and pointed at the vault

---

## Next

Time to start the system and try it: [`05-run-dashboard.md`](05-run-dashboard.md).
