"""
GNM Otter.ai Client
Pulls transcripts from Otter.ai using their unofficial API.
Credentials stay local in .env. Session tokens are in-memory only.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://otter.ai/forward/api/v1"
AUTH_BASE = "https://otter.ai/forward/api/v2"

OTTER_EMAIL = os.getenv("OTTER_EMAIL", "")
OTTER_PASSWORD = os.getenv("OTTER_PASSWORD", "")


class OtterClient:
    """Minimal Otter.ai client — login, list speeches, pull transcript text."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        })
        self.userid = None
        self._csrf_token = None

    def login(self, email: str = None, password: str = None) -> bool:
        """Authenticate with Otter.ai. Returns True on success."""
        email = email or OTTER_EMAIL
        password = password or OTTER_PASSWORD

        if not email or not password:
            raise ValueError("OTTER_EMAIL and OTTER_PASSWORD must be set in .env")

        resp = self.session.get(f"{AUTH_BASE}/login_with_email", params={
            "username": email,
        })

        # Now post credentials
        resp = self.session.post(f"{AUTH_BASE}/login_with_email", json={
            "username": email,
            "password": password,
        })

        if resp.status_code != 200:
            raise ConnectionError(f"Otter login failed: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        self.userid = data.get("userid") or data.get("user", {}).get("userid")

        # Grab CSRF token from cookies
        for cookie in self.session.cookies:
            if cookie.name == "csrftoken":
                self._csrf_token = cookie.value
                self.session.headers["x-csrftoken"] = cookie.value
                break

        if not self.userid:
            raise ConnectionError("Login succeeded but no userid returned")

        print(f"  Otter login OK (user: {self.userid})")
        return True

    def get_speeches(self, page_size: int = 20) -> list[dict]:
        """Get list of recent speeches/transcripts."""
        resp = self.session.get(f"{API_BASE}/speeches", params={
            "userid": self.userid,
            "page_size": page_size,
        })
        resp.raise_for_status()
        data = resp.json()
        return data.get("speeches", [])

    def get_speech(self, speech_id: str) -> dict:
        """Get full speech details including transcript."""
        resp = self.session.get(f"{API_BASE}/speech", params={
            "userid": self.userid,
            "otid": speech_id,
        })
        resp.raise_for_status()
        return resp.json().get("speech", {})

    def get_transcript_text(self, speech: dict) -> str:
        """Extract plain text from a speech object's transcript data."""
        transcripts = speech.get("transcripts", [])
        if not transcripts:
            # Try the text field directly
            return speech.get("text", "")

        lines = []
        for entry in transcripts:
            speaker = entry.get("speaker_name", "Speaker")
            text = entry.get("transcript", "")
            if text:
                lines.append(f"{speaker}: {text}")

        return "\n".join(lines)

    def download_transcript(self, speech_id: str, fmt: str = "txt") -> str:
        """Download transcript in specified format. Returns text content."""
        resp = self.session.get(f"{API_BASE}/speech/export", params={
            "otid": speech_id,
            "format": fmt,
        })
        resp.raise_for_status()
        return resp.text


class OtterPoller:
    """
    Polls Otter.ai for new transcripts and saves them locally.
    Tracks which speeches have already been pulled via a state file.
    """

    def __init__(self, output_dir: Path, state_file: Path = None):
        self.client = OtterClient()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = state_file or (output_dir / ".otter_state.json")
        self.pulled_ids = self._load_state()

    def _load_state(self) -> set:
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            return set(data.get("pulled_ids", []))
        return set()

    def _save_state(self):
        data = {"pulled_ids": list(self.pulled_ids), "last_poll": time.time()}
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def poll(self) -> list[Path]:
        """
        Check for new transcripts. Downloads any not previously pulled.
        Returns list of saved file paths.
        """
        self.client.login()
        speeches = self.client.get_speeches(page_size=50)

        new_files = []
        for speech in speeches:
            speech_id = str(speech.get("otid", ""))
            if not speech_id or speech_id in self.pulled_ids:
                continue

            title = speech.get("title", "untitled")
            created = speech.get("created_at") or speech.get("start_time")
            if created:
                # Otter uses epoch seconds
                try:
                    dt = datetime.fromtimestamp(float(created))
                    date_str = dt.strftime("%Y-%m-%d")
                except (ValueError, TypeError, OSError):
                    date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")

            # Clean filename
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title).strip()
            safe_title = safe_title[:80] or "transcript"
            filename = f"{date_str}-{safe_title}.txt"

            # Pull full transcript
            print(f"  Pulling: {title} ({speech_id})")
            try:
                full_speech = self.client.get_speech(speech_id)
                text = self.client.get_transcript_text(full_speech)

                if not text.strip():
                    # Fallback: try export endpoint
                    text = self.client.download_transcript(speech_id, "txt")

                if text.strip():
                    out_path = self.output_dir / filename
                    out_path.write_text(text, encoding="utf-8")
                    new_files.append(out_path)
                    print(f"    Saved: {out_path}")
                else:
                    print(f"    SKIP: empty transcript")

            except Exception as e:
                print(f"    ERROR pulling {speech_id}: {e}")
                continue

            self.pulled_ids.add(speech_id)

        self._save_state()
        return new_files
