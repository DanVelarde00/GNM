"""
GNM Transcript Processor
Full Obsidian-aware agent: reads transcripts, calls Claude for analysis,
routes structured markdown to the vault with wiki-links, tags, people
management, and action item extraction.
"""

import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import anthropic
from docx import Document

import config

# ── Claude processing prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a note analysis assistant for Glen at Calico Infrastructure Holdings.
You process meeting transcripts and notes into structured Obsidian-compatible markdown.

Known projects: {projects}

Tag taxonomy:
- Project tags (use short form): #calico, #cobia, #personal, #vistra, #zelestra
- Type tags: #meeting, #note, #call, #brainstorm
- Topic tags: #solar-tax-equity, #sce, #due-diligence, #finance, #legal, #operations, #strategy

IMPORTANT — When processing meeting transcripts, IGNORE all opening pleasantries, small talk,
greetings, and closing courtesies (e.g. "How are you?", "Thanks for joining", "Talk to you soon",
"Have a great day"). Begin your summary and extraction from the first substantive business topic.

Your job:
1. Read the raw transcript/note.
2. Detect which project it belongs to from context. If unclear, use "General".
   If multiple projects are discussed, pick the primary one.
3. Extract the date. If not explicit in the text, use today: {today}.
4. Identify ALL participants/people mentioned by name.
5. Determine a short topic (2-5 words, lowercase, hyphenated) for the filename.
6. Assign relevant tags from the taxonomy above. Add new topic tags if needed.

You MUST respond with valid JSON only. No markdown, no explanation, no code fences.
The JSON schema:

{{
  "date": "YYYY-MM-DD",
  "type": "meeting|note|call",
  "source": "otter|inq|manual",
  "participants": ["Name One", "Name Two"],
  "project": "ProjectName",
  "tags": ["#calico", "#meeting", "#solar-tax-equity"],
  "topic": "short-topic-slug",
  "summary": "3-5 sentence summary of the content.",
  "key_points": ["Point one", "Point two"],
  "action_items": [
    {{"task": "Do something", "owner": "Name or null", "due": "YYYY-MM-DD or null"}},
  ],
  "decisions": ["Decision one", "Decision two"]
}}
""".format(projects=", ".join(config.PROJECTS), today=datetime.now().strftime("%Y-%m-%d"))


# ── File reading helpers ────────────────────────────────────────────────────

def read_transcript(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8")
    elif suffix == ".docx":
        doc = Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ── Date/week helpers ───────────────────────────────────────────────────────

def get_week_folder(date: datetime) -> str:
    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)
    _, week_num, _ = date.isocalendar()
    return f"W{week_num:02d}_{week_start.strftime('%b%d')}-{week_end.strftime('%b%d')}"


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return datetime.now()


# ── Parse Claude's JSON response ───────────────────────────────────────────

def parse_response(response_text: str) -> dict:
    text = response_text.strip()
    # Strip code fences if Claude wraps it anyway
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


# ── Build Obsidian markdown with wiki-links ─────────────────────────────────

def build_analyzed_note(data: dict, source_filename: str, project: str) -> str:
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    note_type = data.get("type", "note")
    source = data.get("source", "unknown")
    participants = data.get("participants", [])
    tags = data.get("tags", [])
    topic = data.get("topic", "untitled")

    # YAML frontmatter
    participant_yaml = "\n".join(f'  - "[[{p}]]"' for p in participants)
    tag_yaml = "\n".join(f"  - {t}" for t in tags)

    lines = [
        "---",
        f"date: {date}",
        f"type: {note_type}",
        f"source: {source}",
        f"project: \"[[{project}]]\"",
        "participants:",
        participant_yaml,
        "tags:",
        tag_yaml,
        "---",
        "",
        f"# {topic.replace('-', ' ').title()}",
        "",
        f"**Project:** [[{project}]]  ",
        f"**Date:** {date}  ",
        f"**Participants:** {', '.join(f'[[{p}]]' for p in participants)}  ",
        f"**Source:** {source}",
        "",
        "## Summary",
        data.get("summary", ""),
        "",
        "## Key Points",
    ]

    for point in data.get("key_points", []):
        lines.append(f"- {point}")

    lines.append("")
    lines.append("## Action Items")
    for item in data.get("action_items", []):
        task = item.get("task", "")
        owner = item.get("owner")
        due = item.get("due")
        owner_str = f" — [[{owner}]]" if owner else ""
        due_str = f" (due: {due})" if due else ""
        lines.append(f"- [ ] {task}{owner_str}{due_str}")

    lines.append("")
    lines.append("## Decisions")
    for decision in data.get("decisions", []):
        lines.append(f"- {decision}")

    lines.append("")
    lines.append("## Source")
    source_stem = Path(source_filename).stem
    lines.append(f"[[{source_stem}]]")
    lines.append("")

    return "\n".join(lines)


# ── Build action items file ─────────────────────────────────────────────────

def build_action_items_note(data: dict, analyzed_note_filename: str, project: str) -> str | None:
    items = data.get("action_items", [])
    if not items:
        return None

    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    topic = data.get("topic", "untitled")

    lines = [
        "---",
        f"date: {date}",
        f"project: \"[[{project}]]\"",
        f"source_note: \"[[{analyzed_note_filename}]]\"",
        "tags:",
        "  - action-items",
        "---",
        "",
        f"# Action Items — {topic.replace('-', ' ').title()}",
        "",
        f"From: [[{analyzed_note_filename.replace('.md', '')}]]",
        "",
    ]

    for item in items:
        task = item.get("task", "")
        owner = item.get("owner")
        due = item.get("due")
        owner_str = f" — [[{owner}]]" if owner else ""
        due_str = f" (due: {due})" if due else ""
        lines.append(f"- [ ] {task}{owner_str}{due_str}")

    lines.append("")
    return "\n".join(lines)


# ── People management ──────────────────────────────────────────────────────

def update_people(data: dict, project: str):
    """Create or update People/ .md files for each participant."""
    participants = data.get("participants", [])
    if not participants:
        return

    people_dir = config.VAULT_PATH / "Projects" / project / "People"
    people_dir.mkdir(parents=True, exist_ok=True)

    for person in participants:
        person_file = people_dir / f"{person}.md"
        if person_file.exists():
            # Person file already exists — Obsidian backlinks handle the rest
            continue

        content = f"""---
