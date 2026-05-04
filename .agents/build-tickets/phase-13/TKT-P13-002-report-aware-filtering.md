# TKT-P13-002 Report Aware Filtering

## Objective

Filter implementation handoff items using report evidence.

## Acceptance Criteria

- Accepted tickets without reports are `ready`.
- Accepted tickets with reports are `reported`.
- Reported tickets are excluded by default.
- `--include-reported` includes reported items.
