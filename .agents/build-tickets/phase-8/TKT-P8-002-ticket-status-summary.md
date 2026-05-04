# TKT-P8-002 Ticket Status Summary

## Objective

Build a local status summary from discovered tickets and reports.

## Acceptance Criteria

- Tickets with matching reports are marked `reported`.
- Tickets without reports are marked `planned`.
- Reports without matching tickets are marked `orphan-report`.
- Phase filtering is supported.
