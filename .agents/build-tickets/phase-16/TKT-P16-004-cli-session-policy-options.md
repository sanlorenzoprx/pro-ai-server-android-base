# TKT-P16-004 CLI Session Policy Options

## Objective

Expose session-aware selection controls through the agent CLI.

## Acceptance Criteria

- `agent next-action` accepts `--session-policy`.
- `agent packet` accepts `--session-policy`.
- Both commands accept `--session-file` for testability and recovery.
- Invalid policy values fail with a clear message.
