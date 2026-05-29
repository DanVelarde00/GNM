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
from typing import Optional

import anthropic
from docx import Document

import config

# ── Claude processing prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a note analysis assistant for Glen at Calico Infrastructure Holdings.
You process meeting transcripts and notes into structured Obsidian-compatible markdown.

Known projects: {projects}
Project aliases (always resolve to the canonical name in your response): {aliases}

Tag taxonomy:
- Project tags (use short form): #calico, #cobia, #personal, #vistra, #zelestra, #goldstone
- Type tags: #meeting, #note, #call, #brainstorm
- Topic tags: #solar-tax-equity, #sce, #due-diligence, #finance, #legal, #operations, #strategy
- People: use #people for individual person notes — NEVER use #person

IMPORTANT — When processing meeting transcripts, IGNORE all opening pleasantries, small talk,
greetings, and closing courtesies (e.g. "How are you?", "Thanks for joining", "Talk to you soon",
"Have a great day"). Begin your summary and extraction from the first substantive business topic.

Your job:
1. Read the raw transcript/note.
2. Detect which project it belongs to from context. If unclear, use "General".
   If multiple projects are discussed, pick the primary one.
3. Extract the date. If not explicit in the text, use today: {today}.
4. Identify ALL participants/people mentioned by name.
5. Determine a short topic (2-5 words, lowercase, hyphenated) for the H1 heading.
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
""".format(
    projects=", ".join(config.PROJECTS),
    aliases=", ".join(f"{alias} → {canonical}" for alias, canonical in config.PROJECT_ALIASES.items()) or "none",
    today=datetime.now().strftime("%Y-%m-%d"),
)


# ── Slug helper ─────────────────────────────────────────────────────────────

def _project_slug(project_name: str) -> str:
    """Convert project name to a tag-safe slug: 'Data Center' → 'data-center'."""
    return re.sub(r"[^\w]+", "-", project_name.lower()).strip("-")


# ── File reading helpers ────────────────────────────────────────────────────

class ScannedPDFError(ValueError):
    """Raised when a PDF has no extractable text (likely a scanned image)."""
    pass


def read_transcript(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in (".txt", ".md"):
        return file_path.read_text(encoding="utf-8")
    elif suffix == ".docx":
        doc = Document(str(file_path))
        return "\n".join(p.text for p in doc.paragraphs)
    elif suffix == ".pdf":
        import pypdf
        reader = pypdf.PdfReader(str(file_path))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text() or ""
            pages_text.append(t)
        full_text = "\n".join(pages_text)
        if not full_text.strip():
            raise ScannedPDFError(
                f"PDF has no extractable text layer (likely a scanned image): {file_path.name}"
            )
        return full_text
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
    # Strip code fences if Claude wraps them around the JSON
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()
    # Use raw_decode starting at the first '{': parses exactly one JSON object
    # and ignores any trailing text/comments Claude appended after the closing '}'.
    start = text.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in Claude response: {text[:200]!r}")
    obj, _ = json.JSONDecoder().raw_decode(text, start)
    return obj


# ── Build Obsidian markdown with wiki-links ─────────────────────────────────

def build_analyzed_note(data: dict, source_filename: str, project: str) -> str:
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    note_type = data.get("type", "note")
    source = data.get("source", "unknown")
    participants = data.get("participants", [])
    tags = list(data.get("tags", []))

    # Guarantee the project tag is always present
    proj_tag = f"#{_project_slug(project)}"
    if proj_tag not in tags:
        tags.insert(0, proj_tag)

    topic = data.get("topic", "untitled")

    # YAML frontmatter
    participant_yaml = "\n".join(f'  - "[[{p}]]"' for p in participants)
    tag_yaml = "\n".join(f"  - {t}" for t in tags)

    lines = [
        "---",
        f"date: {date}",
        f"type: {note_type}",
        f"source: {source}",
        f"project: {project}",
        f"source_file: {source_filename}",
        "participants:",
        participant_yaml,
        "tags:",
        tag_yaml,
        "---",
        "",
        f"# {topic.replace('-', ' ').title()}",
        "",
        f"**Project:** {project}  ",
        f"**Date:** {date}  ",
        f"**Participants:** {', '.join(f'[[{p}]]' for p in participants)}  ",
        f"**Source:** {source_filename}",
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

    return "\n".join(lines)


# ── People management ──────────────────────────────────────────────────────

def update_people(data: dict, project: str):
    """Create or update global People/ .md files for each participant.
    Tags each person with #people and the project-specific tag.
    Merges project tags if the person file already exists.
    """
    participants = data.get("participants", [])
    if not participants:
        return

    people_dir = config.PEOPLE_PATH
    people_dir.mkdir(parents=True, exist_ok=True)

    proj_tag = f"#{_project_slug(project)}"

    for person in participants:
        person_file = people_dir / f"{person}.md"

        if person_file.exists():
            # Read existing file and add project tag if not already present
            raw = person_file.read_text(encoding="utf-8")
            fm_match = re.match(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)", raw, re.DOTALL)
            if fm_match:
                open_fence, fm_text, close_fence, body = fm_match.groups()
                # Check if project tag already present
                existing_tags = re.findall(r"-\s*(#\S+)", fm_text)
                if proj_tag not in existing_tags and "tags:" in fm_text:
                    fm_text = re.sub(
                        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
                        lambda mm: mm.group(0).rstrip() + f"\n  - {proj_tag}",
                        fm_text,
                        count=1,
                    )
                    person_file.write_text(
                        open_fence + fm_text + close_fence + body,
                        encoding="utf-8",
                    )
                    print(f"    Updated person tags: {person_file.name}")
            continue

        # Create new person file
        content = f"""---
