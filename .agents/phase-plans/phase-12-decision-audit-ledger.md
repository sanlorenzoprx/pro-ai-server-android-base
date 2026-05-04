# Phase 12: Decision Audit Ledger

## Goal

Add append-only decision history while preserving the current-state ticket decision queue.

## Scope

- Store decision events in `.agents/queue/ticket-decisions.jsonl`.
- Keep `.agents/queue/ticket-decisions.json` as the latest current-state view.
- Add a history renderer and CLI command.
- Keep output deterministic and local.

## Tickets

- `TKT-P12-001`: Decision event model and JSONL loader.
- `TKT-P12-002`: Append-only event writer.
- `TKT-P12-003`: Current-state derivation from event history.
- `TKT-P12-004`: `agent history` CLI command.
- `TKT-P12-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
