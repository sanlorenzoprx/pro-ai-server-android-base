# TKT-P22-004A: Evidence Cleanup and RC Bundle Hygiene

## Target Repo

Pro AI Server and Pro Agentic Coding Server

## Target Area

Release evidence and working tree hygiene

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/contracts/phase-22/release-evidence-contract.md`
- `docs/PRODUCTION_RC.md`

## User / Operator Served

Founder/operator, support, and launch reviewer.

## Pain Solved

Live smoke creates screenshots, logs, generated Termux files, and APK caches. The repo needs durable evidence without committing transient scratch artifacts.

## Definition of Done

- `.gitignore` ignores transient APK cache, generated Termux output, debug logs, and raw smoke screenshots.
- `docs/PRODUCTION_RC.md` records the durable evidence summary from the Moto live run.
- Any intentionally retained evidence is named clearly and referenced from the release document.
- `git status --short` shows only intended source, docs, tests, and ticket changes.

## Expected Files to Change

- `.gitignore`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-004A-report.md`

## Validation

- `git status --short`
- Docs review against release evidence contract

## Dependencies

- TKT-P22-004

## Follow-Up Tickets Unlocked

- TKT-P22-004B
