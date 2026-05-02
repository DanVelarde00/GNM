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
CLAUDE_MODEL = "claude-sonnet-4-6"

# ── Otter MCP ────────────────────────────────────────────────────────────────
OTTER_MCP_URL = os.getenv("OTTER_MCP_URL", "")
OTTER_MCP_TOKEN = os.getenv("OTTER_MCP_TOKEN", "")
OTTER_POLL_INTERVAL = int(os.getenv("OTTER_POLL_INTERVAL", "21600"))  # seconds

# ── Paths ───────────────────────────────────────────────────────────────────
# These are defaults for the prototype (Dan's machine).
# Glen's paths will differ — setup_vault.py handles his initial config.

VAULT_PATH = Path(os.getenv("GNM_VAULT_PATH", os.path.expanduser("~/obsidian/GlenVault")))
INBOX_PATH = Path(os.getenv("GNM_INBOX_PATH", os.path.expanduser("~/Dropbox/NoteInbox")))

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

# ── Known projects ──────────────────────────────────────────────────────────
PROJECTS = ["Calico", "Cobia", "Personal", "Vistra", "Zelestra"]

# ── File extensions we process ──────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".txt", ".docx", ".pdf", ".md"}

# ── Dashboard paths ────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"
SEARCH_INDEX_PATH = DATA_DIR / "search_index"
TRACKER_STATE_FILE = DATA_DIR / "trackers.json"
