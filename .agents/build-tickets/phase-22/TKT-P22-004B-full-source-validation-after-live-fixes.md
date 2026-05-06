# TKT-P22-004B: Full Source Validation After Live Hardware Fixes

## Target Repo

Pro AI Server and Pro Agentic Coding Server

## Target Area

Quality gates after Moto RC fixes

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/contracts/phase-22/release-evidence-contract.md`
- `docs/PRODUCTION_RC.md`

## User / Operator Served

Founder/operator deciding whether the source tree is ready for packaged RC smoke.

## Pain Solved

The live smoke changed tunnel direction and phone bootstrap ordering. Full gates must pass before rebuilding the packaged executable.

## Definition of Done

- `pytest` passes.
- `ruff check .` passes.
- `pro-ai-server validate-release` passes.
- Results are recorded in a TKT-P22-004B report.

## Expected Files to Change

- `.agents/reports/TKT-P22-004B-report.md`
- `docs/PRODUCTION_RC.md` if validation evidence needs updating

## Validation

- `pytest`
- `ruff check .`
- `pro-ai-server validate-release`

## Dependencies

- TKT-P22-004A

## Follow-Up Tickets Unlocked

- TKT-P22-004C
