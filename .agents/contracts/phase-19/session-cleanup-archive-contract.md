# Phase 19 Session Cleanup Archive Contract

## Commands

```powershell
pro-ai-server agent session-archive
pro-ai-server agent session-archive --phase phase-19
pro-ai-server agent session-archive --ticket TKT-P19-001
pro-ai-server agent session-archive --phase phase-19 --write
```

## Inputs

- Current sessions from `.agents/execution/work-sessions.json`.
- Reconciliation warnings from tickets, reports, and current sessions.

## Outputs

- Archive preview table by default.
- With `--write`, updated current sessions JSON.
- With `--write`, archive records appended to `.agents/execution/archived-work-sessions.jsonl`.

## Rules

- Only `finished-session-reported` sessions are archive candidates.
- Finished unreported sessions must be reported before archive.
- Active reported sessions must be finished or reconciled before archive.
- Work-session history JSONL is never modified.
