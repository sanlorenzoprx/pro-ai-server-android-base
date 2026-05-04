# TKT-P14-003 Execution Packet Writer

## Objective

Write execution packets to a deterministic local path.

## Acceptance Criteria

- Default output path is `.agents/execution/{ticket}.execution.md`.
- Parent directories are created as needed.
- Writes are explicit and do not happen during preview.
