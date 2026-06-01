#!/usr/bin/env python3
"""
GNM Runner - Transcript processing agent.

Modes:
    python run.py              Scan inboxes once, process all found files
    python run.py --watch      Poll continuously (every 60s)
    python run.py <file>       Process a single local file
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import config
from processor import process_file


def cleanup_processed(dry_run: bool = False) -> int:
    """Delete files from Inbox/Processed/ older than PROCESSED_RETENTION_DAYS. Returns count removed."""
    folder = config.INBOX_PROCESSED
    if not folder.exists():
        return 0
    cutoff = datetime.now().timestamp() - config.PROCESSED_RETENTION_DAYS * 86400
    removed = 0
    for f in folder.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff:
            if not dry_run:
                f.unlink()
            removed += 1
    return removed


def scan_folder(folder: Path, source_type: str) -> list[tuple[Path, str]]:
    """Find all processable files in a folder.

    Audio files are detected and logged with a clear warning but never returned
    as processable - they must be exported from Otter as TEXT first.
    """
    if not folder.exists():
        return []

    # Warn about any audio/video files that are NOT processable
    for ext in config.AUDIO_EXTENSIONS:
        for audio_file in folder.glob(f"*{ext}"):
            print(
                f"  SKIP (audio, not a transcript): {audio_file.name}"
                f" - export the TEXT transcript from Otter instead"
            )

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


def process_fordan_files() -> int:
    """Drop-folder intake: any file in Inbox/ForDan becomes a GitHub issue for Dan.

    Reads the file, opens an issue with its contents, then archives it to
    Inbox/Processed so it isn't re-filed. Returns the count of issues opened.
    """
    folder = config.INBOX_FORDAN
    if not folder.exists():
        return 0

    files = []
    for ext in config.SUPPORTED_EXTENSIONS:
        files.extend(folder.glob(f"*{ext}"))
    if not files:
        return 0

    try:
        from api.services import github_service
    except ImportError:
        print("  ForDan: github_service unavailable (API not installed) — skipping")
        return 0

    from processor import mark_processed, read_transcript, ScannedPDFError

    fail_dir = folder / "_failed"
    opened = 0
    for f in sorted(files):
        # Per-file try/except: a single bad file (read error, locked file,
        # GitHub outage) must never propagate out and kill the watch loop, whose
        # only handler is KeyboardInterrupt.
        try:
            try:
                content = read_transcript(f)
            except (ScannedPDFError, ValueError) as e:
                print(f"  ForDan SKIP {f.name}: {e}")
                continue

            ts = time.strftime("%Y-%m-%d %H:%M")
            body = (
                f"Glen dropped a file into the ForDan inbox folder on {ts}.\n\n"
                f"**File:** `{f.name}`\n\n"
                "## Contents\n\n"
                f"{content[:8000]}"
                + ("\n\n_(truncated)_" if len(content) > 8000 else "")
            )
            result = github_service.create_issue(
                title=f"From Glen: {f.name}",
                body=body,
                labels=["from-chat"],
            )
            if result.get("ok"):
                print(f"  ForDan: filed issue for {f.name} -> {result.get('url')}")
                mark_processed(f)
                opened += 1
            else:
                # Move aside instead of leaving it in ForDan — otherwise every
                # 60s cycle re-files it (spamming duplicate issues if the issue
                # actually got created before a timeout). Dan can inspect _failed.
                print(f"  ForDan ERROR filing {f.name}: {result.get('error')} — moving to _failed")
                fail_dir.mkdir(exist_ok=True)
                dest = fail_dir / f.name
                counter = 2
                while dest.exists():
                    dest = fail_dir / f"{f.stem}-{counter}{f.suffix}"
                    counter += 1
                f.replace(dest)
        except Exception as e:
            print(f"  ForDan ERROR handling {f.name}: {e} — left in place")

    return opened



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
    """Process a list of files. Returns (processed, errors).

    Instruments per-file timing and prints a cycle total.
    Audio files are double-checked here and skipped if they somehow arrive.
    """
    processed = 0
    errors = 0
    cycle_start = time.perf_counter()

    for file_path, source_type in pending:
        # Defensive audio guard - blocks .mp3 etc. even if passed directly
        if file_path.suffix.lower() in config.AUDIO_EXTENSIONS:
            print(
                f"  SKIP (audio guard): {file_path.name}"
                f" - audio files must never enter the pipeline"
            )
            continue

        t0 = time.perf_counter()
        ts = time.strftime("%H:%M:%S")
        try:
            result = process_file(file_path, source_type)
            elapsed = time.perf_counter() - t0
            if result:
                processed += 1
                print(f"  [{ts}] Processed {file_path.name} in {elapsed:.1f}s")
            else:
                print(f"  [{ts}] Skipped {file_path.name} (no result) in {elapsed:.1f}s")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  [{ts}] ERROR processing {file_path.name} in {elapsed:.1f}s: {e}")
            errors += 1

    cycle_elapsed = time.perf_counter() - cycle_start
    if pending:
        print(f"  Cycle: {processed} processed, {errors} errors in {cycle_elapsed:.1f}s")

    return processed, errors


def run_once():
    """Scan all inboxes and process everything found (uncapped - explicit run)."""
    print_status()

    process_fordan_files()

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

    removed = cleanup_processed()
    if removed:
        print(f"  Cleaned up {removed} file(s) from Processed/ (>{config.PROCESSED_RETENTION_DAYS}d old)")

    print()
    print("=" * 60)
    print(f"  Done. Processed: {processed}  Errors: {errors}")
    print("=" * 60)


def run_watch():
    """Poll Otter + inboxes every 60 seconds. Ctrl+C to stop.

    Caps files processed per cycle to config.OTTER_MAX_PER_CYCLE so a large
    backlog never stalls the pipeline for 45+ minutes in one shot. Leftovers
    are picked up on the next poll iteration.
    """
    print_status()
    print("  Mode: WATCH (polling every 60s)")
    print(f"  Throttle:     max {config.OTTER_MAX_PER_CYCLE} files per cycle (OTTER_MAX_PER_CYCLE)")
    print("  Press Ctrl+C to stop")
    print("=" * 60)

    total_processed = 0
    total_errors = 0

    try:
        while True:
            process_fordan_files()

            seen = set()
            pending = []
            for f, src in scan_all_inboxes():
                if f.name not in seen:
                    seen.add(f.name)
                    pending.append((f, src))

            if pending:
                ts = time.strftime("%H:%M:%S")
                total_found = len(pending)

                # Cap per cycle to prevent long stalls
                if total_found > config.OTTER_MAX_PER_CYCLE:
                    print(
                        f"\n[{ts}] Found {total_found} file(s);"
                        f" processing first {config.OTTER_MAX_PER_CYCLE} this cycle"
                        f" (throttle={config.OTTER_MAX_PER_CYCLE},"
                        f" {total_found - config.OTTER_MAX_PER_CYCLE} deferred to next cycle)"
                    )
                    pending = pending[:config.OTTER_MAX_PER_CYCLE]
                else:
                    print(f"\n[{ts}] Found {total_found} new file(s)")

                for f, src in pending:
                    print(f"  [{src}] {f.name}")

                p, e = process_pending(pending)
                total_processed += p
                total_errors += e
                removed = cleanup_processed()
                if removed:
                    print(f"[{ts}] Cleaned up {removed} file(s) from Processed/ (>{config.PROCESSED_RETENTION_DAYS}d old)")
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

    # Audio guard - block explicitly even when called directly via CLI
    if path.suffix.lower() in config.AUDIO_EXTENSIONS:
        print(
            f"  SKIP (audio, not a transcript): {path.name}"
            f" - export the TEXT transcript from Otter instead"
        )
        sys.exit(0)

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
