# Phase 17 Session Report Reconciliation Contract

## Commands

```powershell
pro-ai-server agent reconcile
pro-ai-server agent reconcile --phase phase-17
pro-ai-server agent reconcile --ticket TKT-P17-001
pro-ai-server agent reconcile --fail-on-warning
```

## Inputs

- Current work sessions from `.agents/execution/work-sessions.json`.
- Tickets from `.agents/build-tickets/**/*.md`.
- Reports from `.agents/reports/*.md`.

## Warning Codes

- `active-session-reported`: picked-up or started session has an implementation report.
- `finished-session-reported`: finished session has an implementation report and may be cleaned up.
- `finished-session-unreported`: finished session does not have an implementation report.
- `orphan-session`: session references a ticket file that no longer exists.

## Rules

- Reconciliation is read-only.
- Reports remain the implementation closeout artifact.
- Session state remains the work-progress artifact.
- `--fail-on-warning` exits nonzero when any warning exists.
