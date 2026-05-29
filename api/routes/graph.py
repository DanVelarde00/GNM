import re
from pathlib import Path

from fastapi import APIRouter

import config

router = APIRouter()

_WIKI_LINK = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]")

PROJECT_ORDER = ["Calico", "Cobia", "Goldstone", "Personal", "Vistra", "Zelestra"]


@router.get("")
def get_graph():
    vault = config.VAULT_PATH
    nodes: list[dict] = []
    node_ids: set[str] = set()

    # Build stem (lowercase) -> relative path map for wiki-link resolution
    stem_map: dict[str, str] = {}
    all_files: list[tuple[Path, str]] = []

    for md in vault.rglob("*.md"):
        if md.name.startswith(".") or ".obsidian" in md.parts:
            continue
        rel = str(md.relative_to(vault)).replace("\\", "/")
        all_files.append((md, rel))
        stem_map[md.stem.lower()] = rel
        stem_map[md.name[:-3].lower()] = rel  # with spaces / mixed case variants

    # Build nodes
    for md, rel in all_files:
        parts = rel.split("/")
        if parts[0] == "Projects" and len(parts) > 1:
            project = parts[1]
            node_type = "note"
        elif parts[0] == "People":
            project = "People"
            node_type = "person"
        else:
            project = ""
            node_type = "other"

        nodes.append({
            "id": rel,
            "label": md.stem.replace("-", " ").title(),
            "project": project,
            "type": node_type,
        })
        node_ids.add(rel)

    # Build edges by parsing wiki-links
    links: list[dict] = []
    seen_edges: set[tuple[str, str]] = set()

    for md, rel in all_files:
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for m in _WIKI_LINK.finditer(content):
            target_name = m.group(1).strip()
            target_rel = stem_map.get(target_name.lower())
            if target_rel and target_rel != rel and target_rel in node_ids:
                edge = (rel, target_rel)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    links.append({"source": rel, "target": target_rel})

    return {"nodes": nodes, "links": links}
