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

Session 2026-05-29: flattened vault structure, global People, PDF/Inq intake, dedup/idempotent naming, chat logs + GitHub-issue tool, Otter throttle + audio guard, model bump. ~$5.2 total.

---

## Totals

| | Input Tokens | Output Tokens | Est. Cost |
|---|---|---|---|
| **Cumulative** | ~336,000 | ~42,000 | **~$5.28** |

---

## Notes
- Update this file at the end of each working session.
- Estimate tokens from Claude's `/context` output if exact counts aren't available.
- Separate rows for sub-agent spawns if costs are significant.
