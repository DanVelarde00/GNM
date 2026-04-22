"""
Manages the background processor subprocess (run_watch_subprocess.py).
Captures stdout for streaming to frontend via WebSocket.
"""

import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class ProcessManager:
    _instance = None

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._log: deque[dict] = deque(maxlen=500)
        self._reader_thread: threading.Thread | None = None
        self._start_time: float | None = None
        self._lock = threading.Lock()
        # Subscribers: list of asyncio.Queue for WebSocket push
        self._subscribers: list = []

    @classmethod
    def instance(cls) -> "ProcessManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self):
        with self._lock:
            if self.running:
                return
            self._proc = subprocess.Popen(
                [sys.executable, "-u", str(PROJECT_ROOT / "run_watch_subprocess.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(PROJECT_ROOT),
            )
            self._start_time = time.time()
            self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self._reader_thread.start()
            self._add_log("[GNM Dashboard] Processor started")

    def stop(self):
        with self._lock:
            if self._proc:
                self._add_log("[GNM Dashboard] Stopping processor...")
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                self._proc = None
                self._add_log("[GNM Dashboard] Processor stopped")

    def restart(self):
        self.stop()
        self.start()

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "pid": self._proc.pid if self.running else None,
            "uptime_seconds": int(time.time() - self._start_time) if self._start_time and self.running else 0,
        }

    def get_recent_log(self, n: int = 100) -> list[dict]:
        return list(self._log)[-n:]

    def subscribe(self, queue):
        self._subscribers.append(queue)

    def unsubscribe(self, queue):
        try:
            self._subscribers.remove(queue)
        except ValueError:
            pass

    def _add_log(self, msg: str):
        entry = {"ts": time.time(), "msg": msg}
        self._log.append(entry)
        for q in self._subscribers[:]:
            try:
                q.put_nowait(entry)
            except Exception:
                pass

    def _read_output(self):
        try:
            for line in self._proc.stdout:
                self._add_log(line.rstrip())
        except Exception:
            pass
