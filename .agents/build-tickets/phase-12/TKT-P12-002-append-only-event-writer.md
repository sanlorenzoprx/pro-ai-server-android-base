# TKT-P12-002 Append Only Event Writer

## Objective

Append decision events without rewriting history.

## Acceptance Criteria

- Each decision appends one JSON object line.
- Event payloads use sorted JSON keys.
- Parent directories are created as needed.
