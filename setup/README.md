# GNM Setup Guide — For Glen

Welcome, Glen. This folder walks you through setting up **Glen's Note Management (GNM)** on your Mac, from zero to a fully running system.

You do **not** need to be a developer to follow this. Every command is copy-pasteable. Each file explains *what* the step does and *why*, so by the end you'll understand how the whole system fits together.

---

## What you're about to install

GNM is a small pipeline that:

1. Pulls your meeting transcripts from **Otter.ai** automatically
2. Watches a **Dropbox inbox** folder for notes you drop in (Inq pen scans, manual files)
3. Sends each new file to **Claude AI** to extract a summary, action items, decisions, people, and tags
4. Writes the result into your **Obsidian vault**, organized by project and week
5. Gives you a **web dashboard** to browse, search, chat with your notes, and tick off action items

Three moving pieces you'll end up with:

| Piece | What it is | Where it lives |
|---|---|---|
| **Vault** | Your knowledge base — organized markdown files | `~/obsidian/GlenVault` |
| **Inbox** | Drop-zone for new notes | `~/Dropbox/NoteInbox` |
| **GNM app** | The code that processes + serves the dashboard | `~/Projects/GNM` |

---

## Two paths — pick one

### 🚀 Fast path (recommended): Let Claude do it for you

Open [`claude-auto-setup.md`](claude-auto-setup.md) — it's a prompt you paste into Claude Code that runs the entire install automatically. You'll need to tap your password once and paste your Anthropic API key when asked. Total time ~15 minutes.

### 🛠️ Manual path: Step through it yourself

Read these in order if you'd rather understand every command:

1. [`01-prerequisites.md`](01-prerequisites.md) — Install Homebrew, Python, Node, Git
2. [`02-clone-and-keys.md`](02-clone-and-keys.md) — Download the code + set up your API keys
3. [`03-install.md`](03-install.md) — Install the Python + Node packages the app needs
4. [`04-vault-setup.md`](04-vault-setup.md) — Create your Obsidian vault + inbox folders
5. [`05-run-dashboard.md`](05-run-dashboard.md) — Start the system and open the dashboard
6. [`06-daily-use.md`](06-daily-use.md) — How to use it day-to-day

Supporting docs:

- [`architecture.md`](architecture.md) — How every part connects (read this if you want the mental model)
- [`paths-cheatsheet.md`](paths-cheatsheet.md) — Mac path conventions + all the paths this system uses
- [`troubleshooting.md`](troubleshooting.md) — Common issues and fixes

---

## Time estimate

- First-time install with no prior dev tools: **~45–60 minutes**
- If you already have Homebrew + Python + Node: **~15 minutes**

---

## Before you start

You'll need:

- A Mac (macOS 13 or newer)
- **Anthropic API key** — get one at https://console.anthropic.com/ (requires a $5 minimum credit)
- **Otter.ai account** (optional but recommended) — your normal login email + password
- **Dropbox** installed and syncing on this Mac
- About 500 MB free disk space for the tools + dependencies

Ready? Open [`01-prerequisites.md`](01-prerequisites.md).
