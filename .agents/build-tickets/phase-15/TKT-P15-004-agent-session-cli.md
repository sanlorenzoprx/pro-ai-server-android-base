# TKT-P15-004 Agent Session CLI

## Objective

Expose work-session tracking through agent CLI commands.

## Acceptance Criteria

- `agent session` records a session event.
- `agent sessions` prints current session state.
- `agent session-history` prints append-only event history.
- Invalid events fail with a clear message.
