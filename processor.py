"""
GNM Transcript Processor
Reads a raw transcript, sends it through Claude for analysis,
writes structured markdown to the vault.
"""

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

Your job:
1. Read the raw transcript/note.
2. Detect which project it belongs to from context. If you can't determine the project, use "General".
3. Extract the date of the meeting/note. If not explicit, use today's date.
4. Identify all participants mentioned.
5. Determine a short topic (2-5 words) for the filename.

Output EXACTLY this format (no extra text before or after):

---YAML---
date: YYYY-MM-DD
type: meeting or note
source: otter or inq or manual
participants:
  - Name One
  - Name Two
project: ProjectName
tags:
  - tag-one
  - tag-two
topic: short-topic-slug
---END YAML---

## Summary
3-5 sentence summary of the content.

## Key Points
- Point one
- Point two

## Action Items
- [ ] Action item with @Owner if identifiable
- [ ] Another action item

## Decisions
- Decision one
- Decision two

## Raw Transcript Link
(will be filled by the system)
""".format(projects=", ".join(config.PROJECTS))


# ── File reading helpers ────────────────────────────────────────────────────

def read_transcript(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".txt" or suffix == ".md":
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


# ── Parse Claude's response ────────────────────────────────────────────────

def parse_response(response_text: str) -> dict:
    yaml_match = re.search(r"---YAML---\n(.+?)\n---END YAML---", response_text, re.DOTALL)
    if not yaml_match:
        raise ValueError("Could not parse YAML block from Claude response")

    yaml_raw = yaml_match.group(1)
    metadata = {}

    for line in yaml_raw.strip().split("\n"):
        line = line.strip()
        if line.startswith("- "):
            # List item — append to last key
            metadata.setdefault(last_key, []).append(line[2:].strip())
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            last_key = key
            if val:
                metadata[key] = val
            else:
                metadata[key] = []

    # Body is everything after the YAML block
    body_start = response_text.find("---END YAML---")
    body = response_text[body_start + len("---END YAML---"):].strip()

    return {"metadata": metadata, "body": body}


# ── Build the output markdown ──────────────────────────────────────────────

def build_markdown(metadata: dict, body: str, source_filename: str) -> str:
    participants = metadata.get("participants", [])
    if isinstance(participants, str):
        participants = [participants]

    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    frontmatter = f"""---
date: {metadata.get('date', datetime.now().strftime('%Y-%m-%d'))}
type: {metadata.get('type', 'note')}
source: {metadata.get('source', 'unknown')}
participants: [{', '.join(f'"{p}"' for p in participants)}]
project: {metadata.get('project', 'General')}
tags: [{', '.join(tags)}]
---"""

    # Replace the raw transcript link placeholder
    body = body.replace(
        "(will be filled by the system)",
        f"[[Transcripts/{source_filename}]]"
    )

    return f"{frontmatter}\n\n{body}\n"


# ── Route output to correct vault location ──────────────────────────────────

def route_to_vault(metadata: dict, markdown: str, source_path: Path):
    project = metadata.get("project", "General")

    # Validate project — if unknown, create it
    project_dir = config.VAULT_PATH / "Projects" / project
    if not project_dir.exists():
        print(f"  New project detected: {project} — creating folder structure")
        for sub in ["Notes", "Transcripts", "AI Analyzed Notes", "Action Items",
                     "Weekly Reports", "People"]:
            (project_dir / sub).mkdir(parents=True, exist_ok=True)

    # Determine date and week folder
    date_str = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        date = datetime.now()

    year = str(date.year)
    week_folder = get_week_folder(date)

    # Write analyzed note
    topic = metadata.get("topic", "untitled")
    topic = re.sub(r"[^\w\-]", "-", topic.lower()).strip("-")
    filename = f"{date_str}-{topic}.md"

    out_dir = project_dir / "AI Analyzed Notes" / year / week_folder
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    out_path.write_text(markdown, encoding="utf-8")
    print(f"  Written: {out_path}")

    # Copy raw transcript to project Transcripts folder
    transcript_dir = project_dir / "Transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, transcript_dir / source_path.name)
    print(f"  Transcript copied: {transcript_dir / source_path.name}")

    return out_path


# ── Move source to Processed ───────────────────────────────────────────────

def mark_processed(source_path: Path):
    config.INBOX_PROCESSED.mkdir(parents=True, exist_ok=True)
    dest = config.INBOX_PROCESSED / source_path.name
    # Avoid overwrite — append timestamp if exists
    if dest.exists():
        stem = source_path.stem
        suffix = source_path.suffix
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        dest = config.INBOX_PROCESSED / f"{stem}_{ts}{suffix}"
    shutil.move(str(source_path), str(dest))
    print(f"  Moved to processed: {dest}")


# ── Main processing function ───────────────────────────────────────────────

def process_file(file_path: Path, source_type: str = "otter") -> Path:
    print(f"\nProcessing: {file_path.name}")
    print(f"  Source type: {source_type}")

    # Read transcript
    transcript = read_transcript(file_path)
    if not transcript.strip():
        print("  SKIP: Empty file")
        return None

    print(f"  Transcript length: {len(transcript)} chars")

    # Call Claude
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
    print(f"  Claude response: {len(response_text)} chars")

    # Parse and build output
    parsed = parse_response(response_text)
    # Ensure source type is set correctly
    parsed["metadata"]["source"] = source_type
    markdown = build_markdown(parsed["metadata"], parsed["body"], file_path.name)

    # Route to vault
    out_path = route_to_vault(parsed["metadata"], markdown, file_path)

    # Move source to Processed
    mark_processed(file_path)

    return out_path
