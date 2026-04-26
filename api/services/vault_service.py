"""
Filesystem operations on the GlenVault Obsidian vault.
All paths are relative to config.VAULT_PATH.
"""

import json
import re
from pathlib import Path

import yaml

import config
from api.models.file_models import FileNode, VaultFile, ProjectInfo


def _vault_path() -> Path:
    return config.VAULT_PATH


def _relative(path: Path) -> str:
    return str(path.relative_to(_vault_path())).replace("\\", "/")


# ── Frontmatter parsing ───────────────────────────────────────────────────

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = _FM_RE.match(content)
    if not m:
        return {}, content
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, m.group(2)


def serialize_frontmatter(meta: dict, body: str) -> str:
    fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return f"---\n{fm}---\n{body}"


# ── Tree building ─────────────────────────────────────────────────────────

def _build_tree(directory: Path, depth: int = 0, max_depth: int = 8) -> list[FileNode]:
    if depth > max_depth or not directory.is_dir():
        return []
    nodes = []
    try:
        entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        if entry.is_dir():
            children = _build_tree(entry, depth + 1, max_depth)
            nodes.append(FileNode(
                name=entry.name,
                path=_relative(entry),
                is_dir=True,
                children=children,
            ))
        elif entry.suffix.lower() == ".md":
            nodes.append(FileNode(
                name=entry.name,
                path=_relative(entry),
            ))
    return nodes


def get_tree() -> list[FileNode]:
    vault = _vault_path()
    return _build_tree(vault)


# ── File read / write ─────────────────────────────────────────────────────

def get_file(vault_relative_path: str) -> VaultFile:
    fp = _vault_path() / vault_relative_path
    if not fp.exists() or not fp.is_file():
        raise FileNotFoundError(f"Not found: {vault_relative_path}")
    raw = fp.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    return VaultFile(path=vault_relative_path, frontmatter=meta, body=body, raw=raw)


def save_file(vault_relative_path: str, content: str) -> None:
    fp = _vault_path() / vault_relative_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")


# ── Projects ──────────────────────────────────────────────────────────────

def list_projects() -> list[ProjectInfo]:
    projects_dir = _vault_path() / "Projects"
    if not projects_dir.is_dir():
        return []
    result = []
    for d in sorted(projects_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        people_dir = d / "People"
        people_count = len(list(people_dir.glob("*.md"))) if people_dir.is_dir() else 0
        result.append(ProjectInfo(
            name=d.name,
            path=_relative(d),
            has_notes=any((d / "Notes").glob("*.md")) if (d / "Notes").is_dir() else False,
            has_transcripts=any((d / "Transcripts").glob("*.md")) if (d / "Transcripts").is_dir() else False,
            has_analyzed=(d / "AI Analyzed Notes").is_dir() and any((d / "AI Analyzed Notes").rglob("*.md")),
            has_action_items=(d / "Action Items").is_dir() and any((d / "Action Items").rglob("*.md")),
            people_count=people_count,
        ))
    return result


# ── Action items scanning ─────────────────────────────────────────────────

_TASK_RE = re.compile(r"^- \[([ xX])\] (.+)$", re.MULTILINE)


def scan_action_items(
    project: str | None = None,
    person: str | None = None,
    completed: bool | None = None,
) -> list[dict]:
    projects_dir = _vault_path() / "Projects"
    items = []

    dirs = []
    if project:
        p = projects_dir / project / "Action Items"
        if p.is_dir():
            dirs.append((project, p))
    else:
        for d in projects_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                ai = d / "Action Items"
                if ai.is_dir():
                    dirs.append((d.name, ai))

    for proj_name, ai_dir in dirs:
        for md in ai_dir.rglob("*.md"):
            content = md.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(content)
            for idx, m in enumerate(_TASK_RE.finditer(body)):
                is_done = m.group(1).lower() == "x"
                task_text = m.group(2)

                # Extract owner from "task — [[Owner]]" pattern
                owner_match = re.search(r"—\s*\[\[([^\]]+)\]\]", task_text)
                owner = owner_match.group(1) if owner_match else None

                # Extract due from "(due: YYYY-MM-DD)" pattern
                due_match = re.search(r"\(due:\s*(\d{4}-\d{2}-\d{2})\)", task_text)
                due = due_match.group(1) if due_match else None

                # Clean task text (remove owner and due annotations)
                clean = re.sub(r"\s*—\s*\[\[[^\]]+\]\]", "", task_text)
                clean = re.sub(r"\s*\(due:\s*\d{4}-\d{2}-\d{2}\)", "", clean).strip()

                if completed is not None and is_done != completed:
                    continue
                if person and (not owner or person.lower() not in owner.lower()):
                    continue

                items.append({
                    "task": clean,
                    "owner": owner,
                    "due": due,
                    "completed": is_done,
                    "project": proj_name,
                    "file_path": _relative(md),
                    "task_index": idx,
                    "date": meta.get("date", ""),
                    "source_note": meta.get("source_note", ""),
                })

    return items


def delete_note(vault_relative_path: str) -> dict:
    """Delete an analyzed note and all derived files listed in its .meta.json sidecar."""
    fp = _vault_path() / vault_relative_path
    meta_path = fp.with_suffix(".meta.json")
    deleted = []

    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for key in ("analyzed", "action_items", "raw"):
            rel = meta.get(key)
            if rel:
                p = _vault_path() / rel
                if p.exists():
                    p.unlink()
                    deleted.append(rel)
        meta_path.unlink()
    else:
        if fp.exists():
            fp.unlink()
            deleted.append(vault_relative_path)

    return {"deleted": deleted}


def toggle_action_item(vault_relative_path: str, task_index: int, completed: bool) -> None:
    fp = _vault_path() / vault_relative_path
    content = fp.read_text(encoding="utf-8")
    matches = list(_TASK_RE.finditer(content))
    if task_index >= len(matches):
        raise IndexError(f"Task index {task_index} out of range (file has {len(matches)} tasks)")

    m = matches[task_index]
    old = m.group(0)
    new_mark = "x" if completed else " "
    new = f"- [{new_mark}] {m.group(2)}"
    content = content[:m.start()] + new + content[m.end():]
    fp.write_text(content, encoding="utf-8")
