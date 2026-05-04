# TKT-P17-004 Agent Reconcile CLI

## Objective

Expose session/report reconciliation through the agent CLI.

## Acceptance Criteria

- `agent reconcile` prints reconciliation warnings.
- `--phase` and `--ticket` filters are supported.
- `--session-file` supports recovery and tests.
- `--fail-on-warning` exits nonzero when warnings exist.
