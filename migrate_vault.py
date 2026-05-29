#!/usr/bin/env python3
"""
migrate_vault.py — Migrate the existing prototype vault from nested → flat structure.

Changes applied:
  1. Move Projects/<P>/AI Analyzed Notes/**/*.md  →  Projects/<P>/<filename>.md (flat)
  2. Delete Projects/<P>/Action Items/ trees (tasks are inline in analyzed notes)
  3. Move Projects/<P>/People/*.md  →  People/<name>.md (global folder, merge tags)
  4. Delete now-empty Notes/, Transcripts/, AI Analyzed Notes/, per-project People/
  5. Delete *.meta.json sidecars that point to removed files
  6. Also apply old frontmatter normalizations (project wiki-link fix, project tag guarantee)

Run once (idempotent — safe to run again):
    python migrate_vault.py
"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

VAULT = config.VAULT_PATH
PROJECTS = set(config.PROJECTS)

_FM_RE = re.compile(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)", re.DOTALL)

# Counters
_stats = {
    "analyzed_moved": 0,
    "action_items_deleted": 0,
    "people_moved": 0,
    "people_merged": 0,
    "raw_deleted": 0,
    "meta_deleted": 0,
    "dirs_removed": 0,
    "frontmatter_fixed": 0,
}


# ── Slug helper ──────────────────────────────────────────────────────────────

def _project_slug(name: str) -> str:
    return re.sub(r"[^\w]+", "-", name.lower()).strip("-")


# ── Frontmatter helpers ──────────────────────────────────────────────────────

def _parse_fm(raw: str):  # -> Optional[tuple[str, str, str, str]]
    """Return (open_fence, fm_text, close_fence, body) or None."""
    m = _FM_RE.match(raw)
    return m.groups() if m else None


def _ensure_project_tag(fm_text: str, proj_name: str) -> tuple[str, bool]:
    """Guarantee the short-form project tag is in the frontmatter tags block."""
    proj_tag = f"#{_project_slug(proj_name)}"
    existing_tags = re.findall(r"-\s*(#\S+)", fm_text)
    if proj_tag in existing_tags:
        return fm_text, False
    if "tags:" not in fm_text:
        return fm_text, False
    new_fm = re.sub(
        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
        lambda mm: mm.group(0).rstrip() + f"\n  - {proj_tag}",
        fm_text,
        count=1,
    )
    return new_fm, True


def _fix_project_wikilink(fm_text: str) -> tuple[str, bool]:
    """Remove [[...]] from project: field."""
    changed = False

    def fix(m):
        nonlocal changed
        changed = True
        return f"project: {m.group(1)}"

    new = re.sub(r'project:\s*["\']?\[\[([^\]]+)\]\]["\']?', fix, fm_text)
    return new, changed


def _get_project_from_fm(fm_text: str):  # -> Optional[str]
    m = re.search(r"^project:\s*(\S+)", fm_text, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip("\"'")


def _upgrade_person_queries(body: str) -> str:
    """Rewrite legacy participant/text `contains(...)` Dataview queries on a person
    page to the robust backlinks idiom (`FROM [[]]`), which lists every note that
    links to this person. Idempotent."""
    # Related Notes: FROM "..." WHERE contains(participants, ...)  ->  FROM [[]]
    body = re.sub(
        r'FROM\s+"[^"]*"\s*\n\s*WHERE contains\(participants,[^\n]*\)',
        "FROM [[]]",
        body,
    )
    # Open Action Items: FROM "..." WHERE contains(text, ...) AND !completed  ->  FROM [[]]\nWHERE !completed
    body = re.sub(
        r'FROM\s+"[^"]*"\s*\n\s*WHERE contains\(text,[^\n]*\)\s*AND\s*!completed',
        "FROM [[]]\nWHERE !completed",
        body,
    )
    return body


def _add_tag_to_person_file(person_file: Path, tag: str) -> bool:
    """Add tag to an existing person file's frontmatter. Returns True if changed."""
    raw = person_file.read_text(encoding="utf-8")
    parts = _parse_fm(raw)
    if not parts:
        return False
    open_fence, fm_text, close_fence, body = parts
    existing_tags = re.findall(r"-\s*(#\S+|\"#\S+\")", fm_text)
    existing_clean = {t.strip('"') for t in existing_tags}
    if tag in existing_clean:
        return False
    if "tags:" not in fm_text:
        return False
    fm_text = re.sub(
        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
        lambda mm: mm.group(0).rstrip() + f'\n  - "{tag}"',
        fm_text,
        count=1,
    )
    person_file.write_text(open_fence + fm_text + close_fence + body, encoding="utf-8")
    return True


