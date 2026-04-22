"""
GNM Dashboard — Single entry point.
Usage:
  python server.py          # Production: FastAPI on :8000
  python server.py --dev    # Dev: FastAPI on :8000 + Next.js on :3000
"""

import subprocess
import sys
import atexit
from pathlib import Path

import uvicorn

DASHBOARD_DIR = Path(__file__).parent / "dashboard"
DEV_MODE = "--dev" in sys.argv

_next_proc = None


def _start_next_dev():
    global _next_proc
    if not DASHBOARD_DIR.is_dir():
        print("[GNM] Warning: dashboard/ not found, skipping Next.js dev server")
        return
    _next_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(DASHBOARD_DIR),
        shell=(sys.platform == "win32"),
    )
    print("[GNM] Next.js dev server starting on http://localhost:3000")


def _stop_next_dev():
    if _next_proc:
        _next_proc.terminate()


atexit.register(_stop_next_dev)


if __name__ == "__main__":
    print("=" * 50)
    print("  GNM Dashboard")
    print(f"  Mode: {'Development' if DEV_MODE else 'Production'}")
    print(f"  API:  http://localhost:8000")
    if DEV_MODE:
        print(f"  UI:   http://localhost:3000")
    print("=" * 50)

    if DEV_MODE:
        _start_next_dev()

    uvicorn.run(
        "api:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=DEV_MODE,
    )
