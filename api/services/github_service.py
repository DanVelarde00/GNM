"""
GitHub integration: file bug reports from the AI chat on Glen's behalf.

Primary path: POST to GitHub REST API using GITHUB_TOKEN (if set).
Fallback: shell out to `gh issue create` (gh CLI is authenticated on this machine).
"""

import json
import subprocess
from datetime import datetime, timezone

import httpx

import config

_LABELS = ["from-chat", "bug"]


def _footer(timestamp: str) -> str:
    return (
        "\n\n---\n"
        f"*Filed via GNM AI Chat on behalf of Glen Casanova — {timestamp}*"
    )


def create_issue(title: str, body: str, labels: list[str] | None = None) -> dict:
    """
    Open a GitHub issue.

    labels defaults to ["from-chat", "bug"]; pass an explicit list to override
    (must be labels that already exist in the repo, or the API path 422s).

    Returns:
        {"ok": True,  "url": "https://github.com/..."}
        {"ok": False, "url": None, "error": "..."}
    """
    labels = labels if labels is not None else _LABELS
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full_body = body + _footer(timestamp)

    if config.GITHUB_TOKEN:
        return _create_via_api(title, full_body, labels)
    return _create_via_cli(title, full_body, labels)


def _create_via_api(title: str, body: str, labels: list[str]) -> dict:
    url = f"https://api.github.com/repos/{config.GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"title": title, "body": body, "labels": labels}
    try:
        resp = httpx.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 201:
            return {"ok": True, "url": resp.json().get("html_url")}
        # 422 often means labels don't exist in the repo yet
        return {
            "ok": False,
            "url": None,
            "error": f"GitHub API returned {resp.status_code}: {resp.text[:300]}",
        }
    except Exception as exc:
        return {"ok": False, "url": None, "error": str(exc)}


def _create_via_cli(title: str, body: str, labels: list[str]) -> dict:
    """Fallback: use the authenticated `gh` CLI."""
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--repo",
                config.GITHUB_REPO,
                "--title",
                title,
                "--body",
                body,
                "--label",
                ",".join(labels),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            # gh prints the issue URL as the last line of stdout
            url = result.stdout.strip().splitlines()[-1].strip()
            if url.startswith("https://"):
                return {"ok": True, "url": url}
            return {"ok": True, "url": url or None}
        return {
            "ok": False,
            "url": None,
            "error": f"gh CLI error: {result.stderr.strip()[:300]}",
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "url": None,
            "error": "gh CLI not found and no GITHUB_TOKEN is set.",
        }
    except Exception as exc:
        return {"ok": False, "url": None, "error": str(exc)}
