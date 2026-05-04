# TKT-P11-002 Decision Queue Persistence

## Objective

Read and write local ticket decisions.

## Acceptance Criteria

- Decisions are stored under `.agents/queue/ticket-decisions.json`.
- Recording a decision updates the current decision for that ticket.
- JSON output is deterministic.
