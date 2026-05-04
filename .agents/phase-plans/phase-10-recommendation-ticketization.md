# Phase 10: Recommendation-to-Ticket Automation

## Goal

Turn accepted self-improvement recommendations into deterministic build-ticket drafts.

## Scope

- Read recommendations from `.agents/reports/self-improvement-review.md`.
- Select accepted recommendations explicitly, or all recommendations when requested.
- Preview build-ticket drafts by default.
- Write ticket drafts under `.agents/build-tickets/{phase}/` only when `--write` is passed.

## Tickets

- `TKT-P10-001`: Recommendation extraction and acceptance matching.
- `TKT-P10-002`: Ticket draft renderer and path generator.
- `TKT-P10-003`: Ticket draft writer with overwrite protection.
- `TKT-P10-004`: `agent ticketize` CLI command.
- `TKT-P10-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
