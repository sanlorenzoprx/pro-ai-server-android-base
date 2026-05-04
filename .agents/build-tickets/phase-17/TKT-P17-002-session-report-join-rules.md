# TKT-P17-002 Session Report Join Rules

## Objective

Join sessions, tickets, and reports to detect reconciliation problems.

## Acceptance Criteria

- Active sessions with reports emit `active-session-reported`.
- Finished sessions with reports emit `finished-session-reported`.
- Finished sessions without reports emit `finished-session-unreported`.
- Sessions without matching ticket files emit `orphan-session`.
