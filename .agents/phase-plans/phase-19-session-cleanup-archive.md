# Phase 19: Session Cleanup Archive

## Goal

Archive finished reported sessions out of current autopilot state while preserving append-only history.

## Scope

- Identify archive candidates from reconciliation warnings.
- Only archive `finished-session-reported` sessions.
- Preview archive candidates by default.
- With explicit write, remove archived sessions from current state.
- Append archived session records to a separate archive JSONL.
- Keep work-session event history untouched.

## Tickets

- `TKT-P19-001`: Session archive model and candidate selection.
- `TKT-P19-002`: Archive writer and current-state cleanup.
- `TKT-P19-003`: Archive renderer.
- `TKT-P19-004`: `agent session-archive` CLI command.
- `TKT-P19-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