name: "{person}"
role:
organization:
tags:
  - person
---

# {person}

## Related Notes
```dataview
LIST
FROM "Projects/{project}"
WHERE contains(participants, "{person}")
SORT date DESC
```

## Action Items
```dataview
TASK
FROM "Projects/{project}"
WHERE contains(text, "{person}") AND !completed
```
"""
        person_file.write_text(content, encoding="utf-8")
        print(f"    Created person: {person_file}")


# ── Transcript vs note detection ────────────────────────────────────────────

def _is_transcript(source_path: Path, data: dict) -> bool:
    """Determine if the source is a transcript (vs a note) based on content signals."""
    # Source type is a strong signal
    source = data.get("source", "")
    if source == "otter":
        return True
    if source == "inq":
        return False

    # Check for timestamp patterns (e.g., "0:03", "12:45", "1:23:45")
    text = source_path.read_text(encoding="utf-8")
    timestamp_pattern = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
    timestamp_hits = len(timestamp_pattern.findall(text[:2000]))

    # Check for speaker labels (e.g., "Name  0:03" or "Speaker 1:")
    speaker_pattern = re.compile(r"^[A-Z][\w\s]+(?:\s+\d+:\d{2}|\s*:)", re.MULTILINE)
    speaker_hits = len(speaker_pattern.findall(text[:2000]))

    # If timestamps and speaker labels are frequent, it's a transcript
    if timestamp_hits >= 3 and speaker_hits >= 2:
        return True

    # Claude's type detection as fallback
    if data.get("type") in ("meeting", "call"):
        return True

    return False


# ── Route output to vault ──────────────────────────────────────────────────

def route_to_vault(data: dict, source_path: Path) -> dict:
    project = data.get("project", "General")

    # Validate project — create structure if new
    project_dir = config.VAULT_PATH / "Projects" / project
    if not project_dir.exists():
        print(f"  New project detected: {project}")
        for sub in ["Notes", "Transcripts", "AI Analyzed Notes",
                     "Action Items", "Weekly Reports", "People"]:
            (project_dir / sub).mkdir(parents=True, exist_ok=True)

    # Date and week
    date = parse_date(data.get("date"))
    year = str(date.year)
    week_folder = get_week_folder(date)
    date_str = date.strftime("%Y-%m-%d")

    # Filename
    topic = data.get("topic", "untitled")
    topic_slug = re.sub(r"[^\w\-]", "-", topic.lower()).strip("-")
    filename = f"{date_str}-{topic_slug}.md"

    # ── Write analyzed note ──
    analyzed_dir = project_dir / "AI Analyzed Notes" / year / week_folder
    analyzed_dir.mkdir(parents=True, exist_ok=True)
    analyzed_path = analyzed_dir / filename

    analyzed_md = build_analyzed_note(data, source_path.name, project)
    analyzed_path.write_text(analyzed_md, encoding="utf-8")
    print(f"  Analyzed note: {analyzed_path}")

    # ── Write action items ──
    actions_filename = filename.replace(".md", "-actions.md")
    action_items_md = build_action_items_note(data, filename, project)
    ai_path = None
    if action_items_md:
        ai_dir = project_dir / "Action Items" / year / week_folder
        ai_dir.mkdir(parents=True, exist_ok=True)
        ai_path = ai_dir / actions_filename
        ai_path.write_text(action_items_md, encoding="utf-8")
        print(f"  Action items: {ai_path}")

    # ── Save raw source as .md (route by content type) ──
    is_transcript = _is_transcript(source_path, data)
    if is_transcript:
        raw_dir = project_dir / "Transcripts"
        raw_type = "transcript"
    else:
        raw_dir = project_dir / "Notes"
        raw_type = "note"

    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_filename = source_path.stem + ".md"
    raw_path = raw_dir / raw_filename
    raw_text = source_path.read_text(encoding="utf-8")
    raw_md = f"""---
