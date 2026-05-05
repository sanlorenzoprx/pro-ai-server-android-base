# TKT-P22-002: Packaged Windows Exe Release-Candidate Smoke

## Target Repo

Pro AI Server

## Target Area

Windows executable release candidate

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/windows-rc-contract.md`

## User / Operator Served

Release operator building the first customer-facing Windows artifact.

## Pain Solved

The source-tree CLI passing tests is not enough; the packaged `.exe` must prove the customer path works.

## Definition of Done

- `scripts/build-windows-exe.ps1` builds the release candidate artifact.
- Packaged exe validates release files and bundled ADB.
- Packaged exe runs no-phone smoke commands.
- Packaged exe with-phone smoke is recorded when hardware is available.
- Artifact path and limitations are documented.

## Expected Files to Change

- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-002-report.md`

## Validation

- `scripts/build-windows-exe.ps1`
- `dist/pro-ai-server/pro-ai-server.exe validate-release`
- `dist/pro-ai-server/pro-ai-server.exe setup --production`
- `dist/pro-ai-server/pro-ai-server.exe status`

## Dependencies

- TKT-P22-001

## Follow-Up Tickets Unlocked

- TKT-P22-003
- TKT-P22-004
