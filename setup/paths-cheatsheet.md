# Paths Cheatsheet

Every path GNM touches, and whether it's safe to change. Mac-specific.

---

## Mac path basics

| Symbol | What it means |
|---|---|
| `~` | Your home folder — `/Users/glen/` |
| `~/Foo` | `/Users/glen/Foo` |
| `/` | Root of your Mac's disk |
| Spaces in paths | Work fine, but when typing in Terminal wrap them in quotes: `"~/Google Drive/My Drive"` |

**Don't use `\`** (backslash) — that's Windows syntax. Mac uses forward slashes.

**Finder shortcut to navigate to a hidden path:** In Finder, press `Cmd + Shift + G`, type the path, press Enter.

---

## Paths GNM uses

### Code location (safe to change, but defaults are recommended)

| Path | What's there | Safe to change? |
|---|---|---|
| `~/Projects/GNM/` | The GNM source code (cloned from GitHub) | Yes — clone anywhere. If you do, adjust commands in all setup docs. |

---

### Vault + inbox (configurable in `.env`)

| Env variable | Default | What's there | Safe to change? |
|---|---|---|---|
| `GNM_VAULT_PATH` | `~/obsidian/GlenVault` | Your Obsidian knowledge base — all processed notes | **Yes**, change if you want vault elsewhere |
| `GNM_INBOX_PATH` | `~/Dropbox/NoteInbox` | Drop-zone for unprocessed notes + transcripts | **Yes**, but keep it in Dropbox (or whatever sync folder you use) |
| `GNM_OTTER_GDRIVE_PATH` | `~/Google Drive/My Drive/Otter` | Where Otter dumps to Google Drive (if you use that integration) | Yes, or leave empty if you don't use Google Drive |

**How to change:** Edit `.env` and uncomment/set the variable. Example:

```
GNM_VAULT_PATH=/Users/glen/Documents/Obsidian/GlenVault
GNM_INBOX_PATH=/Users/glen/Dropbox/Work/NoteInbox
```

Then re-run `python setup_vault.py` to create the folders in the new location (or move them manually). Restart the server.

---

### Inbox subfolders (fixed — created by `setup_vault.py`)

Inside whatever you set `GNM_INBOX_PATH` to:

| Path | Purpose |
|---|---|
| `Inq/` | Drop Inq pen exports here |
| `Otter/` | Otter auto-pull lands here |
| `Manual/` | Any other file you want processed |
| `Processed/` | Originals move here after processing — leave untouched |

---

### Vault subfolders (fixed — created by `setup_vault.py`)

Inside whatever you set `GNM_VAULT_PATH` to:

| Path | Purpose |
|---|---|
| `Attachments/` | Images/PDFs you paste into notes |
| `Templates/` | Starter templates (Analyzed Note, Action Items, Weekly Report, Person) |
| `Home.md` | Your dashboard with Dataview queries |
| `Projects/<Name>/Notes/` | Raw notes per project |
| `Projects/<Name>/Transcripts/` | Raw transcripts per project |
| `Projects/<Name>/AI Analyzed Notes/YYYY/WNN_MonDD-MonDD/` | Claude's analysis output |
| `Projects/<Name>/Action Items/YYYY/WNN_MonDD-MonDD/` | Extracted action items |
| `Projects/<Name>/Weekly Reports/YYYY/` | Friday rollups (Phase 1.5) |
| `Projects/<Name>/People/` | Auto-created person pages |
| `.obsidian/` | Obsidian settings + Dataview plugin |

---

### Inside the GNM code (don't move)

| Path | Purpose |
|---|---|
| `~/Projects/GNM/.env` | Your API keys — gitignored, never commit |
| `~/Projects/GNM/venv/` | Python virtual environment — recreatable |
| `~/Projects/GNM/data/trackers.json` | Custom tracker definitions |
| `~/Projects/GNM/data/search_index/` | Whoosh full-text index — recreatable |
| `~/Projects/GNM/.otter_state.json` | Otter pull history — recreatable |
| `~/Projects/GNM/dashboard/node_modules/` | Node packages — recreatable |
| `~/Projects/GNM/dashboard/.next/` | Next.js build cache — recreatable |

---

## Recommended setups

### Minimal (what 04-vault-setup.md describes)

```
~/Projects/GNM/                   ← the code
~/obsidian/GlenVault/             ← vault (local, not synced)
~/Dropbox/NoteInbox/              ← inbox (Dropbox synced)
```

### Vault on iCloud Drive (sync across your own devices)

```
GNM_VAULT_PATH=~/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/GlenVault
```

Pro: syncs to other Apple devices automatically. Con: can be flaky with Obsidian's rapid writes.

### Vault in Dropbox (sync with team)

```
GNM_VAULT_PATH=~/Dropbox/GlenVault
```

Pro: team members can see raw files. Con: Obsidian + Dropbox sometimes creates "Conflicted copy" duplicates with simultaneous edits.

**Best practice:** keep the vault local and use Obsidian Sync ($4/mo) if you need multi-device.

---

## URL paths (dashboard)

| URL | Page |
|---|---|
| `http://localhost:3000` | Dashboard home (dev mode) |
| `http://localhost:8000` | Dashboard home (production mode) + API |
| `http://localhost:3000/vault` | File browser |
| `http://localhost:3000/search` | Full-text search |
| `http://localhost:3000/chat` | AI chat |
| `http://localhost:3000/action-items` | Consolidated action items |
| `http://localhost:3000/trackers` | Custom trackers |
| `http://localhost:3000/processor` | Processor start/stop + logs |
| `http://localhost:3000/submit` | File drop zone |
| `http://localhost:8000/docs` | Auto-generated API docs (Swagger UI) |

---

## When you move a path — checklist

1. Edit `.env` with the new path
2. Move the actual folder to the new location (or re-run `setup_vault.py` to create fresh)
3. Restart the server
4. If you moved the vault: re-point Obsidian's "Open folder as vault" to the new path
