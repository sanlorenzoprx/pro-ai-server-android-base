# Phase 15 Work Session Tracking Contract

## Commands

```powershell
pro-ai-server agent session TKT-P15-001 --event picked-up --note "Taking it."
pro-ai-server agent session TKT-P15-001 --event started --note "Working."
pro-ai-server agent session TKT-P15-001 --event finished --note "Ready for report."
pro-ai-server agent sessions
pro-ai-server agent sessions --phase phase-15
pro-ai-server agent session-history
```

## Inputs

- Ticket metadata from `.agents/build-tickets/**/*.md`.
- Optional packet files from `.agents/execution/{ticket}.execution.md`.
- Work-session current state from `.agents/execution/work-sessions.json`.
- Work-session events from `.agents/execution/work-sessions.jsonl`.

## Rules

- Valid events are `picked-up`, `started`, and `finished`.
- `pickup`, `start`, and `finish` are accepted command aliases.
- Every recorded event appends one JSONL row.
- Current state is rebuilt from the latest event per ticket.
- Session tracking does not create implementation reports.
- Session writes are local single-writer operations.
