# Phase 16 Session-Aware Next Action Contract

## Commands

```powershell
pro-ai-server agent next-action --phase phase-16
pro-ai-server agent next-action --phase phase-16 --session-policy resume
pro-ai-server agent next-action --phase phase-16 --session-policy all
pro-ai-server agent packet --phase phase-16
pro-ai-server agent packet --phase phase-16 --session-policy resume
```

## Inputs

- Ready handoff tickets from accepted decisions and reports.
- Current work sessions from `.agents/execution/work-sessions.json`.
- Optional custom paths from `--queue` and `--session-file`.

## Rules

- Reports still close tickets; session state only affects selection while a ticket is unreported.
- `available` is the default policy: skip `finished` sessions and prefer tickets with no session.
- `resume` prioritizes `picked-up` and `started` sessions before tickets with no session.
- `all` includes finished session tickets for audit/recovery.
- Selection remains deterministic by policy rank, phase, and ticket ID.
