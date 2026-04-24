# Troubleshooting

Common issues and how to fix them. Scan for your error message.

---

## Setup issues

### `command not found: brew`

Homebrew isn't on your PATH. Run:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
```

Close Terminal, reopen, try `brew --version` again.

---

### `command not found: python3.11`

Homebrew didn't link Python. Try:

```bash
brew link --force python@3.11
```

If that fails, reinstall:

```bash
brew reinstall python@3.11
```

---

### `command not found: node` after `brew install node@20`

Node 20 is keg-only and needs to be linked:

```bash
brew link --force --overwrite node@20
```

---

### Git asks for username/password when cloning

You're using HTTPS. Either:

- **Easiest:** Install GitHub CLI and authenticate: `brew install gh && gh auth login`
- **Or:** Use a personal access token as the password — make one at https://github.com/settings/tokens

---

### `.env` file won't save as `.env` (saves as `.env.rtf`)

TextEdit is saving as Rich Text. Fix it:

1. Open TextEdit → **Format → Make Plain Text** (`Cmd + Shift + T`)
2. Save again
3. If Finder shows `.env.rtf`, rename it: `mv ~/Projects/GNM/.env.rtf ~/Projects/GNM/.env`

Or use nano from Terminal instead:

```bash
nano ~/Projects/GNM/.env
```

(Ctrl+O to save, Enter to confirm, Ctrl+X to exit.)

---

### `pip: command not found` or installing to wrong Python

You forgot to activate the venv. Run:

```bash
cd ~/Projects/GNM
source venv/bin/activate
```

Your prompt should show `(venv)`. Then retry the `pip install` command.

---

### `npm install` fails with permission errors

You're probably installing globally. Make sure you're in the `dashboard/` folder:

```bash
cd ~/Projects/GNM/dashboard
npm install
```

---

## Runtime issues

### Dashboard shows "Failed to fetch" on every page

The FastAPI backend isn't running or crashed. Check the Terminal window running `python server.py`. If you see a stack trace, read the last few lines — usually a missing dependency or misconfigured path.

Common fix: make sure you ran `pip install -r requirements.txt` inside the activated venv.

---

### Port 3000 or 8000 already in use

Something else is on that port (or a previous server didn't shut down cleanly).

Find and kill it:

```bash
# Find what's using port 8000
lsof -iTCP:8000 -sTCP:LISTEN

# Kill it (replace 12345 with the PID from above)
kill 12345
```

Then restart `python server.py --dev`.

---

### Processor says "Otter pull failed: invalid credentials"

Check `.env` — your `OTTER_EMAIL` / `OTTER_PASSWORD` are wrong. Log in to otter.ai in a browser to confirm they work, update `.env`, restart the server.

If the credentials are correct but still failing, Otter may have rolled a session check. Open `.otter_state.json` and delete it to force re-auth (you'll re-pull recent transcripts — move duplicates out manually).

---

### Processor runs but no files appear in the vault

Check the Processor page log. Common causes:

1. **File format not supported** — GNM accepts `.txt`, `.md`, `.docx`, `.pdf` only
2. **Claude API error** — look for `rate_limit_error` or `authentication_error` in the log; check your Anthropic key and billing credits
3. **Wrong inbox path** — confirm your test file is actually in `~/Dropbox/NoteInbox/Manual/` (not `~/Dropbox/NoteInbox/Inbox/Manual/` — classic nesting mistake)

---

### `ANTHROPIC_API_KEY not set` error

`.env` isn't being read. Verify:

```bash
cd ~/Projects/GNM
cat .env | grep ANTHROPIC_API_KEY
```

If that shows your key, the file is fine. Make sure you're starting the server from inside `~/Projects/GNM/` (not a different directory).

---

### Search returns no results even though notes exist

The Whoosh index isn't built yet or got corrupted. Rebuild it:

```bash
cd ~/Projects/GNM
rm -rf data/search_index
```

Restart the server. The index rebuilds automatically the first time you search.

---

### A file got processed twice / duplicate vault notes

If a file appears in `Inbox/Processed/` AND its original folder, something failed partway. Safe to delete the duplicate in the vault (check timestamps — keep the newer one).

To avoid re-processing, make sure the inbox folders only contain truly new files.

---

### Chat says "no relevant notes found" when they clearly exist

The search index is out of date. Add a new note (anything) to trigger an index update, or manually rebuild as in the search issue above.

---

### Obsidian shows Dataview queries as plain text

The Dataview plugin isn't enabled. In Obsidian: **Settings → Community plugins → Turn off Restricted mode → Community plugins → Dataview → Enable**.

---

### Notes go to the wrong project

Claude's project detection is imperfect. Fixes:

1. **Mention the project explicitly** in the file content or filename (e.g., `2026-04-24-calico-permit.txt`)
2. **Rename the file** to include the project name before dropping it in the inbox
3. **Move the output manually** — the routing is just filesystem moves, nothing breaks

---

## Data recovery

### I deleted `~/obsidian/GlenVault/` by accident

Dropbox + Time Machine are your safety nets. Check Time Machine first (`open -a "Time Machine"`). If the vault was in Dropbox, restore from https://www.dropbox.com/deleted_files.

Going forward, set up Time Machine if you haven't: **System Settings → General → Time Machine**.

### I deleted `.env`

Just recreate it from `.env.example` and re-enter your keys:

```bash
cp .env.example .env
open -e .env
```

Your Anthropic key is retrievable from console.anthropic.com (or create a new one). Your Otter password is in your password manager.

---

## Getting help

- **Dan Velarde** — dan.velarde@outlook.com — for any GNM bugs, feature requests, or stuckness
- **Anthropic support** — https://support.anthropic.com for API issues
- **Obsidian Discord** — https://obsidian.md/community for vault/plugin issues

When reporting a bug to Dan, include:

1. What you did (exact command or click)
2. What you expected
3. What happened (paste the error message)
4. The last ~20 lines of the Processor log
