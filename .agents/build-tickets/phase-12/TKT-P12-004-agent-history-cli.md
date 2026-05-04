# TKT-P12-004 Agent History CLI

## Objective

Expose decision audit history through the agent CLI group.

## Acceptance Criteria

- `pro-ai-server agent history` renders event count and rows.
- `--ledger` supports custom JSONL paths.
- Empty history renders a deterministic empty table.
