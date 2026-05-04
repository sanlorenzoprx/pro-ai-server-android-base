# TKT-P16-001 Session-Aware Selector Policy

## Objective

Apply current work-session state to next-action selection.

## Acceptance Criteria

- Default selection skips finished session tickets.
- Default selection prefers tickets without active sessions.
- Resume selection prioritizes picked-up and started tickets.
- All selection can include finished session tickets.
