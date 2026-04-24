# Step 1 — Install Prerequisites

Before we can run GNM, your Mac needs four tools: **Homebrew**, **Python**, **Node.js**, and **Git**. Each has a specific job.

---

## What each tool does

| Tool | Why we need it |
|---|---|
| **Homebrew** | Mac package manager — lets you install the other three with one command each |
| **Python 3.11+** | Runs the processor + backend (the part that talks to Claude and Otter) |
| **Node.js 20+** | Runs the dashboard UI (the web app you'll look at in your browser) |
| **Git** | Downloads the GNM code from GitHub and lets you update it later |

---

## 1.1 — Open Terminal

Press `Cmd + Space`, type `Terminal`, press Enter. A window will open with a prompt like `glen@MacBook-Pro ~ %`.

Everything in this guide happens in Terminal. Copy each command, paste with `Cmd + V`, press Enter.

---

## 1.2 — Install Homebrew

Paste this and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

It'll ask for your Mac password (you won't see it as you type — that's normal). Wait for it to finish (2–5 minutes).

**After it finishes**, it will print two lines that look like this — **run them**:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

This adds Homebrew to your PATH so Terminal can find it.

**Verify:**

```bash
brew --version
```

You should see something like `Homebrew 4.x.x`. If you do, you're good.

---

## 1.3 — Install Python 3.11

```bash
brew install python@3.11
```

**Verify:**

```bash
python3.11 --version
```

Should print `Python 3.11.x`. If yes, move on.

---

## 1.4 — Install Node.js 20

```bash
brew install node@20
brew link --force --overwrite node@20
```

**Verify:**

```bash
node --version
npm --version
```

Should print `v20.x.x` and a version like `10.x.x`.

---

## 1.5 — Install Git

Most Macs already have Git. Check:

```bash
git --version
```

If it prints a version, skip ahead. If it says "install Command Line Tools", let it pop up the installer and click Install. Wait for it to finish (5–10 minutes).

---

## 1.6 — (Optional but recommended) GitHub CLI

The `gh` tool makes it easier to pull updates later.

```bash
brew install gh
gh auth login
```

Follow the prompts: choose **GitHub.com**, **HTTPS**, **Login with a web browser**, paste the code, sign in.

---

## You're done with prerequisites

You now have all the tools the system needs. Next: [`02-clone-and-keys.md`](02-clone-and-keys.md) — download the GNM code and set up your API keys.
