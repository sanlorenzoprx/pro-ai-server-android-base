# TKT-P13-004 Agent Handoff CLI

## Objective

Expose implementation handoff through the agent CLI group.

## Acceptance Criteria

- `pro-ai-server agent handoff` prints accepted tickets ready for work.
- `--phase`, `--ticket`, and `--include-reported` are supported.
- Empty output is deterministic and friendly.
