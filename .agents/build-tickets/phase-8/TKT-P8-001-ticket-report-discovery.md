# TKT-P8-001 Ticket Report Discovery

## Objective

Discover agent build tickets and implementation reports from local `.agents` files.

## Acceptance Criteria

- Ticket IDs are parsed from ticket filenames.
- Ticket phase is derived from the parent directory.
- Report ticket IDs are parsed from filenames or report body text.
- Discovery order is deterministic.
