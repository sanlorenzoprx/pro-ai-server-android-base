# Phase 9 Self-Improvement Contract

## Commands

```powershell
pro-ai-server agent improve
pro-ai-server agent improve --phase phase-9
pro-ai-server agent improve --write
pro-ai-server agent improve --write --output .agents/reports/custom-review.md
```

## Inputs

- Ticket status from `.agents/build-tickets/**/*.md` and `.agents/reports/*.md`.
- Validation evidence from report `## Validation Results` or `## Validation` sections.
- Mistake records from `.agents/mistakes/*.md`.

## Output

- Markdown review printed to stdout by default.
- Optional written review at `.agents/reports/self-improvement-review.md`.

## Constraints

- Do not call an LLM.
- Do not require network access.
- Keep recommendations deterministic and derived from local evidence.
