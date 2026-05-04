# TKT-P19-004 Agent Session Archive CLI

## Objective

Expose session cleanup archive through the agent CLI.

## Acceptance Criteria

- `agent session-archive` previews candidates.
- `--write` applies archive cleanup.
- `--phase`, `--ticket`, `--session-file`, and `--archive` filters/paths are supported.
- `--fail-on-empty` supports automation checks.
