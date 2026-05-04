# Phase 18 Controlled Autopilot Contract

## Commands

```powershell
pro-ai-server agent autopilot --phase phase-18
pro-ai-server agent autopilot --phase phase-18 --execute
pro-ai-server agent autopilot --phase phase-18 --execute --start-session
pro-ai-server agent autopilot --phase phase-18 --fail-on-stop
```

## Inputs

- Reconciliation warnings from current sessions, tickets, and reports.
- Next-action selection from accepted unreported tickets.
- Execution packet generation.
- Optional work-session current-state and ledger paths.

## Rules

- Preview is the default and writes nothing.
- Reconciliation warnings stop autopilot before packet/session writes.
- Active picked-up or started sessions stop default autopilot before another ticket is selected.
- Use `--session-policy resume` to continue active work intentionally.
- `--execute` writes one execution packet.
- `--start-session` only works with `--execute` and records `picked-up` plus `started`.
- Autopilot stops after one selected ticket for implementation, validation, and report gates.
- It does not commit, push, or create implementation reports automatically.
