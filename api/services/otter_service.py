"""
Otter MCP service - polls Otter.ai via Claude's MCP integration.

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

    Throttled to config.OTTER_MAX_PER_CYCLE transcripts per call so a large
    backlog never causes a multi-hour stall. Skipped transcripts are NOT added
    to pulled_ids and will be fetched on the next pull cycle.

    Each step is timed and logged so dashboard log streaming reveals the
    real bottleneck (list call vs. per-transcript fetch).
    """
    if not is_configured():
        return []

    client = _get_client()
    pulled_ids = _load_state()

    # Step 1: list available transcripts
    t_list_start = time.perf_counter()
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
    t_list_elapsed = time.perf_counter() - t_list_start

    raw = "".join(
        b.text for b in list_response.content if hasattr(b, "text")
    ).strip()

    # Extract JSON array from response
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        print(f"[Otter] listed 0 transcripts in {t_list_elapsed:.1f}s (no JSON array in response)")
        return []

    transcripts = json.loads(match.group())
    new_transcripts = [t for t in transcripts if t["id"] not in pulled_ids]

    print(f"[Otter] listed {len(transcripts)} transcript(s) in {t_list_elapsed:.1f}s,"
          f" {len(new_transcripts)} new")

    if not new_transcripts:
        return []

    # Sort oldest-first so the backlog drains in chronological order
    new_transcripts.sort(key=lambda t: t.get("created_at", ""), reverse=False)

    # Throttle: cap to OTTER_MAX_PER_CYCLE per pull; remainder picked up next cycle
    if len(new_transcripts) > config.OTTER_MAX_PER_CYCLE:
        print(
            f"[Otter] {len(new_transcripts)} new, pulling first {config.OTTER_MAX_PER_CYCLE}"
            f" this cycle (throttle={config.OTTER_MAX_PER_CYCLE},"
            f" {len(new_transcripts) - config.OTTER_MAX_PER_CYCLE} deferred)"
        )
        new_transcripts = new_transcripts[:config.OTTER_MAX_PER_CYCLE]

    new_files: list[Path] = []
    config.INBOX_OTTER.mkdir(parents=True, exist_ok=True)

    for t in new_transcripts:
        # Step 2: fetch full text for each new transcript
        t_fetch_start = time.perf_counter()
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
        t_fetch_elapsed = time.perf_counter() - t_fetch_start

        content = "".join(
            b.text for b in text_response.content if hasattr(b, "text")
        ).strip()

        title = t.get("title", t["id"])
        if not content:
            print(f"[Otter] fetched '{title}' in {t_fetch_elapsed:.1f}s (empty - skipping)")
            continue

        print(f"[Otter] fetched '{title}' in {t_fetch_elapsed:.1f}s ({len(content)} chars)")

        date_str = t.get("created_at", time.strftime("%Y-%m-%d"))[:10]
        filename = f"{date_str}-{_slug(t['title'])}.txt"
        out_path = config.INBOX_OTTER / filename
        out_path.write_text(content, encoding="utf-8")

        pulled_ids.add(t["id"])
        new_files.append(out_path)

    _save_state(pulled_ids)
    return new_files
