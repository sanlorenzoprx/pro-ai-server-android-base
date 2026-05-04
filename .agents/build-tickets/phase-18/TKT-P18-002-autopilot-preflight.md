# TKT-P18-002 Autopilot Preflight

## Objective

Run reconciliation and next-action selection before autopilot writes anything.

## Acceptance Criteria

- Reconciliation warnings stop autopilot.
- No ready ticket stops autopilot.
- Session-aware next-action selection is reused.
- Invalid max-ticket values stop safely.
