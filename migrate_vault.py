#!/usr/bin/env python3
"""
migrate_vault.py — Update existing vault notes to match current format.

Changes applied:
  - project frontmatter: "[[ProjectName]]" → plain ProjectName
  - project body references: [[ProjectName]] → plain ProjectName
  - tags: ensures short-form project tag (#calico etc.) is present

Run once after pulling changes:
    python migrate_vault.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

VAULT = config.VAULT_PATH
PROJECTS = set(config.PROJECTS)

_FM_RE = re.compile(r"^(---\s*\n)(.*?)(\n---\s*\n?)(.*)", re.DOTALL)


def migrate_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    m = _FM_RE.match(raw)
    if not m:
        return False

    open_fence, fm_text, close_fence, body = m.groups()
    changed = False

    # ── Fix project field in frontmatter ──────────────────────────
    def fix_project(match):
        nonlocal changed
        proj = match.group(1)
        changed = True
        return f"project: {proj}"

    new_fm = re.sub(r'project:\s*["\']?\[\[([^\]]+)\]\]["\']?', fix_project, fm_text)

    # ── Ensure short-form project tag in frontmatter tags ─────────
    proj_match = re.search(r"^project:\s*(\S+)", new_fm, re.MULTILINE)
    if proj_match:
        proj_name = proj_match.group(1).strip("\"'")
        if proj_name in PROJECTS:
            proj_tag = f"#{proj_name.lower()}"
            # Check existing tags (handles both inline list and block list)
            existing_tags = re.findall(r"-\s*(#\S+|\S+)", new_fm)
            tag_values = {t.lstrip("#") for t in existing_tags}
            if proj_name.lower() not in tag_values and proj_tag.lstrip("#") not in tag_values:
                # Append to tags block if it exists, else skip (template files)
                if "tags:" in new_fm:
                    new_fm = re.sub(
                        r"(tags:(?:\s*\n(?:\s+-[^\n]*))*)",
                        lambda mm: mm.group(0).rstrip() + f"\n  - {proj_tag}",
                        new_fm,
                        count=1,
                    )
                    changed = True

    # ── Remove [[ProjectName]] wiki-links from body ───────────────
    new_body = body
    for proj in PROJECTS:
        pattern = f"[[{proj}]]"
        if pattern in new_body:
            new_body = new_body.replace(pattern, proj)
            changed = True

    if not changed:
        return False

    path.write_text(open_fence + new_fm + close_fence + new_body, encoding="utf-8")
    return True


def main():
    if not VAULT.exists():
        print(f"Vault not found at {VAULT}")
        print("Set GNM_VAULT_PATH in .env or check config.py")
        sys.exit(1)

    print(f"Migrating vault: {VAULT}")
    print(f"Known projects: {', '.join(sorted(PROJECTS))}")
    print()

    md_files = list(VAULT.rglob("*.md"))
    updated = 0
    skipped = 0

    for path in md_files:
        try:
            if migrate_file(path):
                rel = path.relative_to(VAULT)
                print(f"  updated  {rel}")
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ERROR    {path.name}: {e}")

    print()
    print(f"Done. {updated} updated, {skipped} unchanged.")


if __name__ == "__main__":
    main()
