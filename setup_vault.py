#!/usr/bin/env python3
"""
GNM Vault Setup Script
Creates the Obsidian vault folder structure and starter files
for Glen's Note Management pipeline.

Usage:
    python setup_vault.py
"""

import os
from pathlib import Path
from datetime import datetime, timedelta


def get_current_week_info():
    """Return (year, week_number, week_start, week_end) for the current week."""
    today = datetime.now()
    # ISO week: Monday = start
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    iso_year, iso_week, _ = today.isocalendar()
    return iso_year, iso_week, week_start, week_end


def format_week_folder(year, week_num, week_start, week_end):
    """Format: W16_Apr14-Apr20"""
    start_str = week_start.strftime("%b%d")
    end_str = week_end.strftime("%b%d")
    return f"W{week_num:02d}_{start_str}-{end_str}"


def prompt_path(label, default):
    """Ask user for a path, with a default."""
    user_input = input(f"{label} [{default}]: ").strip()
    return Path(user_input) if user_input else Path(default)


def create_dir(path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def write_file(path, content=""):
    """Write file if it doesn't exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


# ── Starter file templates ──────────────────────────────────────────────────

OBSIDIAN_APP_JSON = """{
  "alwaysUpdateLinks": true,
  "newFileLocation": "current",
  "attachmentFolderPath": "Attachments"
}
"""

OBSIDIAN_APPEARANCE_JSON = """{
  "baseFontSize": 16,
  "interfaceFontSize": 14
}
"""

DATAVIEW_PLUGIN_JSON = """{
  "taskCompletionTracking": true,
  "taskCompletionUseEmojiShorthand": false,
  "taskCompletionText": "completion",
  "recursiveSubTaskCompletion": false,
  "warnOnEmptyResult": true,
  "renderNullAs": "\\\\-",
  "maxRecursiveRenderDepth": 4,
  "tableIdColumnName": "File",
  "tableGroupColumnName": "Group",
  "defaultDateFormat": "MMMM dd, yyyy",
  "defaultDateTimeFormat": "h:mm a - MMMM dd, yyyy",
  "enableDataviewJs": true,
  "enableInlineDataviewJs": true
}
"""

COMMUNITY_PLUGINS_JSON = '["dataview"]'

HOME_NOTE = """---
tags: [dashboard]
---

# Glen's Note Management Vault

Welcome to the GNM vault. This vault is managed by the GNM processing pipeline.

## Quick Navigation
- [[Projects/]] — All project folders
- [[Templates/]] — Note templates

## Recent Notes
```dataview
TABLE date, project, type
FROM ""
WHERE date
SORT date DESC
LIMIT 10
```

## Open Action Items
```dataview
TASK
FROM ""
WHERE !completed
SORT file.name ASC
```
"""

ANALYZED_NOTE_TEMPLATE = """---
date: {{date}}
type: {{type}}
source: {{source}}
participants: []
project: {{project}}
tags: []
---

## Summary


## Key Points
-

## Action Items
- [ ]

## Decisions
-

## Source
Link to raw transcript: [[]]
"""

ACTION_ITEMS_TEMPLATE = """---
date: {{date}}
project: {{project}}
week: {{week}}
tags: [action-items]
---

## Action Items — {{project}} — {{week}}

- [ ]
"""

WEEKLY_REPORT_TEMPLATE = """---
date: {{date}}
project: {{project}}
week: {{week}}
type: weekly-report
tags: [weekly-report]
---

## Weekly Report — {{project}} — {{week}}

### Summary


### Key Decisions
-

### Action Items for Next Week
- [ ]

### Notes Reviewed
-
"""

PERSON_TEMPLATE = """---
name: {{name}}
role:
organization:
tags: [person]
---

# {{name}}

## Role


## Related Notes
```dataview
LIST
FROM ""
WHERE contains(participants, "{{name}}")
SORT date DESC
```

## Action Items
```dataview
TASK
FROM ""
WHERE contains(text, "{{name}}") AND !completed
```
"""


def main():
    print("=" * 60)
    print("  GNM Vault Setup")
    print("  Glen's Note Management — Folder Structure Generator")
    print("=" * 60)
    print()

    # ── Gather paths ────────────────────────────────────────────

    vault_path = prompt_path(
        "Obsidian vault location",
        os.path.expanduser("~/obsidian/GlenVault"),
    )

    inbox_path = prompt_path(
        "Note inbox location (Dropbox)",
        os.path.expanduser("~/Dropbox/NoteInbox"),
    )

    # Starter projects
    print()
    default_projects = "Calico, Cobia, Personal, Vistra, Zelestra"
    projects_input = input(f"Initial projects (comma-separated) [{default_projects}]: ").strip()
    projects = [p.strip() for p in (projects_input or default_projects).split(",") if p.strip()]

    print()
    print(f"  Vault:    {vault_path}")
    print(f"  Inbox:    {inbox_path}")
    print(f"  Projects: {', '.join(projects)}")
    print()
    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("Aborted.")
        return

    # ── Get current week for sample folders ─────────────────────

    year, week_num, week_start, week_end = get_current_week_info()
    week_folder = format_week_folder(year, week_num, week_start, week_end)

    # ── Create inbox structure ──────────────────────────────────

    print()
    print("Creating inbox folders...")
    for sub in ["Inq", "Otter", "Manual", "Processed"]:
        p = inbox_path / sub
        create_dir(p)
        print(f"  {p}")

    # ── Create vault structure ──────────────────────────────────

    print()
    print("Creating vault structure...")

    # Root-level folders
    create_dir(vault_path / "Attachments")
    create_dir(vault_path / "Templates")

    # Per-project folders
    for project in projects:
        base = vault_path / "Projects" / project
        create_dir(base / "Notes")
        create_dir(base / "Transcripts")
        create_dir(base / "AI Analyzed Notes" / str(year) / week_folder)
        create_dir(base / "Action Items" / str(year) / week_folder)
        create_dir(base / "Weekly Reports" / str(year))
        create_dir(base / "People")
        print(f"  {base}")

    # ── Write starter files ─────────────────────────────────────

    print()
    print("Writing starter files...")

    # Obsidian config
    obsidian_config = vault_path / ".obsidian"
    create_dir(obsidian_config)
    create_dir(obsidian_config / "plugins" / "dataview")
    write_file(obsidian_config / "app.json", OBSIDIAN_APP_JSON)
    write_file(obsidian_config / "appearance.json", OBSIDIAN_APPEARANCE_JSON)
    write_file(obsidian_config / "community-plugins.json", COMMUNITY_PLUGINS_JSON)
    write_file(
        obsidian_config / "plugins" / "dataview" / "data.json",
        DATAVIEW_PLUGIN_JSON,
    )
    print(f"  .obsidian config")

    # Home note
    write_file(vault_path / "Home.md", HOME_NOTE)
    print(f"  Home.md")

    # Templates
    write_file(vault_path / "Templates" / "Analyzed Note.md", ANALYZED_NOTE_TEMPLATE)
    write_file(vault_path / "Templates" / "Action Items.md", ACTION_ITEMS_TEMPLATE)
    write_file(vault_path / "Templates" / "Weekly Report.md", WEEKLY_REPORT_TEMPLATE)
    write_file(vault_path / "Templates" / "Person.md", PERSON_TEMPLATE)
    print(f"  Templates (4 files)")

    # ── Shell alias for start-my-day ────────────────────────────

    script_path = Path(__file__).resolve().parent / "start-my-day.sh"
    if script_path.exists():
        script_path.chmod(script_path.stat().st_mode | 0o111)  # make executable

    import platform
    if platform.system() == "Darwin":
        print()
        print("─" * 60)
        print("  Setting up 'start-my-day' command...")

        # Detect shell config file
        shell_rc = Path.home() / ".zshrc"
        if not shell_rc.exists():
            shell_rc = Path.home() / ".bash_profile"

        alias_line = f'\nalias start-my-day="{script_path}"\n'
        existing = shell_rc.read_text(encoding="utf-8") if shell_rc.exists() else ""

        if "start-my-day" in existing:
            print(f"  Alias already set in {shell_rc} — skipping.")
        else:
            add_alias = input(f"  Add 'start-my-day' alias to {shell_rc}? [Y/n]: ").strip().lower()
            if not add_alias or add_alias == "y":
                with open(shell_rc, "a", encoding="utf-8") as f:
                    f.write(alias_line)
                print(f"  Added alias to {shell_rc}")
                print(f"  Run `source {shell_rc}` or open a new terminal to activate it.")
            else:
                print(f"  Skipped. To add manually:")
                print(f'    echo \'alias start-my-day="{script_path}"\' >> {shell_rc}')

        print()
        print("  How it works:")
        print("    - Type `start-my-day` in any terminal window")
        print("    - It starts the GNM server + processor in the background")
        print("    - Opens the dashboard at http://localhost:3000 in your browser")
        print("    - Logs go to /tmp/gnm-server.log if you need to debug")

    # ── Migrate existing notes ───────────────────────────────────

    print()
    print("─" * 60)
    run_migrate = input("  Migrate existing vault notes to new format? [Y/n]: ").strip().lower()
    if not run_migrate or run_migrate == "y":
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            import migrate_vault
            migrate_vault.VAULT = vault_path
            migrate_vault.main()
        except Exception as e:
            print(f"  Migration error: {e}")
            print("  Run manually: python migrate_vault.py")

    # ── Done ────────────────────────────────────────────────────

    print()
    print("=" * 60)
    print("  Setup complete!")
    print()
    print(f"  Vault: {vault_path}")
    print(f"  Inbox: {inbox_path}")
    print()
    print("  Next steps:")
    print("    1. Open Obsidian -> 'Open folder as vault' -> select the vault path")
    print("    2. Enable the Dataview community plugin when prompted")
    print("    3. Drop test files into the inbox folders")
    if platform.system() == "Darwin":
        print("    4. Type `start-my-day` to launch everything")
    print("=" * 60)


if __name__ == "__main__":
    main()
