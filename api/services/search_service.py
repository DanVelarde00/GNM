"""
Full-text search over the vault using Whoosh.
Index stored at config.SEARCH_INDEX_PATH.
"""

import os
from pathlib import Path

from whoosh import index as whoosh_index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, DATETIME, STORED
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.query import And, Term, Every

import config
from api.services.vault_service import parse_frontmatter

SCHEMA = Schema(
    path=ID(stored=True, unique=True),
    project=KEYWORD(stored=True, lowercase=True),
    type=KEYWORD(stored=True, lowercase=True),
    date=ID(stored=True),
    tags=KEYWORD(stored=True, commas=True, lowercase=True),
    participants=TEXT(stored=True),
    title=TEXT(stored=True),
    body=TEXT,
)


def _index_dir() -> Path:
    return config.SEARCH_INDEX_PATH


def _get_or_create_index():
    idx_dir = _index_dir()
    if whoosh_index.exists_in(str(idx_dir)):
        return whoosh_index.open_dir(str(idx_dir))
    idx_dir.mkdir(parents=True, exist_ok=True)
    return whoosh_index.create_in(str(idx_dir), SCHEMA)


def build_full_index() -> int:
    """Rebuild the entire search index from vault files. Returns count indexed."""
    idx_dir = _index_dir()
    idx_dir.mkdir(parents=True, exist_ok=True)
    ix = whoosh_index.create_in(str(idx_dir), SCHEMA)
    writer = ix.writer()
    count = 0

    vault = config.VAULT_PATH
    for md in vault.rglob("*.md"):
        if md.name.startswith(".") or ".obsidian" in md.parts:
            continue
        try:
            raw = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        meta, body = parse_frontmatter(raw)
        rel_path = str(md.relative_to(vault)).replace("\\", "/")

        # Extract project from path: Projects/<Name>/...
        parts = rel_path.split("/")
        project = parts[1] if len(parts) > 1 and parts[0] == "Projects" else ""

        tags = meta.get("tags", [])
        if isinstance(tags, list):
            tags_str = ",".join(str(t).lstrip("#") for t in tags)
        else:
            tags_str = str(tags)

        participants = meta.get("participants", [])
        if isinstance(participants, list):
            participants_str = " ".join(
                str(p).replace("[[", "").replace("]]", "").strip('"')
                for p in participants
            )
        else:
            participants_str = str(participants)

        writer.update_document(
            path=rel_path,
            project=project.lower(),
            type=str(meta.get("type", "")),
            date=str(meta.get("date", "")),
            tags=tags_str,
            participants=participants_str,
            title=md.stem.replace("-", " "),
            body=body[:10000],
        )
        count += 1

    writer.commit()
    return count


def index_file(vault_relative_path: str) -> None:
    """Add or update a single file in the index."""
    ix = _get_or_create_index()
    fp = config.VAULT_PATH / vault_relative_path
    if not fp.exists():
        return
    raw = fp.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)

    parts = vault_relative_path.split("/")
    project = parts[1] if len(parts) > 1 and parts[0] == "Projects" else ""

    tags = meta.get("tags", [])
    tags_str = ",".join(str(t).lstrip("#") for t in tags) if isinstance(tags, list) else str(tags)

    participants = meta.get("participants", [])
    if isinstance(participants, list):
        participants_str = " ".join(
            str(p).replace("[[", "").replace("]]", "").strip('"')
            for p in participants
        )
    else:
        participants_str = str(participants)

    writer = ix.writer()
    writer.update_document(
        path=vault_relative_path,
        project=project.lower(),
        type=str(meta.get("type", "")),
        date=str(meta.get("date", "")),
        tags=tags_str,
        participants=participants_str,
        title=fp.stem.replace("-", " "),
        body=body[:10000],
    )
    writer.commit()


def search(
    q: str,
    project: str | None = None,
    file_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    ix = _get_or_create_index()
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "body", "participants", "tags"], SCHEMA, group=OrGroup)
        text_q = parser.parse(q)

        filters = []
        if project:
            filters.append(Term("project", project.lower()))
        if file_type:
            filters.append(Term("type", file_type.lower()))

        final_q = And([text_q] + filters) if filters else text_q
        results = searcher.search(final_q, limit=limit)

        out = []
        for r in results:
            out.append({
                "path": r["path"],
                "project": r.get("project", ""),
                "type": r.get("type", ""),
                "date": r.get("date", ""),
                "title": r.get("title", ""),
                "participants": r.get("participants", ""),
                "score": r.score,
                "highlights": "",
            })
        return out
