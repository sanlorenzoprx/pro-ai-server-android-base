# TKT-P20-006: Simple Windows Installer UI

## Target Repo

Pro AI Server

## Target Area

New UI wrapper over the production installer state machine

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/installer-ui-contract.md`

## User / Operator Served

Non-technical customers who need guided setup.

## Pain Solved

The CLI can be production-ready but still intimidating. The first UI should make the setup state obvious without creating a separate installer logic path.

## Definition of Done

- UI calls the same installer state machine as CLI.
- UI has screens for checklist, detection, hardware scan, install progress, test prompt, IDE prompt, receipt, and recoverable errors.
- UI can run a mocked dry-run flow without a phone.
- Advanced network modes are not shown during first-run setup.
- Docs explain how to launch and troubleshoot the UI.

## Expected Files to Change

- New UI package or wrapper files
- `src/pro_ai_server/setup_workflow.py`
- UI docs
- UI smoke tests or mocked flow tests

## Validation

- `ruff check .`
- Relevant UI/state-machine tests
- Manual smoke: mocked no-phone flow and real USB phone flow

## Dependencies

- TKT-P20-005

## Follow-Up Tickets Unlocked

- TKT-P20-007

