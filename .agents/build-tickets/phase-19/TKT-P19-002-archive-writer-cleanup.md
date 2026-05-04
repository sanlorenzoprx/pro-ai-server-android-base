# TKT-P19-002 Archive Writer Cleanup

## Objective

Archive finished reported sessions and remove them from current session state.

## Acceptance Criteria

- Archive records append to `.agents/execution/archived-work-sessions.jsonl`.
- Archived sessions are removed from `.agents/execution/work-sessions.json`.
- Work-session event history is not modified.
- Empty archive writes are safe.
