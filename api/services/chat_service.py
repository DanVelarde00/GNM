"""
RAG-powered AI chat: searches vault via Whoosh, then streams Claude response.
Supports tool use: get_processor_status, file_bug_report.
"""

import json
from typing import AsyncIterator

import anthropic

import config
from api.models.chat_models import ChatMessage
from api.services import search_service, vault_service
from api.services import github_service
from api.services.process_manager import ProcessManager

# ── System prompt ─────────────────────────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """You are Glen's personal assistant for his note management system at Calico Infrastructure Holdings.
You help Glen find information from his meeting notes and transcripts, and you can check on the system and report issues to Dan (the developer).

IMPORTANT — Scope rules (follow strictly):
- Answer ONLY from the Context Documents provided below. Do not use outside knowledge to fill in gaps about Glen's projects, meetings, people, or business.
- If the answer is not in the context documents, say exactly: "I don't see that in the vault — it may not have been processed yet."
- Never invent facts, names, decisions, or action items that are not explicitly in the context.
- You may use general knowledge only for system/tool questions (e.g., explaining what a processor status means), not for vault content questions.

How you work:
- You answer questions using the vault context documents provided below.
- Cite file paths when referencing specific notes (e.g., "According to Projects/Goldstone/...").
- Use [[wiki-links]] when mentioning people or projects.
- Be concise, friendly, and non-technical in your replies.
- For action items, include who owns them and any due dates.

When Glen reports something is broken or isn't working:
- Call get_processor_status first so you have the current state and recent log lines.
- Then call file_bug_report with a clear title and a body that describes what Glen said, plus any relevant status/log information.
- After filing, tell Glen the issue link and reassure him that Dan will look into it.

When Glen asks "is processing working?" or "what did it process today?" or similar:
- Call get_processor_status to get live status and recent logs, then summarise in plain language.

Known projects: {projects}

## Context Documents
{context}
"""

# ── Tool schemas ──────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_processor_status",
        "description": (
            "Returns the current status of the background note processor "
            "(running/stopped, uptime, process ID) plus the 50 most recent log lines. "
            "Call this when Glen asks about whether processing is working, what was "
            "processed, or whether there are errors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "file_bug_report",
        "description": (
            "Opens a GitHub issue to report a bug or problem to Dan (the developer). "
            "Call this when Glen says something is broken, not working, or asks for a fix. "
            "Gather relevant context (processor status/logs if applicable) before calling. "
            "The tool returns the URL of the created issue."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short, descriptive issue title (e.g., 'Processor not picking up new Otter transcripts').",
                },
                "body": {
                    "type": "string",
                    "description": (
                        "Detailed description: what Glen reported, any error patterns "
                        "from logs, current processor status. Use Markdown."
                    ),
                },
            },
            "required": ["title", "body"],
        },
    },
]

# ── Context builder ───────────────────────────────────────────────────────────

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

# ── Tool executor ─────────────────────────────────────────────────────────────

def _execute_tool(name: str, tool_input: dict) -> str:
    """Execute a named tool and return the result as a JSON string."""
    if name == "get_processor_status":
        pm = ProcessManager.instance()
        status = pm.get_status()
        logs = pm.get_recent_log(50)
        log_lines = [entry.get("msg", "") for entry in logs]
        result = {
            "status": status,
            "recent_logs": log_lines,
        }
        return json.dumps(result, indent=2)

    if name == "file_bug_report":
        title = tool_input.get("title", "Bug report from Glen")
        body = tool_input.get("body", "No details provided.")
        result = github_service.create_issue(title=title, body=body)
        return json.dumps(result)

    return json.dumps({"error": f"Unknown tool: {name}"})

# ── Main streaming entry point ────────────────────────────────────────────────

async def stream_response(
    message: str,
    history: list[ChatMessage],
    project_filter: str | None = None,
) -> AsyncIterator[dict]:
    """
    Yields dicts:
        {"type": "sources", "files": [...]}
        {"type": "token",   "content": "..."}
        {"type": "done"}
        {"type": "error",   "message": "..."}

    Implements a streaming tool-use loop (capped at 4 iterations).
    When the model calls a tool, we execute it and stream the follow-up response.
    """

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

    max_iterations = 4
    for iteration in range(max_iterations):
        # Open a new stream for this turn
        with client.messages.stream(
            model=config.CLAUDE_MODEL,
            max_tokens=2048,
            system=system,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            # Yield text deltas as they arrive
            for text in stream.text_stream:
                yield {"type": "token", "content": text}

            # After the stream ends, inspect the final message
            final = stream.get_final_message()

        stop_reason = final.stop_reason

        if stop_reason != "tool_use":
            # Natural end — we're done
            break

        # Collect all content blocks from the assistant turn
        assistant_content = final.content  # list of TextBlock | ToolUseBlock

        # Append the full assistant turn to the conversation
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute every tool_use block and collect results
        tool_results = []
        for block in assistant_content:
            if block.type != "tool_use":
                continue

            # Notify Glen visually so he doesn't see a blank pause
            if block.name == "file_bug_report":
                yield {"type": "token", "content": "\n\n_Filing a report with Dan..._\n\n"}
            elif block.name == "get_processor_status":
                yield {"type": "token", "content": "\n\n_Checking the processor..._\n\n"}

            result_str = _execute_tool(block.name, block.input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        # Feed tool results back into the conversation
        messages.append({"role": "user", "content": tool_results})
        # Loop to stream the assistant's follow-up response

    yield {"type": "done"}
