# Phase 13 Accepted Ticket Handoff Contract

## Commands

```powershell
pro-ai-server agent handoff
pro-ai-server agent handoff --phase phase-13
pro-ai-server agent handoff --ticket TKT-P13-001
pro-ai-server agent handoff --include-reported
```

## Inputs

- Tickets from `.agents/build-tickets/**/*.md`.
- Decisions from `.agents/queue/ticket-decisions.json`.
- Reports from `.agents/reports/*.md`.

## Rules

- Only `accepted` decisions are eligible.
- Reported tickets are excluded by default.
- `--include-reported` includes accepted tickets with implementation reports.
- No implementation work is executed automatically.
