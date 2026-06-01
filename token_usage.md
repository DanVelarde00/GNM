# GNM Project — Token Usage & Cost Tracker

Model pricing reference (as of April 2026):
- Claude Sonnet 4.6: $3.00 / 1M input tokens, $15.00 / 1M output tokens
- Claude Opus 4.6: $15.00 / 1M input tokens, $75.00 / 1M output tokens
- Claude Haiku 4.5: $0.80 / 1M input tokens, $4.00 / 1M output tokens

---

## Session Log

| Date       | Session Description              | Model   | Input Tokens | Output Tokens | Est. Cost |
|------------|----------------------------------|---------|-------------|---------------|-----------|
| 2026-04-17 | Initial planning & CLAUDE.md     | Sonnet  | ~3,000      | ~2,000        | ~$0.04    |
| 2026-04-17 | Project plan & structure design  | Sonnet  | ~5,000      | ~3,000        | ~$0.06    |
| 2026-05-29 | Sprint fixes (orchestration: Opus)| Opus    | ~180,000    | ~25,000       | ~$4.58    |
| 2026-05-29 | 3 parallel fix sub-agents        | Sonnet  | ~140,000    | ~12,000       | ~$0.60    |
| 2026-05-31 | Fix issues #5-#10 (misroute, reprocess, ForDan) | Opus | ~95,000 | ~9,000 | ~$1.16 |

Session 2026-05-29: flattened vault structure, global People, PDF/Inq intake, dedup/idempotent naming, chat logs + GitHub-issue tool, Otter throttle + audio guard, model bump. ~$5.2 total.

Session 2026-05-31: closed all 6 open GitHub issues. Fixed processor misrouting (filename project override + Calico company/project prompt disambiguation + filename-date authority); added reprocess_service (scan_missing_fields/reprocess_note/move_note) + 3 chat tools; added ForDan drop-folder → auto GitHub issue. Includes ~4 verification Claude calls (Sonnet) during testing.

---

## Totals

| | Input Tokens | Output Tokens | Est. Cost |
|---|---|---|---|
| **Cumulative** | ~431,000 | ~51,000 | **~$6.44** |

---

## Notes
- Update this file at the end of each working session.
- Estimate tokens from Claude's `/context` output if exact counts aren't available.
- Separate rows for sub-agent spawns if costs are significant.
