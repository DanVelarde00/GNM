# Step 2 — Download the Code + Set Up Your Keys

Now we'll grab the GNM code from GitHub and give it your API keys so it can talk to Claude and Otter.

---

## 2.1 — Pick where the code lives

The standard place for development projects on Mac is `~/Projects/`.

`~` is your home folder — equivalent to `/Users/glen/`. So `~/Projects/GNM` means `/Users/glen/Projects/GNM`.

Create that folder and move into it:

```bash
mkdir -p ~/Projects
cd ~/Projects
```

---

## 2.2 — Clone the repo

This downloads the GNM code:

```bash
git clone https://github.com/DanVelarde00/GNM.git
cd GNM
```

You should now see a prompt like `glen@MacBook-Pro GNM %`. Confirm you're in the right place:

```bash
pwd
ls
```

`pwd` should print `/Users/glen/Projects/GNM` (with your username). `ls` should show files like `run.py`, `processor.py`, `server.py`, `dashboard/`, `setup/`.

---

## 2.3 — Create your `.env` file

The `.env` file holds your secret API keys. It is **never** committed to GitHub (it's listed in `.gitignore`).

Copy the template to a real `.env`:

```bash
cp .env.example .env
```

Now open it in a text editor. Easiest: use the built-in TextEdit:

```bash
open -e .env
```

(Or if you prefer VS Code and you have it installed: `code .env`)

You'll see:

```
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Otter.ai credentials (optional — enables auto-pull from Otter)
OTTER_EMAIL=
OTTER_PASSWORD=

# Override default paths if needed
# GNM_VAULT_PATH=~/obsidian/GlenVault
# GNM_INBOX_PATH=~/Dropbox/NoteInbox
# GNM_OTTER_GDRIVE_PATH=~/Google Drive/My Drive/Otter
```

---

## 2.4 — Get your Anthropic API key

1. Go to https://console.anthropic.com/
2. Sign in (or sign up — use your normal email)
3. Click **Settings → API Keys**
4. Click **Create Key**, name it `GNM`, copy the key (starts with `sk-ant-`)
5. Add at least **$5 in credits** under **Settings → Billing** (this is what pays for Claude calls)

Paste the key into `.env`, replacing `sk-ant-xxxxx`:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

> **Cost check:** Processing one typical meeting costs roughly $0.02–$0.05. $5 in credits will easily cover the first few weeks of real use.

---

## 2.5 — (Optional) Add your Otter.ai credentials

If you fill these in, GNM will automatically pull new transcripts from your Otter account every time it runs. Skip this section if you'd rather export manually (you can always add them later).

```
OTTER_EMAIL=glen@calicoinfrastructure.com
OTTER_PASSWORD=your-otter-password-here
```

> **Security:** This file stays only on your Mac and is excluded from Git. No one else will see it. The password is used once per session to log in to Otter's API and fetch your transcripts.

---

## 2.6 — (Optional) Override default paths

The bottom of `.env` has commented-out path overrides. **Leave them commented for now** — the defaults work fine for most people:

- Vault default: `~/obsidian/GlenVault`
- Inbox default: `~/Dropbox/NoteInbox`
- Otter Google Drive sync: `~/Google Drive/My Drive/Otter`

If you want to use custom locations (e.g., you prefer your vault somewhere else), uncomment the relevant line and set a new path. See [`paths-cheatsheet.md`](paths-cheatsheet.md) for guidance on which paths are safe to change.

---

## 2.7 — Save the file

In TextEdit: `Cmd + S`, then close the window.

**Double-check it saved correctly:**

```bash
cat .env
```

You should see your keys filled in. If it still shows `sk-ant-xxxxx`, TextEdit may have saved it as `.env.rtf` — open Finder (`open .`), confirm the file is named exactly `.env` with no extension.

---

## Next

Keys are in place. Next we install the code's dependencies: [`03-install.md`](03-install.md).
