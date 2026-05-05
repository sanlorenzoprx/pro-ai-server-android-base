# TKT-P20-001: Production Installer State Machine

## Target Repo

Pro AI Server

## Target Area

`src/pro_ai_server/setup_workflow.py`, `src/pro_ai_server/cli.py`

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/installer-state-machine-contract.md`

## User / Operator Served

Customers installing Pro AI Server on Windows with an Android phone connected over USB.

## Pain Solved

The current CLI has the needed pieces, but production setup needs one stable state machine that the CLI, packaged `.exe`, and future UI can call.

## Definition of Done

- Installer steps are represented as stable structured results.
- The production path covers host checks, phone detection, ADB, hardware scan, profile selection, Termux readiness, script generation, push, tunnel, server/model checks, test prompt placeholder, and receipt.
- Failures map to user-facing recovery guidance.
- Existing setup behavior is preserved or intentionally routed through the new orchestrator.
- Tests cover step ordering and representative failures.

## Expected Files to Change

- `src/pro_ai_server/setup_workflow.py`
- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/setup_receipt.py`
- `tests/test_setup_workflow.py`
- `tests/test_cli_workflows.py`

## Validation

- `ruff check .`
- `pytest tests/test_setup_workflow.py tests/test_cli_workflows.py`
- `pro-ai-server validate-release`

## Dependencies

- Existing setup workflow

## Follow-Up Tickets Unlocked

- TKT-P20-002
- TKT-P20-003
- TKT-P20-004