name: "{person}"
role:
organization:
tags:
  - "#people"
  - "{proj_tag}"
---

# {person}

## Related Notes
```dataview
LIST
FROM [[]]
SORT date DESC
```

## Open Action Items
```dataview
TASK
FROM [[]]
WHERE !completed
```
"""
        person_file.write_text(content, encoding="utf-8")
        print(f"    Created person: {person_file}")


# ── Route output to vault ──────────────────────────────────────────────────

def route_to_vault(data: dict, source_path: Path) -> dict:
    project = data.get("project", "General")
    project = config.PROJECT_ALIASES.get(project, project)

    # Validate project — create flat structure if new
    project_dir = config.VAULT_PATH / "Projects" / project
    project_dir.mkdir(parents=True, exist_ok=True)

    # Date — prefer Claude's value; fall back to filename date if Claude's is
    # wildly wrong (>180 days from the filename's embedded date).
    date = parse_date(data.get("date"))
    fn_match = re.match(r"(\d{4}-\d{2}-\d{2})", source_path.stem)
    if fn_match:
        fn_date = parse_date(fn_match.group(1))
        if abs((date - fn_date).days) > 180:
            print(f"  WARNING: Claude date {date.date()} is far from filename date {fn_date.date()} — using filename date")
            date = fn_date
    date_str = date.strftime("%Y-%m-%d")

    # ── Deterministic filename from source identity (Fix 5) ──
    # Strip any leading YYYY-MM-DD- from the source stem first, so Otter files
    # (named like "2026-05-29-title.txt") don't get a doubled date prefix.
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}[-_]", "", source_path.stem)
    source_slug = re.sub(r"[^\w\-]", "-", stem.lower()).strip("-") or "untitled"
    filename = f"{date_str}-{source_slug}.md"

    # Handle genuine collision: same date+slug but DIFFERENT source file
    target_path = project_dir / filename
    if target_path.exists():
        # Check if it's the same source (idempotent re-run) or a different one
        existing_raw = target_path.read_text(encoding="utf-8")
        existing_source_match = re.search(r"^source_file:\s*(.+)$", existing_raw, re.MULTILINE)
        existing_source = existing_source_match.group(1).strip() if existing_source_match else None
        if existing_source and existing_source != source_path.name:
            # Different source → numeric suffix
            counter = 2
            while True:
                candidate = project_dir / f"{date_str}-{source_slug}-{counter}.md"
                if not candidate.exists():
                    filename = candidate.name
                    target_path = candidate
                    break
                counter += 1
        # else: same source → overwrite (idempotent)

    analyzed_path = target_path

    # ── Write analyzed note (flat — no subfolders) ──
    analyzed_md = build_analyzed_note(data, source_path.name, project)
    analyzed_path.write_text(analyzed_md, encoding="utf-8")
    print(f"  Analyzed note: {analyzed_path}")

    # ── Write custom tracker items (flat within tracker subfolder) ──
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
project: {project}
tracker: "{tracker.name}"
source_note: "[[{filename.replace('.md', '')}]]"
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

    # ── Create/update people files (global People/ folder) ──
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

def process_file(file_path: Path, source_type: str = "otter") -> Optional[dict]:
    print(f"\n{'='*60}")
    print(f"  Processing: {file_path.name}")
    print(f"  Source: {source_type}")
    print(f"{'='*60}")

    # Read transcript
    try:
        transcript = read_transcript(file_path)
    except ScannedPDFError as e:
        print(f"  SKIP: {file_path.name} appears to be a scanned PDF (needs OCR): {e}")
        return None

    if not transcript.strip():
        print("  SKIP: Empty file")
        return None

    # Truncate to avoid hitting context limits on very long transcripts
    MAX_CHARS = 100_000
    if len(transcript) > MAX_CHARS:
        print(f"  Truncating transcript: {len(transcript)} -> {MAX_CHARS} chars")
        transcript = transcript[:MAX_CHARS]

    print(f"  Transcript: {len(transcript)} chars")

    # Call Claude
    print("  Calling Claude...")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    # Inject today fresh per-call so the date fallback is never stale
    today = datetime.now().strftime("%Y-%m-%d")
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Today's date (use as fallback only if no date is in the text): {today}\n\n"
                    f"Process this {source_type} transcript:\n\n{transcript}"
                ),
            }
        ],
    )

    if not message.content:
        raise ValueError(f"Claude returned empty content (stop_reason: {message.stop_reason})")

    response_text = message.content[0].text
    if not response_text.strip():
        raise ValueError(f"Claude returned empty text (stop_reason: {message.stop_reason})")

    print(f"  Response: {len(response_text)} chars")

    # Parse JSON
    data = parse_response(response_text)
    data["source"] = source_type

    # Route to vault (before mark_processed so a crash doesn't lose the source)
    result = route_to_vault(data, file_path)

    # Move source to Processed
    mark_processed(file_path)

    print(f"\n  Done -> {result['project']}/{file_path.name}")
    return result
