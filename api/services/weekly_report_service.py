"""
Weekly report generator: scans a week's analyzed notes per project,
sends to Claude for consolidation, writes Weekly Report .md files.
"""

from datetime import datetime, timedelta
from pathlib import Path

import anthropic

import config
from api.services.vault_service import parse_frontmatter
from processor import get_week_folder

WEEKLY_REPORT_PROMPT = """You are a project management assistant for Glen at Calico Infrastructure Holdings.

You are given all the AI-analyzed notes for a single project from one week.
Write a concise weekly summary report.

Respond with valid JSON only:
{{
  "summary": "2-4 paragraph executive summary of the week's activity",
  "key_decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {{"task": "...", "owner": "Name or null", "due": "YYYY-MM-DD or null"}}
  ],
  "risks_or_blockers": ["Risk 1"],
  "notes_reviewed": ["filename1.md", "filename2.md"]
}}
"""


def _get_week_range(target_date: datetime | None = None) -> tuple[datetime, datetime, str]:
    """Get the Monday-Sunday range and folder name for a given date's week."""
    if target_date is None:
        target_date = datetime.now()
    week_start = target_date - timedelta(days=target_date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=6)
    week_folder = get_week_folder(target_date)
    return week_start, week_end, week_folder


def _collect_week_notes(project_dir: Path, week_folder: str) -> list[tuple[str, str]]:
    """Collect all analyzed notes for a project in a given week folder.
    Returns list of (filename, content) tuples."""
    year = str(datetime.now().year)
    notes_dir = project_dir / "AI Analyzed Notes" / year / week_folder
    if not notes_dir.is_dir():
        return []

    notes = []
    for md in sorted(notes_dir.glob("*.md")):
        content = md.read_text(encoding="utf-8")
        notes.append((md.name, content))
    return notes


def generate_report_for_project(
    project: str,
    week_folder: str,
    notes: list[tuple[str, str]],
) -> dict:
    """Call Claude to generate a weekly report from the week's notes."""
    notes_text = ""
    for filename, content in notes:
        notes_text += f"\n\n--- {filename} ---\n{content}"

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=4096,
        system=WEEKLY_REPORT_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Generate a weekly report for project '{project}', week {week_folder}.\n\nNotes from this week:\n{notes_text}",
        }],
    )

    import json
    import re
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return json.loads(text)


def _build_report_md(data: dict, project: str, week_folder: str, date_str: str) -> str:
    """Build the weekly report markdown file."""
    lines = [
        "---",
        f"date: {date_str}",
        f'project: "[[{project}]]"',
        f"week: {week_folder}",
        "type: weekly-report",
        "tags:",
        "  - weekly-report",
        "---",
        "",
        f"# Weekly Report — {project} — {week_folder}",
        "",
        "## Summary",
        data.get("summary", ""),
        "",
        "## Key Decisions",
    ]

    for d in data.get("key_decisions", []):
        lines.append(f"- {d}")

    lines.append("")
    lines.append("## Action Items")
    for item in data.get("action_items", []):
        task = item.get("task", "")
        owner = item.get("owner")
        due = item.get("due")
        owner_str = f" — [[{owner}]]" if owner else ""
        due_str = f" (due: {due})" if due else ""
        lines.append(f"- [ ] {task}{owner_str}{due_str}")

    if data.get("risks_or_blockers"):
        lines.append("")
        lines.append("## Risks & Blockers")
        for r in data["risks_or_blockers"]:
            lines.append(f"- {r}")

    lines.append("")
    lines.append("## Notes Reviewed")
    for n in data.get("notes_reviewed", []):
        stem = n.replace(".md", "")
        lines.append(f"- [[{stem}]]")

    lines.append("")
    return "\n".join(lines)


def generate_weekly_reports(target_date: datetime | None = None) -> list[dict]:
    """Generate weekly reports for all projects that have notes this week.
    Returns list of {project, path, notes_count} for each report written."""
    week_start, week_end, week_folder = _get_week_range(target_date)
    date_str = week_start.strftime("%Y-%m-%d")
    year = str(week_start.year)
    results = []

    projects_dir = config.VAULT_PATH / "Projects"
    if not projects_dir.is_dir():
        return results

    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir() or proj_dir.name.startswith("."):
            continue

        project = proj_dir.name
        notes = _collect_week_notes(proj_dir, week_folder)
        if not notes:
            continue

        print(f"[Weekly Report] {project}: {len(notes)} notes for {week_folder}")

        data = generate_report_for_project(project, week_folder, notes)

        report_md = _build_report_md(data, project, week_folder, date_str)

        report_dir = proj_dir / "Weekly Reports" / year
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{week_folder}.md"
        report_path.write_text(report_md, encoding="utf-8")

        rel_path = str(report_path.relative_to(config.VAULT_PATH)).replace("\\", "/")
        results.append({
            "project": project,
            "path": rel_path,
            "notes_count": len(notes),
        })
        print(f"[Weekly Report] Written: {report_path}")

    return results
