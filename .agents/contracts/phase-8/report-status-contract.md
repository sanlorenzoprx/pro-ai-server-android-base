# Phase 8 Report Status Contract

## Commands

```powershell
pro-ai-server agent report TKT-P8-001 --summary "Implemented status tracking."
pro-ai-server agent status
pro-ai-server agent status --phase phase-8
```

## Files

- Tickets are read from `.agents/build-tickets/**/*.md`.
- Reports are read from and written to `.agents/reports/*.md`.
- Generated report names use `.agents/reports/{ticket-or-slug}-report.md`.

## Status Rules

- `reported`: a matching ticket file and report file exist.
- `planned`: a ticket file exists but no matching report file exists.
- `orphan-report`: a report references a ticket ID without a matching ticket file.

## Constraints

- Do not call an LLM.
- Do not require a database or service.
- Keep output deterministic and reviewable.
