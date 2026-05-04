# Phase 9: Self-Improvement Automation

## Goal

Add a deterministic self-improvement workflow that reviews ticket status, implementation reports, validation evidence, and mistake records.

## Scope

- Read ticket status through the Phase 8 tracker.
- Read validation sections from `.agents/reports/*.md`.
- Read mistake records from `.agents/mistakes/*.md`.
- Generate a local self-improvement review with recommendations.
- Optionally write the review to `.agents/reports/self-improvement-review.md`.

## Tickets

- `TKT-P9-001`: Mistake record discovery and section extraction.
- `TKT-P9-002`: Report validation evidence scanner.
- `TKT-P9-003`: Self-improvement review builder and renderer.
- `TKT-P9-004`: `agent improve` CLI command.
- `TKT-P9-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