# ── Collision-safe move ───────────────────────────────────────────────────────

def _safe_move(src: Path, dest_dir: Path) -> Path:
    """Move src to dest_dir/<src.name>, with numeric suffix on collision."""
    dest = dest_dir / src.name
    if not dest.exists():
        shutil.move(str(src), str(dest))
        return dest
    # Check if it's literally the same file content (re-run safety)
    if dest.read_bytes() == src.read_bytes():
        src.unlink()
        return dest
    # Different file → numeric suffix
    stem, suffix = src.stem, src.suffix
    counter = 2
    while True:
        candidate = dest_dir / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            shutil.move(str(src), str(candidate))
            return candidate
        counter += 1


def _try_rmdir(path: Path):
    """Remove directory if it exists and is empty (recursively prune)."""
    if not path.is_dir():
        return
    for sub in path.iterdir():
        if sub.is_dir():
            _try_rmdir(sub)
        else:
            return  # non-empty, stop
    try:
        path.rmdir()
        _stats["dirs_removed"] += 1
    except OSError:
        pass


# ── Step 1: Flatten AI Analyzed Notes ────────────────────────────────────────

def _flatten_analyzed(proj_dir: Path):
    ai_root = proj_dir / "AI Analyzed Notes"
    if not ai_root.is_dir():
        return

    for md in list(ai_root.rglob("*.md")):
        dest = _safe_move(md, proj_dir)
        print(f"  [flatten] {md.relative_to(proj_dir)}  →  {dest.name}")
        _stats["analyzed_moved"] += 1

    # Delete the now-empty tree
    _try_rmdir(ai_root)


# ── Step 2: Delete Action Items trees ────────────────────────────────────────

def _delete_action_items(proj_dir: Path):
    ai_dir = proj_dir / "Action Items"
    if not ai_dir.is_dir():
        return

    removed = list(ai_dir.rglob("*.md"))
    if removed:
        print(f"  [action-items] Removing {len(removed)} file(s) from {proj_dir.name}/Action Items/")
        print("  WARNING: These tasks should already be inline in the analyzed notes.")
        for f in removed:
            print(f"    REMOVED: {f.relative_to(proj_dir)}")
        _stats["action_items_deleted"] += len(removed)
    shutil.rmtree(str(ai_dir), ignore_errors=True)


# ── Step 3: Move per-project People → global People/ ─────────────────────────

def _migrate_people(proj_dir: Path, global_people: Path, project_name: str):
    local_people = proj_dir / "People"
    if not local_people.is_dir():
        return

    proj_tag = f"#{_project_slug(project_name)}"

    for person_md in list(local_people.glob("*.md")):
        global_dest = global_people / person_md.name

        if global_dest.exists():
            # Merge: add project tag to existing global file
            changed = _add_tag_to_person_file(global_dest, proj_tag)
            if changed:
                print(f"  [people] Merged tag {proj_tag} into {person_md.name}")
                _stats["people_merged"] += 1
            # Also add #people tag if missing
            _add_tag_to_person_file(global_dest, "#people")
            person_md.unlink()
        else:
            # Move and upgrade the file format
            raw = person_md.read_text(encoding="utf-8")
            parts = _parse_fm(raw)
            if parts:
                open_fence, fm_text, close_fence, body = parts
                # Add #people tag
                _add_tag_flag = "#people" not in fm_text
                if _add_tag_flag and "tags:" in fm_text:
                    fm_text = re.sub(
                        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
                        lambda mm: mm.group(0).rstrip() + '\n  - "#people"',
                        fm_text,
                        count=1,
                    )
                # Add project tag
                if proj_tag not in fm_text and "tags:" in fm_text:
                    fm_text = re.sub(
                        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
                        lambda mm: mm.group(0).rstrip() + f'\n  - "{proj_tag}"',
                        fm_text,
                        count=1,
                    )
                # Upgrade Dataview queries to the robust backlinks idiom (FROM [[]])
                body = _upgrade_person_queries(body)
                global_dest.write_text(
                    open_fence + fm_text + close_fence + body,
                    encoding="utf-8",
                )
                person_md.unlink()
            else:
                shutil.move(str(person_md), str(global_dest))

            print(f"  [people] {proj_dir.name}/{person_md.name}  →  People/{person_md.name}")
            _stats["people_moved"] += 1

    _try_rmdir(local_people)


