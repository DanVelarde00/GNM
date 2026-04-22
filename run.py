#!/usr/bin/env python3
"""
GNM Runner — On-demand transcript processing.

Scans all inbox folders (Inq, Otter, Manual) and the Google Drive Otter sync
folder for new files, processes each through Claude, and routes output to the vault.

Usage:
    python run.py              # Process all inbox folders
    python run.py --watch      # Watch mode (persistent, for future use)
    python run.py <file>       # Process a single file
"""

import sys
import time
from pathlib import Path

import config
from processor import process_file


def scan_folder(folder: Path, source_type: str) -> list[Path]:
    if not folder.exists():
        return []
    files = []
    for ext in config.SUPPORTED_EXTENSIONS:
        files.extend(folder.glob(f"*{ext}"))
    return [(f, source_type) for f in sorted(files)]


def scan_all_inboxes() -> list[tuple[Path, str]]:
    pending = []
    pending.extend(scan_folder(config.OTTER_GDRIVE_PATH, "otter"))
    pending.extend(scan_folder(config.INBOX_OTTER, "otter"))
    pending.extend(scan_folder(config.INBOX_INQ, "inq"))
    pending.extend(scan_folder(config.INBOX_MANUAL, "manual"))
    return pending


def run_once():
    print("=" * 60)
    print("  GNM — Scanning for new transcripts")
    print("=" * 60)
    print(f"  Vault:       {config.VAULT_PATH}")
    print(f"  Otter GDrive: {config.OTTER_GDRIVE_PATH}")
    print(f"  Inbox:       {config.INBOX_PATH}")
    print()

    pending = scan_all_inboxes()

    if not pending:
        print("No new files found.")
        return

    print(f"Found {len(pending)} file(s) to process:\n")
    for f, src in pending:
        print(f"  [{src}] {f.name}")
    print()

    processed = 0
    errors = 0
    for file_path, source_type in pending:
        try:
            result = process_file(file_path, source_type)
            if result:
                processed += 1
        except Exception as e:
            print(f"  ERROR processing {file_path.name}: {e}")
            errors += 1

    print()
    print("=" * 60)
    print(f"  Done. Processed: {processed}  Errors: {errors}")
    print("=" * 60)


def run_watch():
    """Persistent watch mode — polls every 30 seconds."""
    print("GNM Watcher — monitoring for new files (Ctrl+C to stop)")
    print(f"  Polling interval: 30s\n")
    try:
        while True:
            pending = scan_all_inboxes()
            if pending:
                print(f"\n[{time.strftime('%H:%M:%S')}] Found {len(pending)} new file(s)")
                for file_path, source_type in pending:
                    try:
                        process_file(file_path, source_type)
                    except Exception as e:
                        print(f"  ERROR: {file_path.name}: {e}")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


def run_single(file_path_str: str):
    path = Path(file_path_str)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    # Guess source type from parent folder name
    parent = path.parent.name.lower()
    if "otter" in parent:
        source_type = "otter"
    elif "inq" in parent:
        source_type = "inq"
    else:
        source_type = "manual"

    process_file(path, source_type)


def main():
    if not config.ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--watch":
            run_watch()
        else:
            run_single(arg)
    else:
        run_once()


if __name__ == "__main__":
    main()
