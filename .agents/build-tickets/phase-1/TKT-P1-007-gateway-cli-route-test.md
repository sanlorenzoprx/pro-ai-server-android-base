# TKT-P1-007: Gateway CLI Route-Test Command

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/cli.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/gateway-cli-contract.md`
- `.agents/contracts/phase-1/model-routing-contract.md`

## User / Operator Served

Developers verifying route selection without writing raw HTTP requests.

## Pain Solved

The route-test endpoint needs an ergonomic CLI command for local diagnostics and future validation scripts.

## Definition of Done

- `pro-ai-server gateway-route-test --task chat` prints selected route and model.
- The command handles unsupported tasks through the documented fallback.
- Tests cover command routing and output.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `tests/test_cli_workflows.py`

## Contract Impact

- CLI: `gateway-route-test`
- Schema: uses route-test response contract

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_cli_workflows.py`
- L3 manual later: `pro-ai-server gateway-route-test --task chat`

## Rollback Plan

Remove CLI command and tests.

## Dependencies

- TKT-P1-005

## Follow-Up Tickets Unlocked

- TKT-P1-008

