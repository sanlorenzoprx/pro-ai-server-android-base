# TKT-P1-006: Gateway CLI Start and Status Commands

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/cli.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/gateway-cli-contract.md`

## User / Operator Served

Developers starting and checking the local gateway from the existing Pro AI Server CLI.

## Pain Solved

Gateway lifecycle should fit the current CLI instead of requiring users to know framework-specific commands.

## Definition of Done

- `pro-ai-server gateway-start` starts the gateway locally.
- `pro-ai-server gateway-status` checks gateway health.
- Commands have clear errors when dependencies or the server are unavailable.
- Existing CLI behavior remains unchanged.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `tests/test_cli_workflows.py`
- possibly `pyproject.toml` if adding a web framework dependency

## Contract Impact

- CLI: `gateway-start`, `gateway-status`
- Network/security: default host remains loopback.

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_cli_workflows.py`
- L3 release: `pro-ai-server validate-release`

## Rollback Plan

Remove new CLI commands and tests.

## Dependencies

- TKT-P1-001
- TKT-P1-003

## Follow-Up Tickets Unlocked

- TKT-P1-008

