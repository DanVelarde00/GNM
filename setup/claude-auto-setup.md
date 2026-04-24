# Automated Setup — Give This to Claude

This doc is a **prompt for Claude Code**. Paste it (or tell Claude to read it) and Claude will do the entire GNM setup for you. At the end, Claude tells you exactly what you still need to finish manually.

---

## Part A — Before you paste this into Claude (5 minutes)

Three things Claude can't do for you:

### 1. Install Claude Code on your Mac

Claude Code is the terminal tool that runs these instructions. Install it from **https://claude.com/code** using the Mac installer — it doesn't require Node or Python to be installed first.

After install, open Terminal (`Cmd + Space` → "Terminal") and run:

```bash
claude
```

Sign in when prompted. You're now in a Claude Code session.

### 2. Get an Anthropic API key

1. Go to https://console.anthropic.com/
2. Sign in with your normal email
3. **Settings → Billing** → add **$5** in credits
4. **Settings → API Keys → Create Key**, name it `GNM`, copy the full key (starts with `sk-ant-`)
5. Paste it into a notes app — you'll hand it to Claude when it asks

### 3. (Optional) Have your Otter.ai email + password ready

If you want Otter transcripts auto-pulled (strongly recommended), have your Otter login ready to paste when Claude asks.

---

## Part B — Paste this into your Claude Code session

Open the Claude Code session and paste **everything below the line**, exactly as-is. Claude will take it from there.

---

