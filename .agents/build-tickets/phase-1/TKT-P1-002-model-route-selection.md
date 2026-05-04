# TKT-P1-002: Model Route Selection

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/gateway/router.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/model-routing-contract.md`

## User / Operator Served

Developers who need predictable model choice for chat, autocomplete, refactor, test generation, and documentation tasks.

## Pain Solved

Task-to-model routing needs to be explicit before gateway endpoints depend on it.

## Definition of Done

- Router selects a route for known task types.
- Unknown task types fall back safely to chat.
- Selected route includes task type, profile, preferred model, and fallback model when available.
- Tests cover known tasks and fallback behavior.

## Expected Files to Change

- `src/pro_ai_server/gateway/router.py`
- `src/pro_ai_server/gateway/schemas.py`
- `tests/test_gateway_router.py`

## Contract Impact

- Config: uses model names from existing model profiles where possible.
- Schema: route-test response shape is defined.

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_gateway_router.py`
- L3 release: `pro-ai-server validate-release`

## Rollback Plan

Remove router module and tests before dependent endpoint tickets land.

## Dependencies

- TKT-P1-001

## Follow-Up Tickets Unlocked

- TKT-P1-004
- TKT-P1-005

