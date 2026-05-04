# Phase Ticket Handoff Runbook

Use this when starting any build ticket.

## Steps

1. Read the phase plan.
2. Read the active build ticket.
3. Read referenced contracts.
4. Check `git status`.
5. Create or confirm the implementation branch.
6. Implement only the active ticket.
7. Run ticket-specific validation.
8. Run default validation before completion.
9. Write validation evidence into an implementation report.
10. If behavior drifts from a contract, update the contract or file a follow-up ticket.

## Required Evidence

- Ticket ID
- Files changed
- Validation commands and results
- Contract changes, if any
- Follow-up tickets or mistake records, if any

