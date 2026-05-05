# TKT-P22-003: Live Continue IDE Validation

## Target Repo

Pro Agentic Coding Server

## Target Area

VS Code / Cursor live validation

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/ide-live-validation-contract.md`

## User / Operator Served

Founder/operator proving the DevStack coding assistant inside an IDE.

## Pain Solved

The launch claim depends on Continue chat and coding assistance working against the local phone endpoint.

## Definition of Done

- VS Code or Cursor readiness is recorded.
- Continue extension presence is recorded.
- DevStack config points to `http://localhost:11434`.
- One chat prompt receives a local response.
- One autocomplete or coding assistance moment is recorded.
- Low-RAM or latency caveats are documented.

## Expected Files to Change

- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-003-report.md`

## Validation

- `pro-ai-server devstack-ide-status`
- `pro-ai-server configure-devstack`
- Manual Continue chat
- Manual autocomplete or code assistance proof

## Dependencies

- TKT-P22-001
- TKT-P22-002

## Follow-Up Tickets Unlocked

- TKT-P22-004
