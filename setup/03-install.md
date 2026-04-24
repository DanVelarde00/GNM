# Step 3 — Install Dependencies

The code we cloned is just source files. It depends on a bunch of external libraries (Anthropic's SDK, FastAPI, Next.js, etc.). This step installs them.

There are two dependency sets:

1. **Python packages** — for the processor + API backend (listed in `requirements.txt`)
2. **Node packages** — for the web dashboard (listed in `dashboard/package.json`)

---

## 3.1 — Make sure you're in the project folder

```bash
cd ~/Projects/GNM
pwd
```

Should print `/Users/glen/Projects/GNM`.

---

## 3.2 — Create a Python virtual environment

A **virtual environment** is an isolated bucket for this project's Python packages, so they don't conflict with anything else on your Mac. This is standard Python practice.

```bash
python3.11 -m venv venv
```

This creates a folder called `venv/` inside `GNM/`. It's already excluded from Git — don't worry about it.

**Activate the environment** (you'll need to do this every time you open a new Terminal window to work with GNM):

```bash
source venv/bin/activate
```

Your prompt will change to show `(venv)` at the front, like `(venv) glen@MacBook-Pro GNM %`. That means packages you install now will land inside `venv/` instead of being installed system-wide.

---

## 3.3 — Install the Python packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install ~15 packages (Anthropic SDK, FastAPI, Whoosh, etc.). Takes 1–2 minutes.

**Verify:**

```bash
python -c "import anthropic, fastapi, whoosh; print('OK')"
```

Should print `OK`. If you see an error, re-run the install command.

---

## 3.4 — Install the dashboard's Node packages

The dashboard is a Next.js app in the `dashboard/` subfolder. Install its dependencies:

```bash
cd dashboard
npm install
```

This takes 1–3 minutes and installs ~300 packages into `dashboard/node_modules/` (also excluded from Git).

When it's done, move back to the project root:

```bash
cd ..
```

---

## 3.5 — Build the dashboard (production mode only)

**Skip this if you plan to always run in dev mode.** If you want to run the dashboard in production mode (single URL at http://localhost:8000), build it now:

```bash
cd dashboard
npm run build
cd ..
```

This creates an optimized production build. Takes ~30 seconds. You only need to re-run this when you pull code updates.

If you skip this step, just always use `python server.py --dev` in Step 5 and everything works fine.

---

## Checkpoint

At this point you should have:

- `venv/` — Python virtual environment with all required packages
- `dashboard/node_modules/` — Node packages for the dashboard
- `.env` — Your API keys
- Clean Terminal prompt with `(venv)` prefix when active

---

## Next

Let's create your Obsidian vault and inbox: [`04-vault-setup.md`](04-vault-setup.md).
