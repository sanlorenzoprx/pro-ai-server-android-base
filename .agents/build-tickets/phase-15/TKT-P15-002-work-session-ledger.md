# TKT-P15-002 Work Session Ledger

## Objective

Persist work-session events as an append-only local ledger.

## Acceptance Criteria

- Events are appended to `.agents/execution/work-sessions.jsonl`.
- Current state is saved to `.agents/execution/work-sessions.json`.
- Latest event per ticket determines current status.
- Writes create parent directories as needed.