date: {date_str}
type: {raw_type}
source: {data.get('source', 'unknown')}
project: "[[{project}]]"
tags:
  - {raw_type}
---

# {raw_type.title()} — {source_path.stem}

{raw_text}
"""
    raw_path.write_text(raw_md, encoding="utf-8")
    print(f"  {raw_type.title()}: {raw_path}")

    # ── Write sidecar meta (used by delete endpoint) ──
    meta = {
        "analyzed": str(analyzed_path.relative_to(config.VAULT_PATH)).replace("\\", "/"),
        "action_items": str(ai_path.relative_to(config.VAULT_PATH)).replace("\\", "/") if ai_path else None,
        "raw": str(raw_path.relative_to(config.VAULT_PATH)).replace("\\", "/"),
    }
    meta_path = analyzed_dir / filename.replace(".md", ".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # ── Write custom tracker items ──
    try:
        from api.services.tracker_service import load_trackers
        for tracker in load_trackers():
            if not tracker.active:
                continue
            key = tracker.folder_name.lower().replace(" ", "_") + "_items"
            items = data.get(key, [])
            if not items:
                continue
            tracker_dir = project_dir / tracker.folder_name
            tracker_dir.mkdir(parents=True, exist_ok=True)
            for item in items:
                item_title = item.get("title", "untitled")
                item_slug = re.sub(r"[^\w\-]", "-", item_title.lower()).strip("-")[:40]
                item_filename = f"{date_str}-{item_slug}.md"
                item_md = f"""---
date: {date_str}
project: "[[{project}]]"
tracker: "{tracker.name}"
source_note: "[[{filename}]]"
tags:
  - {tracker.folder_name.lower().replace(' ', '-')}
---

# {item_title}

{item.get('details', '')}

From: [[{filename.replace('.md', '')}]]
"""
                (tracker_dir / item_filename).write_text(item_md, encoding="utf-8")
                print(f"  Tracker [{tracker.name}]: {item_filename}")
    except ImportError:
        pass  # API not installed, running standalone

    # ── Create/update people files ──
    update_people(data, project)

    return {"analyzed_path": analyzed_path, "project": project, "data": data}


# ── Move source to Processed ───────────────────────────────────────────────

def mark_processed(source_path: Path):
    config.INBOX_PROCESSED.mkdir(parents=True, exist_ok=True)
    dest = config.INBOX_PROCESSED / source_path.name
    if dest.exists():
        stem = source_path.stem
        suffix = source_path.suffix
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = config.INBOX_PROCESSED / f"{stem}_{ts}{suffix}"
    shutil.move(str(source_path), str(dest))
    print(f"  Moved to processed: {dest}")


# ── Main processing function ───────────────────────────────────────────────

def process_file(file_path: Path, source_type: str = "otter") -> dict | None:
    print(f"\n{'='*60}")
    print(f"  Processing: {file_path.name}")
    print(f"  Source: {source_type}")
    print(f"{'='*60}")

    # Read transcript
    transcript = read_transcript(file_path)
    if not transcript.strip():
        print("  SKIP: Empty file")
        return None

    print(f"  Transcript: {len(transcript)} chars")

    # Call Claude
    print("  Calling Claude...")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Process this {source_type} transcript:\n\n{transcript}"
            }
        ],
    )

    response_text = message.content[0].text
    print(f"  Response: {len(response_text)} chars")

    # Parse JSON
    data = parse_response(response_text)
    data["source"] = source_type

    # Route to vault
    result = route_to_vault(data, file_path)

    # Move source to Processed
    mark_processed(file_path)

    print(f"\n  Done -> {result['project']}/{file_path.name}")
    return result
