"""
Custom tracker system: CRUD for tracker definitions,
dynamic system prompt injection, and vault folder management.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import config
from api.models.tracker_models import TrackerCreate, TrackerDefinition, TrackerItem
from api.services.vault_service import parse_frontmatter


def _state_file() -> Path:
    return config.TRACKER_STATE_FILE


def load_trackers() -> list[TrackerDefinition]:
    sf = _state_file()
    if not sf.exists():
        return []
    data = json.loads(sf.read_text(encoding="utf-8"))
    return [TrackerDefinition(**t) for t in data]


def save_trackers(trackers: list[TrackerDefinition]) -> None:
    sf = _state_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(
        json.dumps([t.model_dump() for t in trackers], indent=2),
        encoding="utf-8",
    )


def create_tracker(req: TrackerCreate) -> TrackerDefinition:
    trackers = load_trackers()

    tracker = TrackerDefinition(
        id=str(uuid.uuid4()),
        created_at=datetime.now().strftime("%Y-%m-%d"),
        **req.model_dump(),
    )
    trackers.append(tracker)
    save_trackers(trackers)

    # Create tracker folders in every project
    projects_dir = config.VAULT_PATH / "Projects"
    if projects_dir.is_dir():
        for d in projects_dir.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                (d / tracker.folder_name).mkdir(parents=True, exist_ok=True)

    return tracker


def update_tracker(tracker_id: str, updates: dict) -> TrackerDefinition | None:
    trackers = load_trackers()
    for i, t in enumerate(trackers):
        if t.id == tracker_id:
            data = t.model_dump()
            data.update(updates)
            trackers[i] = TrackerDefinition(**data)
            save_trackers(trackers)
            return trackers[i]
    return None


def delete_tracker(tracker_id: str) -> bool:
    trackers = load_trackers()
    for i, t in enumerate(trackers):
        if t.id == tracker_id:
            t.active = False
            trackers[i] = t
            save_trackers(trackers)
            return True
    return False


def get_tracker(tracker_id: str) -> TrackerDefinition | None:
    for t in load_trackers():
        if t.id == tracker_id:
            return t
    return None


def get_tracker_items(tracker_id: str) -> list[TrackerItem]:
    tracker = get_tracker(tracker_id)
    if not tracker:
        return []

    items = []
    projects_dir = config.VAULT_PATH / "Projects"
    if not projects_dir.is_dir():
        return []

    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir() or proj_dir.name.startswith("."):
            continue
        tracker_dir = proj_dir / tracker.folder_name
        if not tracker_dir.is_dir():
            continue
        for md in tracker_dir.rglob("*.md"):
            raw = md.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(raw)
            rel_path = str(md.relative_to(config.VAULT_PATH)).replace("\\", "/")
            items.append(TrackerItem(
                tracker_id=tracker_id,
                project=proj_dir.name,
                file_path=rel_path,
                title=md.stem.replace("-", " ").title(),
                date=str(meta.get("date", "")),
                content_preview=body[:200].strip(),
                tags=[str(t) for t in meta.get("tags", [])],
            ))

    items.sort(key=lambda x: x.date, reverse=True)
    return items


def build_dynamic_system_prompt(base_prompt: str) -> str:
    """Extend the base SYSTEM_PROMPT with active tracker extraction instructions."""
    trackers = load_trackers()
    active = [t for t in trackers if t.active]
    if not active:
        return base_prompt

    additions = ["\n\n## Custom Trackers\nIn addition to the standard fields, extract items for these custom trackers:\n"]

    for t in active:
        key = t.folder_name.lower().replace(" ", "_") + "_items"
        additions.append(f"""
### {t.name}
{t.extraction_prompt}
If relevant content is found, include a "{key}" key in your JSON response:
"{key}": [
  {{"title": "short title", "details": "1-2 sentence detail", "date": "YYYY-MM-DD"}}
]
If no relevant content is found for this tracker, omit the key entirely.
""")

    return base_prompt + "\n".join(additions)
