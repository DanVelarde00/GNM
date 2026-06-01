"""
GNM Configuration
All paths and settings in one place. Reads from .env for secrets.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── API ─────────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Current latest Sonnet — used for both processing (high volume, cheap) and chat.
CLAUDE_MODEL = "claude-sonnet-4-6"

# ── GitHub (AI chat files issues on the user's behalf) ───────────────────────
# Glen can tell the chat "this is broken, please fix" and it opens an issue Dan triages.
# Token optional — service falls back to the `gh` CLI when unset.
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "DanVelarde00/GNM")

# ── Otter MCP ────────────────────────────────────────────────────────────────
OTTER_MCP_URL = os.getenv("OTTER_MCP_URL", "")
OTTER_MCP_TOKEN = os.getenv("OTTER_MCP_TOKEN", "")
OTTER_POLL_INTERVAL = int(os.getenv("OTTER_POLL_INTERVAL", "21600"))  # seconds
# Max transcripts to pull/process per cycle (throttle to avoid 45-min batch stalls).
OTTER_MAX_PER_CYCLE = int(os.getenv("GNM_MAX_PER_CYCLE", "5"))

# ── Paths ───────────────────────────────────────────────────────────────────
# These are defaults for the prototype (Dan's machine).
# Glen's paths will differ — setup_vault.py handles his initial config.

VAULT_PATH = Path(os.getenv("GNM_VAULT_PATH", os.path.expanduser("~/obsidian/GlenVault")))
INBOX_PATH = Path(os.getenv("GNM_INBOX_PATH", os.path.expanduser("~/Dropbox/NoteInbox")))

# Global People folder — one note per person, links to every note that mentions them.
PEOPLE_PATH = VAULT_PATH / "People"

# Google Drive local sync folder where Otter transcripts land.
# Otter.ai exports to Google Drive via native integration,
# Google Drive desktop app syncs to this local path.
OTTER_GDRIVE_PATH = Path(os.getenv(
    "GNM_OTTER_GDRIVE_PATH",
    os.path.expanduser("~/Google Drive/My Drive/Otter")
))

# ── Inbox subfolders ────────────────────────────────────────────────────────
INBOX_INQ = INBOX_PATH / "Inq"
INBOX_OTTER = INBOX_PATH / "Otter"
INBOX_MANUAL = INBOX_PATH / "Manual"
INBOX_PROCESSED = INBOX_PATH / "Processed"
# Drop a file here and the processor auto-opens a GitHub issue for Dan to action.
INBOX_FORDAN = INBOX_PATH / "ForDan"

# ── Known projects ──────────────────────────────────────────────────────────
PROJECTS = ["Calico", "Cobia", "Goldstone", "Personal", "Vistra", "Zelestra"]

# ── Project aliases — map alternate names to canonical project names ─────────
PROJECT_ALIASES = {
    "Goldstone": "Calico",
}

# ── Inbox cleanup ───────────────────────────────────────────────────────────
PROCESSED_RETENTION_DAYS = int(os.getenv("GNM_PROCESSED_RETENTION_DAYS", "30"))

# ── File extensions we process ──────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf", ".md"}

# Audio files must NEVER be sent to the pipeline — transcript TEXT only.
# These are skipped with a clear message if they land in an inbox.
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mov", ".webm"}

# ── Dashboard paths ────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
SEARCH_INDEX_PATH = DATA_DIR / "search_index"
TRACKER_STATE_FILE = DATA_DIR / "trackers.json"