# ── Step 4: Delete empty raw folders ─────────────────────────────────────────

def _delete_raw_folders(proj_dir: Path):
    for folder_name in ("Notes", "Transcripts"):
        raw_dir = proj_dir / folder_name
        if not raw_dir.is_dir():
            continue
        files = list(raw_dir.rglob("*.md"))
        if files:
            print(f"  [raw] Removing {len(files)} file(s) from {proj_dir.name}/{folder_name}/")
            for f in files:
                f.unlink()
                _stats["raw_deleted"] += 1
        shutil.rmtree(str(raw_dir), ignore_errors=True)
        _stats["dirs_removed"] += 1


# ── Step 5: Delete stale .meta.json sidecars ─────────────────────────────────

def _delete_stale_meta(proj_dir: Path):
    # .meta.json sidecars are vestigial in the flat layout (delete_note unlinks the
    # note directly). Remove them all — they're exactly the clutter fix 6 targets.
    for meta in list(proj_dir.rglob("*.meta.json")):
        meta.unlink()
        print(f"  [meta] Removed vestigial sidecar: {meta.relative_to(VAULT)}")
        _stats["meta_deleted"] += 1


# ── Step 6: Frontmatter normalization on flat notes ───────────────────────────

def _normalize_frontmatter(proj_dir: Path, project_name: str):
    for md in proj_dir.glob("*.md"):
        try:
            raw = md.read_text(encoding="utf-8")
        except OSError:
            continue
        parts = _parse_fm(raw)
        if not parts:
            continue
        open_fence, fm_text, close_fence, body = parts
        changed = False

        # Fix project wikilink
        fm_text, c = _fix_project_wikilink(fm_text)
        changed = changed or c

        # Detect project from frontmatter (may differ from folder name for old files)
        proj = _get_project_from_fm(fm_text) or project_name
        if proj in PROJECTS:
            fm_text, c = _ensure_project_tag(fm_text, proj)
            changed = changed or c

        # Remove body [[ProjectName]] wiki-links (cleanup old format)
        new_body = body
        for pname in PROJECTS:
            pattern = f"[[{pname}]]"
            if pattern in new_body:
                new_body = new_body.replace(pattern, pname)
                changed = True

        if changed:
            md.write_text(open_fence + fm_text + close_fence + new_body, encoding="utf-8")
            _stats["frontmatter_fixed"] += 1


# ── Main ─────────────────────────────────────────────────────────────────────

