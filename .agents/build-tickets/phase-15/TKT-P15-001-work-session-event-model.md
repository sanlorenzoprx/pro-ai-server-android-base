# TKT-P15-001 Work Session Event Model

## Objective

Model ticket work-session events for packet consumption and implementation progress.

## Acceptance Criteria

- Valid events are `picked-up`, `started`, and `finished`.
- CLI-friendly aliases normalize to valid events.
- Session records include ticket ID, note, sequence, phase, ticket path, and packet path when available.
