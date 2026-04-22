"""
RAG-powered AI chat: searches vault via Whoosh, then streams Claude response.
"""

from typing import AsyncIterator

import anthropic

import config
from api.models.chat_models import ChatMessage
from api.services import search_service, vault_service

CHAT_SYSTEM_PROMPT = """You are Glen's AI assistant for his note management vault at Calico Infrastructure Holdings.
You answer questions based on the context documents provided below.

Rules:
- Answer ONLY based on the provided context. If the context doesn't contain the answer, say so.
- Cite file paths when referencing specific notes (e.g., "According to Projects/Goldstone/AI Analyzed Notes/...").
- Use [[wiki-links]] when mentioning people or projects.
- Be concise and direct.
- For action items, include who owns them and any due dates.

Known projects: {projects}

## Context Documents
{context}
"""


def _build_context(query: str, project_filter: str | None) -> tuple[str, list[str]]:
    """Search vault and build context string. Returns (context_block, source_paths)."""
    results = search_service.search(q=query, project=project_filter, limit=8)
    if not results:
        return "(No matching documents found in the vault.)", []

    docs = []
    paths = []
    for r in results[:6]:
        try:
            vf = vault_service.get_file(r["path"])
            content = vf.raw[:3000]
            docs.append(f"### {r['path']}\n{content}")
            paths.append(r["path"])
        except FileNotFoundError:
            continue

    return "\n\n---\n\n".join(docs), paths


async def stream_response(
    message: str,
    history: list[ChatMessage],
    project_filter: str | None = None,
) -> AsyncIterator[dict]:
    """Yields dicts: {"type": "sources", ...}, {"type": "token", ...}, {"type": "done"}"""

    context, source_paths = _build_context(message, project_filter)

    yield {"type": "sources", "files": source_paths}

    system = CHAT_SYSTEM_PROMPT.format(
        projects=", ".join(config.PROJECTS),
        context=context,
    )

    messages = []
    for h in history[-10:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": message})

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    with client.messages.stream(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield {"type": "token", "content": text}

    yield {"type": "done"}
