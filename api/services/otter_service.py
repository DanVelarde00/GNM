"""
Otter MCP service — polls Otter.ai via Claude's MCP integration.

Requires OTTER_MCP_URL and OTTER_MCP_TOKEN in .env.
Falls back silently if not configured.
"""

import json
import re
import time
from pathlib import Path

import anthropic

import config

_STATE_FILE = config.DATA_DIR / "otter_state.json"
_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _load_state() -> set[str]:
    if _STATE_FILE.exists():
        return set(json.loads(_STATE_FILE.read_text()).get("pulled_ids", []))
    return set()


def _save_state(pulled_ids: set[str]) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps({"pulled_ids": sorted(pulled_ids)}))


def is_configured() -> bool:
    return bool(config.OTTER_MCP_URL and config.OTTER_MCP_TOKEN)


def _slug(title: str) -> str:
    return re.sub(r"[^\w]+", "-", title.lower()).strip("-")[:60]


def pull_new_transcripts() -> list[Path]:
    """
    Call Otter MCP via Claude, pull any transcripts not yet in state,
    write them to INBOX_OTTER, return list of new file paths.
    """
    if not is_configured():
        return []

    client = _get_client()
    pulled_ids = _load_state()

    # Step 1: list available transcripts
    list_response = client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        betas=["mcp-client-2025-04-04"],
        mcp_servers=[{
            "type": "url",
            "url": config.OTTER_MCP_URL,
            "authorization_token": config.OTTER_MCP_TOKEN,
        }],
        messages=[{
            "role": "user",
            "content": (
                "Use the Otter MCP tool to list recent transcripts. "
                "Return ONLY a JSON array (no markdown, no prose) with objects: "
                '{"id": "...", "title": "...", "created_at": "YYYY-MM-DD"}. '
                "Include transcripts from the last 30 days."
            ),
        }],
    )

    raw = "".join(
        b.text for b in list_response.content if hasattr(b, "text")
    ).strip()

    # Extract JSON array from response
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []

    transcripts = json.loads(match.group())
    new_transcripts = [t for t in transcripts if t["id"] not in pulled_ids]

    if not new_transcripts:
        return []

    new_files: list[Path] = []
    config.INBOX_OTTER.mkdir(parents=True, exist_ok=True)

    for t in new_transcripts:
        # Step 2: fetch full text for each new transcript
        text_response = client.beta.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=8096,
            betas=["mcp-client-2025-04-04"],
            mcp_servers=[{
                "type": "url",
                "url": config.OTTER_MCP_URL,
                "authorization_token": config.OTTER_MCP_TOKEN,
            }],
            messages=[{
                "role": "user",
                "content": (
                    f"Use the Otter MCP tool to get the full transcript for id={t['id']}. "
                    "Return ONLY the raw transcript text with speaker labels, exactly as Otter provides it. "
                    "No intro, no explanation."
                ),
            }],
        )

        content = "".join(
            b.text for b in text_response.content if hasattr(b, "text")
        ).strip()

        if not content:
            continue

        date_str = t.get("created_at", time.strftime("%Y-%m-%d"))[:10]
        filename = f"{date_str}-{_slug(t['title'])}.txt"
        out_path = config.INBOX_OTTER / filename
        out_path.write_text(content, encoding="utf-8")

        pulled_ids.add(t["id"])
        new_files.append(out_path)

    _save_state(pulled_ids)
    return new_files
