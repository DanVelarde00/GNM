#!/usr/bin/env python3
"""
GNM Runner — Transcript processing agent.

Modes:
    python run.py              Scan inboxes once, process all found files
    python run.py --watch      Poll continuously (every 60s)
    python run.py <file>       Process a single local file
"""

import sys
import time
from pathlib import Path

import config
from processor import process_file


def scan_folder(folder: Path, source_type: str) -> list[tuple[Path, str]]:
    """Find all processable files in a folder."""
    if not folder.exists():
        return []
    files = []
    for ext in config.SUPPORTED_EXTENSIONS:
        files.extend(folder.glob(f"*{ext}"))
    return [(f, source_type) for f in sorted(files)]


def scan_all_inboxes() -> list[tuple[Path, str]]:
    """Scan all local watched folders for new files."""
    pending = []
    pending.extend(scan_folder(config.INBOX_OTTER, "otter"))
    pending.extend(scan_folder(config.INBOX_INQ, "inq"))
    pending.extend(scan_folder(config.INBOX_MANUAL, "manual"))
    return pending



def print_status():
    """Print current configuration."""
    print("=" * 60)
    print("  GNM Agent")
    print("=" * 60)
    print(f"  Vault:        {config.VAULT_PATH}")
    print(f"  Inbox:        {config.INBOX_PATH}")
    print(f"  Otter MCP:    {'enabled' if config.OTTER_MCP_URL else 'disabled (set OTTER_MCP_URL + OTTER_MCP_TOKEN)'}")
    print(f"  Projects:     {', '.join(config.PROJECTS)}")

    folders = [
        ("Inbox/Otter", config.INBOX_OTTER),
        ("Inbox/Inq", config.INBOX_INQ),
        ("Inbox/Manual", config.INBOX_MANUAL),
    ]
    print()
    for name, path in folders:
        exists = "OK" if path.exists() else "NOT FOUND"
        print(f"  [{exists}] {name}: {path}")
    print()


def process_pending(pending: list[tuple[Path, str]]) -> tuple[int, int]:
    """Process a list of files. Returns (processed, errors)."""
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
    return processed, errors


def run_once():
    """Scan all inboxes and process everything found."""
    print_status()

    pending = []
    seen = set()
    for f, src in scan_all_inboxes():
        if f.name not in seen:
            seen.add(f.name)
            pending.append((f, src))

    if not pending:
        print("No new files found.")
        return

    print(f"\nFound {len(pending)} file(s) to process:")
    for f, src in pending:
        print(f"  [{src}] {f.name}")

    processed, errors = process_pending(pending)

    print()
    print("=" * 60)
    print(f"  Done. Processed: {processed}  Errors: {errors}")
    print("=" * 60)


def run_watch():
    """Poll Otter + inboxes every 60 seconds. Ctrl+C to stop."""
    print_status()
    print("  Mode: WATCH (polling every 60s)")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    total_processed = 0
    total_errors = 0

    try:
        while True:
            seen = set()
            pending = []
            for f, src in scan_all_inboxes():
                if f.name not in seen:
                    seen.add(f.name)
                    pending.append((f, src))

            if pending:
                ts = time.strftime("%H:%M:%S")
                print(f"\n[{ts}] Found {len(pending)} new file(s)")
                for f, src in pending:
                    print(f"  [{src}] {f.name}")

                p, e = process_pending(pending)
                total_processed += p
                total_errors += e
                print(f"[{ts}] Session total: {total_processed} processed, {total_errors} errors")

            time.sleep(60)
    except KeyboardInterrupt:
        print(f"\nWatcher stopped. Total: {total_processed} processed, {total_errors} errors")


def run_single(file_path_str: str):
    """Process one file."""
    path = Path(file_path_str)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

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
        print("ERROR: ANTHROPIC_API_KEY not set.")
        print(f"Add your key to: {Path(config.__file__).parent / '.env'}")
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
