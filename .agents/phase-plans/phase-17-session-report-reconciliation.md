# Phase 17: Session Report Reconciliation Warnings

## Goal

Surface mismatches between work-session state and implementation reports before autopilot continues.

## Scope

- Join current work sessions with tickets and implementation reports.
- Warn when active sessions already have reports.
- Warn when finished sessions lack reports.
- Warn when finished sessions still linger after reports exist.
- Warn when session records reference missing ticket files.
- Expose reconciliation through an agent CLI command with a fail option.

## Tickets

- `TKT-P17-001`: Reconciliation warning model.
- `TKT-P17-002`: Session/report join rules.
- `TKT-P17-003`: Reconciliation renderer.
- `TKT-P17-004`: `agent reconcile` CLI command.
- `TKT-P17-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
