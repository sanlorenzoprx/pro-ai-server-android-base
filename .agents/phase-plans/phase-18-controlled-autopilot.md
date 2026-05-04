# Phase 18: Controlled Agent Autopilot

## Goal

Add a controlled autopilot preflight and one-ticket loop command that uses reconciliation, next-action selection, packet generation, sessions, validation gates, and report gates.

## Scope

- Run reconciliation before any packet or session write.
- Select the next ready ticket with existing session-aware policy.
- Preview by default with no writes.
- With explicit execution, write the packet and optionally record session pickup/start.
- Stop after packet/session setup so implementation, validation, and reporting remain explicit gates.
- Surface strict stop reasons.

## Tickets

- `TKT-P18-001`: Autopilot result model and stop reasons.
- `TKT-P18-002`: Reconciliation and next-action preflight.
- `TKT-P18-003`: Packet and session execution actions.
- `TKT-P18-004`: `agent autopilot` CLI command.
- `TKT-P18-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