```
You are setting up the GNM (Glen's Note Management) system on Glen's Mac.
Glen is a business owner, not a developer. Be warm, clear, and explicit.
When you need something from him (password, API key, decision), STOP and ask
in plain language. Don't assume he's watching — he may be getting coffee.
Never guess values he needs to provide.

Follow every step in order. After each step, print a one-line status
("✓ Step N done" or "✗ Step N blocked because ..."). Do not skip the
verification commands — they catch problems early.

═══════════════════════════════════════════════════════════
GNM AUTOMATED SETUP — TARGET: macOS 13+
═══════════════════════════════════════════════════════════

## Step 0 — Sanity checks

Run each of these. Report the output of each.

  uname -sm                 # expect: Darwin arm64 or Darwin x86_64
  sw_vers -productVersion   # expect: 13.x or higher
  echo $HOME                # expect: /Users/<something>
  pwd

If macOS is older than 13, STOP and tell Glen to update macOS first.

## Step 1 — Install Homebrew if missing

  brew --version

If that errors, install Homebrew:

  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

⚠️ This will prompt for Glen's Mac password. Tell him out loud:
   "Homebrew is about to ask for your Mac login password in the Terminal.
    Type it when prompted — it won't show any characters, that's normal."

After install, add brew to PATH (both commands — check chip type first):

  if [[ -x /opt/homebrew/bin/brew ]]; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/usr/local/bin/brew shellenv)"
  fi

Verify: brew --version should work now.

## Step 2 — Install Python 3.11, Node 20, Git, GitHub CLI

  brew install python@3.11 node@20 git gh
  brew link --force --overwrite node@20

Verify all four:

  python3.11 --version    # Python 3.11.x
  node --version          # v20.x.x
  npm --version
  git --version
  gh --version

## Step 3 — Install Obsidian and (if missing) Dropbox

  brew list --cask obsidian >/dev/null 2>&1 || brew install --cask obsidian

Check if Dropbox is already installed and syncing:

  ls ~/Dropbox >/dev/null 2>&1 && echo "Dropbox present" || echo "Dropbox missing"

If Dropbox is missing, install it:

  brew install --cask dropbox

Then STOP and tell Glen:
  "Dropbox has been installed but you need to sign in before we continue.
   Open Dropbox from Launchpad or Applications, sign in with your account,
   wait until you see a ~/Dropbox folder appear in Finder, then tell me 'go'."

Wait for Glen to say go before continuing.

## Step 4 — Clone GNM

  mkdir -p ~/Projects
  cd ~/Projects
  if [ -d GNM ]; then
    cd GNM && git pull
  else
    git clone https://github.com/DanVelarde00/GNM.git
    cd GNM
  fi
  pwd    # should print /Users/<glen>/Projects/GNM

## Step 5 — Create the .env file

  cp .env.example .env

Now STOP and ask Glen:
  "Paste your Anthropic API key (starts with sk-ant-). I'll put it in .env.
   It stays on your Mac only — never committed to GitHub."

Also ask (separately):
  "Do you want Otter auto-pull? If yes, paste your Otter.ai email and
   password, each on a new line. If no or 'skip', we'll leave it blank —
   you can always add it later."

Write the values into .env using this pattern (do NOT echo the key back):

  # Use sed or Python to edit .env — NEVER print Glen's actual key to chat
  python3.11 - <<'PY'
  from pathlib import Path
  env = Path(".env")
  text = env.read_text()
  # Replace placeholder with real key (key comes from the variable you stored)
  # ... update ANTHROPIC_API_KEY, OTTER_EMAIL, OTTER_PASSWORD lines ...
  env.write_text(text)
  PY

Verify WITHOUT printing secrets:

  grep -c "^ANTHROPIC_API_KEY=sk-ant-" .env   # should print 1
  grep -c "^ANTHROPIC_API_KEY=sk-ant-xxxxx" .env   # should print 0

If verification fails, STOP and tell Glen.

## Step 6 — Python virtual environment + dependencies

  python3.11 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt

Verify:

  python -c "import anthropic, fastapi, whoosh, dotenv; print('python deps OK')"

## Step 7 — Dashboard dependencies

  cd dashboard
  npm install
  cd ..

Verify dashboard/node_modules/next exists:

  test -d dashboard/node_modules/next && echo "node deps OK" || echo "NODE DEPS FAILED"

## Step 8 — Create the Obsidian vault + Dropbox inbox

The setup_vault.py script is interactive. Run it and answer the three
prompts with defaults (three Enters + Y):

  printf "\n\n\nY\n" | python setup_vault.py

Verify the expected folders now exist:

  ls ~/obsidian/GlenVault/Projects     # should list Calico, Cobia, etc.
  ls ~/Dropbox/NoteInbox               # should list Inq, Otter, Manual, Processed

If either ls fails, STOP and debug. Possible cause: Dropbox hasn't finished
syncing and ~/Dropbox doesn't exist yet.

## Step 9 — Build the dashboard for production

  cd dashboard
  npm run build
  cd ..

Verify build succeeded:

  test -d dashboard/.next && echo "build OK" || echo "BUILD FAILED"

## Step 10 — Start the server in the background

Start it detached so this session can keep working:

  nohup ./venv/bin/python server.py > server.log 2>&1 &
  echo "Server PID: $!"

Wait 8 seconds, then check it's healthy:

  sleep 8
  curl -sS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8000/api/files/tree

Expect "HTTP 200". If you get connection refused, check the tail of server.log
for errors and share them with Glen.

## Step 11 — End-to-end test

Write a test note, wait for the processor to pick it up, confirm it reached
the vault.

First, trigger the processor once manually:

  ./venv/bin/python - <<'PY'
  from pathlib import Path
  test = Path.home() / "Dropbox" / "NoteInbox" / "Manual" / "setup-test.txt"
  test.write_text(
      "Quick setup test on " + __import__("datetime").datetime.now().isoformat() + ".\n"
      "Meeting with Dan about the GNM rollout for Calico.\n"
      "Action: Dan to confirm install completed. Glen to review dashboard.\n"
  )
  print(f"wrote {test}")
  PY

  ./venv/bin/python run.py   # one-shot scan, processes the test file

Verify an analyzed note landed in the vault:

  find ~/obsidian/GlenVault/Projects/Calico/"AI Analyzed Notes" -name "*setup-test*" -o -name "*.md" -newer .env | head -5

If you see a new .md file under that path, processing works end-to-end.

Clean up the test file from Processed/ if Glen prefers:

  # (optional) rm ~/Dropbox/NoteInbox/Processed/setup-test.txt

═══════════════════════════════════════════════════════════
## Final report — print this for Glen
═══════════════════════════════════════════════════════════

Print a summary in this exact format, filling in actual values:

---

### ✅ What's installed and working

- Homebrew, Python 3.11, Node 20, Git, GitHub CLI: all installed
- Obsidian: installed (app icon in Applications)
- Dropbox: [installed / was already present]
- GNM code: cloned to ~/Projects/GNM
- Python venv + dependencies: installed
- Dashboard dependencies: installed
- Dashboard production build: complete
- Vault: created at ~/obsidian/GlenVault with [N] projects
- Inbox: created at ~/Dropbox/NoteInbox
- Server: running in background on PID [X], health check passed
- End-to-end test: [passed / failed with reason]

### 🌐 Open these URLs now

- Dashboard:  http://localhost:8000
- API docs:   http://localhost:8000/docs

### 🫵 What YOU still need to do manually

1. **Open Obsidian** (from Applications or Launchpad)
   - Click "Open folder as vault"
   - Press Cmd+Shift+G, paste: ~/obsidian/GlenVault
   - Click Open
   - When prompted, turn OFF Restricted Mode and ENABLE the Dataview plugin

2. **Verify the dashboard is accessible**
   - Visit http://localhost:8000 in Chrome or Safari
   - You should see a sidebar with Vault / Search / Chat / Action Items / Trackers / Processor / Submit

3. **Start the background processor**
   - In the dashboard, go to the **Processor** page
   - Click **Start**
   - You should see log lines scrolling — that's the 60-second poll

4. **(If you skipped Otter setup)** Add Otter credentials later
   - Edit ~/Projects/GNM/.env, fill in OTTER_EMAIL and OTTER_PASSWORD
   - Restart the server

5. **Set up auto-start on login** (optional)
   - See setup/05-run-dashboard.md section 5.8 for the crontab one-liner

### 🆘 If something's off

- Server not responding? Check: tail -50 ~/Projects/GNM/server.log
- Dashboard shows errors? Open DevTools (Cmd+Opt+I) → Console, share what you see
- Contact Dan Velarde: dan.velarde@outlook.com

### 🔑 Important paths to remember

- Your vault:     ~/obsidian/GlenVault
- Your inbox:     ~/Dropbox/NoteInbox
  - Drop Inq notes → Inq/
  - Drop anything else → Manual/
- The code:       ~/Projects/GNM
- Your secrets:   ~/Projects/GNM/.env  (never share this file)

### To restart the server later

  cd ~/Projects/GNM
  source venv/bin/activate
  python server.py

To stop: find the process and kill it, or close Terminal.

---

END OF SETUP. Welcome to GNM, Glen.
```

---

## Part C — If Claude gets stuck

Claude will stop and ask you for input at three points:

1. **Mac password** during Homebrew install (just your normal login password)
2. **Anthropic API key** (the `sk-ant-...` string you copied earlier)
3. **Otter credentials** (or say "skip" if you don't want auto-pull yet)

If Claude reports a failure at any step, **copy the error message and send it back to Claude** — it can almost always self-correct. If it can't, email Dan: dan.velarde@outlook.com with:

- Which step failed (e.g., "Step 7")
- The error message
- What Claude tried

---

## Part D — After Claude finishes (~5 minutes of manual)

Claude will print a "What YOU still need to do manually" list. It boils down to:

1. **Open Obsidian** → Open folder as vault → `~/obsidian/GlenVault` → enable Dataview
2. **Open http://localhost:8000** → go to Processor page → click Start
3. **(Optional)** Set up auto-start on login (see `05-run-dashboard.md` §5.8)

That's it. Total time from paste to working system: **~15 minutes** (mostly waiting on brew + npm installs).
