# TKT-P16-003 Session-Aware Packet Generation

## Objective

Make execution packet generation use the same session-aware selector as next-action.

## Acceptance Criteria

- Packet preview and write skip finished sessions by default.
- Packet preview and write can prioritize active sessions with resume policy.
- Packet metadata includes session status.
