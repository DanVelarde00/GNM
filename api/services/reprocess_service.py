"""
Reprocess / repair service for the assistant.

Lets the AI chat (and the dashboard) fix individual notes without touching the
whole vault:
  - scan_missing_fields: find notes missing a frontmatter field (e.g. participants)
  - reprocess_note: re-run the LLM pipeline on a note's original source file
  - move_note: relocate a misrouted note to the correct project + fix frontmatter

All paths in/out are vault-relative (the same form vault_service uses).
"""

import re
from pathlib import Path

import config
from api.services import vault_service


# ── Scan for notes missing a field ────────────────────────────────────────────

def _is_empty(value) -> bool:
    """A frontmatter field counts as missing if absent, None, empty, or all-empty."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple)):
        return len([v for v in value if v is not None and str(v).strip()]) == 0
    return False


def _has_tags_in_raw(raw: str) -> bool:
    """True if the note's frontmatter has at least one tag.

    Tags are written unquoted ('- #calico'), and yaml.safe_load reads '#...' as a
    comment — so EVERY note's tags parse to [None, None]. Trusting the parsed
    value would make scan_missing_fields('tags') either report nothing (old bug)
    or report every note (naive None-filter). Detect tags from the raw frontmatter
    text instead.
    """
    fm_match = re.match(r"^---\s*\n(.*?)\n---", raw, re.DOTALL)
    if not fm_match:
        return False
    in_tags = False
    for line in fm_match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("tags:"):
            inline = stripped[len("tags:"):].strip()  # inline form: tags: [a, b]
            if inline.startswith("[") and inline.strip("[] ").strip():
                return True
            in_tags = True
            continue
        if in_tags:
            if line[:1].isspace() and stripped.startswith("-"):
                if stripped.lstrip("- ").strip():
                    return True
            elif stripped:  # a new top-level key — left the tags block
                in_tags = False
    return False


def _field_missing(field: str, meta: dict, raw: str) -> bool:
    if field == "tags":
        return not _has_tags_in_raw(raw)
    return _is_empty(meta.get(field))


def scan_missing_fields(field: str = "participants") -> list[dict]:
    """Return top-level project notes whose `field` is missing or empty."""
    projects_dir = config.VAULT_PATH / "Projects"
    if not projects_dir.is_dir():
        return []

    hits = []
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or proj_dir.name.startswith("."):
            continue
        for md in sorted(proj_dir.glob("*.md")):
            raw = md.read_text(encoding="utf-8")
            meta, _ = vault_service.parse_frontmatter(raw)
            if _field_missing(field, meta, raw):
                hits.append({
                    "path": str(md.relative_to(config.VAULT_PATH)).replace("\\", "/"),
                    "project": proj_dir.name,
                    "date": meta.get("date", ""),
                    "source_file": meta.get("source_file", ""),
                })
    return hits


# ── Locate the original source file ────────────────────────────────────────────

def _find_source(source_file: str) -> Path | None:
    """Find a note's original source in Inbox/Processed.

    mark_processed() may have appended a timestamp on collision
    ({stem}_{ts}{suffix}), so glob on the stem rather than matching exactly.
    """
    if not source_file:
        return None
    processed = config.INBOX_PROCESSED
    if not processed.is_dir():
        return None

    exact = processed / source_file
    if exact.exists():
        return exact

    stem = Path(source_file).stem
    suffix = Path(source_file).suffix
    candidates = sorted(processed.glob(f"{stem}*{suffix}"))
    return candidates[0] if candidates else None


# ── Reprocess a single note ────────────────────────────────────────────────────

def reprocess_note(note_rel_path: str) -> dict:
    """Re-run the LLM pipeline on a note's original source and overwrite the note.

    Returns {ok, old_path, new_path, project, moved} or {ok: False, error}.
    The source is left in Processed (move_when_done=False). If reprocessing
    routes the note to a different filename/project, the old note is removed.
    """
    import processor

    try:
        note = vault_service.get_file(note_rel_path)
    except FileNotFoundError:
        return {"ok": False, "error": f"Note not found: {note_rel_path}"}

    source_file = note.frontmatter.get("source_file", "")
    source_type = note.frontmatter.get("source", "manual")
    src = _find_source(source_file)
    if src is None:
        return {
            "ok": False,
            "error": (
                f"Original source '{source_file}' not found in Inbox/Processed — "
                "cannot reprocess (only the AI summary remains)."
            ),
        }

    old_abs = (config.VAULT_PATH / note_rel_path).resolve()
    try:
        result = processor.process_file(src, source_type, move_when_done=False)
    except Exception as e:
        return {"ok": False, "error": f"Reprocessing failed for {src.name}: {e}"}
    if not result:
        return {"ok": False, "error": f"Reprocessing produced no result for {src.name}"}

    new_abs = Path(result["analyzed_path"]).resolve()
    moved = new_abs != old_abs
    if moved and old_abs.exists():
        if new_abs.parent == old_abs.parent:
            # Same project folder, different filename: the source stem only
            # changed because mark_processed appended a collision timestamp
            # ('foo.txt' -> 'foo_20260601120000.txt'). That's a spurious rename,
            # not a re-route — keep the original filename so every [[wiki-link]]
            # and People/ backlink to it survives. (A different parent folder is
            # a genuine project move, so let that one stand.)
            old_abs.write_text(new_abs.read_text(encoding="utf-8"), encoding="utf-8")
            new_abs.unlink()
            new_abs = old_abs
            moved = False
        else:
            old_abs.unlink()

    new_rel = str(new_abs.relative_to(config.VAULT_PATH.resolve())).replace("\\", "/")
    return {
        "ok": True,
        "old_path": note_rel_path,
        "new_path": new_rel,
        "project": result["project"],
        "moved": moved,
    }


# ── Move a misrouted note ──────────────────────────────────────────────────────

def move_note(note_rel_path: str, target_project: str) -> dict:
    """Move a note to Projects/<target_project>/ and fix its project label + tag.

    Pure file move — does NOT re-run the LLM. Use this to correct a misrouted note
    when the summary itself is fine. Returns {ok, old_path, new_path} or {ok: False}.

    Frontmatter is edited as text (regex), NOT round-tripped through YAML: these
    notes write tags unquoted (`- #calico`), which yaml.safe_load reads as comments
    (null), so a yaml.dump round-trip would destroy the tag list.
    """
    import processor

    src_abs = config.VAULT_PATH / note_rel_path
    if not src_abs.exists() or not src_abs.is_file():
        return {"ok": False, "error": f"Note not found: {note_rel_path}"}

    target_dir = config.VAULT_PATH / "Projects" / target_project
    dest_abs = target_dir / src_abs.name
    if dest_abs.resolve() == src_abs.resolve():
        return {"ok": False, "error": f"Note is already in {target_project}"}

    # Collision: a DIFFERENT note with the same filename already lives in the
    # target project. Never overwrite it — disambiguate with a numeric suffix
    # (mirrors route_to_vault's collision handling) so we don't silently destroy
    # an unrelated note.
    if dest_abs.exists():
        stem, suffix = src_abs.stem, src_abs.suffix
        counter = 2
        while dest_abs.exists():
            dest_abs = target_dir / f"{stem}-{counter}{suffix}"
            counter += 1

    raw = src_abs.read_text(encoding="utf-8")
    fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)$", raw, re.DOTALL)
    if not fm_match:
        return {"ok": False, "error": f"Note has no frontmatter: {note_rel_path}"}
    open_fence, fm_text, close_fence, body = fm_match.groups()

    proj_match = re.search(r"^project:\s*(.+)$", fm_text, re.MULTILINE)
    old_project = proj_match.group(1).strip() if proj_match else ""
    new_tag = f"#{processor._project_slug(target_project)}"
    old_tag = f"#{processor._project_slug(old_project)}" if old_project else None

    # 1. project: line
    if proj_match:
        fm_text = fm_text[:proj_match.start()] + f"project: {target_project}" + fm_text[proj_match.end():]

    # 2. swap the project tag list item; insert under tags: if not present
    swapped = 0
    if old_tag and old_tag != new_tag:
        fm_text, swapped = re.subn(
            rf"^(\s*-\s*){re.escape(old_tag)}\s*$",
            rf"\g<1>{new_tag}",
            fm_text,
            count=1,
            flags=re.MULTILINE,
        )
    if swapped == 0 and not re.search(rf"^\s*-\s*{re.escape(new_tag)}\s*$", fm_text, re.MULTILINE):
        fm_text = re.sub(r"^(tags:[ \t]*)$", rf"\1\n  - {new_tag}", fm_text, count=1, flags=re.MULTILINE)

    # 3. body "**Project:** X" line, if present
    body = re.sub(r"^\*\*Project:\*\*\s*.+$", f"**Project:** {target_project}  ", body, count=1, flags=re.MULTILINE)

    target_dir.mkdir(parents=True, exist_ok=True)
    dest_abs.write_text(open_fence + fm_text + close_fence + body, encoding="utf-8")
    src_abs.unlink()

    new_rel = str(dest_abs.relative_to(config.VAULT_PATH)).replace("\\", "/")
    return {"ok": True, "old_path": note_rel_path, "new_path": new_rel, "moved_from": old_project}
