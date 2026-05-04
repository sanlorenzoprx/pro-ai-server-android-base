# Phase 10 Recommendation Ticketization Contract

## Commands

```powershell
pro-ai-server agent ticketize --accept "validation"
pro-ai-server agent ticketize --all
pro-ai-server agent ticketize --all --write
pro-ai-server agent ticketize --accept "optional inputs" --phase phase-11 --ticket-prefix TKT-P11 --start 3 --write
```

## Inputs

- Default review path: `.agents/reports/self-improvement-review.md`.
- Accepted items are passed through repeatable `--accept` values.
- `--all` ticketizes every recommendation in the review.

## Outputs

- Preview markdown table by default.
- Written tickets under `.agents/build-tickets/{phase}/` when `--write` is used.

## Safety

- Do not write files unless `--write` is passed.
- Refuse to overwrite existing ticket files unless `--force` is passed.
- Do not call an LLM or network service.
