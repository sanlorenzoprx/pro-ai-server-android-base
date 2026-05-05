# TKT-P22-001: Production Hardware Smoke Matrix

## Target Repo

Pro AI Server and Pro Agentic Coding Server

## Target Area

Hardware validation docs and smoke evidence

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/hardware-smoke-contract.md`

## User / Operator Served

Founder/operator validating the first production phone path.

## Pain Solved

The project needs real-device proof before release-candidate packaging and customer demos.

## Definition of Done

- Hardware smoke matrix records phone model, Android version, serial handling, RAM profile, selected models, and result.
- Smoke steps cover ADB, USB debugging, setup execution, Termux readiness, script push, tunnel, status, model inventory, and test prompt.
- Failure/recovery notes are captured.
- Matrix clearly separates completed, blocked, and skipped checks.

## Expected Files to Change

- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001-report.md`

## Validation

- Docs review
- Manual: `scripts/smoke-production-installer.ps1 -WithPhone`
- Manual: `pro-ai-server test-prompt`

## Dependencies

- Phase 20 installer
- Phase 21 DevStack docs

## Follow-Up Tickets Unlocked

- TKT-P22-002
- TKT-P22-003
