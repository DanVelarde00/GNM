"""
Subprocess wrapper for the GNM watch loop.
Patches the system prompt with active tracker definitions before starting.
Run by ProcessManager — do not run directly.
"""

import sys
sys.stdout.reconfigure(line_buffering=True)

print("[GNM] Starting processor subprocess...")

# Inject tracker-aware system prompt
try:
    from api.services.tracker_service import load_trackers, build_dynamic_system_prompt
    import processor

    trackers = load_trackers()
    active = [t for t in trackers if t.active]
    if active:
        processor.SYSTEM_PROMPT = build_dynamic_system_prompt(processor.SYSTEM_PROMPT)
        print(f"[GNM] Loaded {len(active)} active tracker(s) into system prompt")
    else:
        print("[GNM] No active trackers")
except Exception as e:
    print(f"[GNM] Warning: tracker prompt injection failed: {e}")

from run import run_watch
run_watch()