def _run_all():
    """Run the full migration over the vault (assumes VAULT exists)."""
    print(f"Migrating vault: {VAULT}")
    print(f"Known projects: {', '.join(sorted(PROJECTS))}")
    print()

    global_people = VAULT / "People"
    global_people.mkdir(parents=True, exist_ok=True)

    projects_dir = VAULT / "Projects"
    if not projects_dir.is_dir():
        print("No Projects/ directory found — nothing to migrate.")
        return

    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or proj_dir.name.startswith("."):
            continue
        project_name = proj_dir.name
        print(f"\n-- Project: {project_name} --")

        _flatten_analyzed(proj_dir)
        _delete_action_items(proj_dir)
        _migrate_people(proj_dir, global_people, project_name)
        _delete_raw_folders(proj_dir)
        # Prune legacy empty "Weekly Reports/" trees (new reports go to "_Weekly Reports/")
        _try_rmdir(proj_dir / "Weekly Reports")
        _delete_stale_meta(proj_dir)
        _normalize_frontmatter(proj_dir, project_name)

    # Normalize Dataview queries on ALL global People files (catches already-migrated ones).
    for person_md in global_people.glob("*.md"):
        raw = person_md.read_text(encoding="utf-8")
        upgraded = _upgrade_person_queries(raw)
        if upgraded != raw:
            person_md.write_text(upgraded, encoding="utf-8")
            print(f"  [people] Upgraded Dataview queries: People/{person_md.name}")

    print()
    print("=" * 60)
    print(f"  Migration complete.")
    print(f"  Analyzed notes flattened: {_stats['analyzed_moved']}")
    print(f"  Action item files deleted: {_stats['action_items_deleted']}")
    print(f"  People moved to global:   {_stats['people_moved']}")
    print(f"  People tags merged:       {_stats['people_merged']}")
    print(f"  Raw notes deleted:        {_stats['raw_deleted']}")
    print(f"  Meta sidecars cleaned:    {_stats['meta_deleted']}")
    print(f"  Directories removed:      {_stats['dirs_removed']}")
    print(f"  Frontmatter normalized:   {_stats['frontmatter_fixed']}")
    print("=" * 60)


# ── One-time auto-migration (safe to call on every server startup) ────────────

_LEGACY_SUBDIRS = {"AI Analyzed Notes", "Action Items", "Transcripts", "Notes", "People", "Weekly Reports"}
_MARKER_NAME = ".gnm_migrated"


def _needs_migration() -> bool:
    """True if the vault still has old nested folders or stale .meta.json sidecars."""
    projects_dir = VAULT / "Projects"
    if not projects_dir.is_dir():
        return False
    for proj in projects_dir.iterdir():
        if not proj.is_dir() or proj.name.startswith("."):
            continue
        for sub in proj.iterdir():
            if sub.is_dir() and sub.name in _LEGACY_SUBDIRS:
                return True
    return any(projects_dir.rglob("*.meta.json"))


def auto_migrate_once() -> dict:
    """Idempotent first-launch cleanup: back up the vault, flatten it, drop a marker
    so it never runs again. Safe to call on every startup — returns immediately if
    already migrated, the vault is missing, or it's already in the new flat layout.
    Glen never touches a terminal; a timestamped backup is always kept on success.
    """
    from datetime import datetime

    if not VAULT.exists():
        return {"ran": False, "reason": "vault not found"}

    marker = VAULT / _MARKER_NAME
    if marker.exists():
        return {"ran": False, "reason": "already migrated"}

    if not _needs_migration():
        marker.write_text(
            f"No migration needed (already flat). {datetime.now().isoformat(timespec='seconds')}\n",
            encoding="utf-8",
        )
        return {"ran": False, "reason": "nothing to migrate"}

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = VAULT.parent / f"{VAULT.name}_backup_{ts}"
    print(f"[migrate] First launch with legacy layout detected. Backing up vault -> {backup}")
    try:
        shutil.copytree(VAULT, backup)
    except Exception as e:
        # Never migrate without a safety copy.
        print(f"[migrate] Backup FAILED ({e}); skipping auto-migration to protect the vault.")
        return {"ran": False, "reason": f"backup failed: {e}"}

    print("[migrate] Running one-time vault cleanup (flatten + global People)...")
    try:
        _run_all()
    except Exception as e:
        print(f"[migrate] Migration error: {e}. Original vault is safe at {backup}")
        return {"ran": False, "reason": f"migration error: {e}", "backup": str(backup)}

    marker.write_text(
        f"Migrated {datetime.now().isoformat(timespec='seconds')}. Backup: {backup}\n",
        encoding="utf-8",
    )
    print(f"[migrate] Cleanup complete. Rollback copy retained at {backup}")
    return {"ran": True, "backup": str(backup)}


def main():
    if not VAULT.exists():
        print(f"Vault not found at {VAULT}")
        print("Set GNM_VAULT_PATH in .env or check config.py")
        sys.exit(1)
    _run_all()


if __name__ == "__main__":
    main()
