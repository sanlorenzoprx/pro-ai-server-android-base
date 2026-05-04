# TKT-P1-005: Route-Test Endpoint

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/gateway/app.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/gateway-api-contract.md`
- `.agents/contracts/phase-1/model-routing-contract.md`

## User / Operator Served

Developers verifying that task routing chooses the expected model before wiring Continue/Cursor traffic through the gateway.

## Pain Solved

Routing should be inspectable through an endpoint, not hidden inside implementation details.

## Definition of Done

- `POST /route-test` accepts a task type and optional prompt.
- Response includes selected route and model metadata.
- Unknown task types return the safe fallback route.
- Tests cover known and unknown task routing.

## Expected Files to Change

- `src/pro_ai_server/gateway/app.py`
- `src/pro_ai_server/gateway/schemas.py`
- `tests/test_gateway_router.py`
- `tests/test_gateway_health.py` or `tests/test_gateway_route_test.py`

## Contract Impact

- Endpoint: `POST /route-test`
- Schema: route-test request and response

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_gateway_router.py`
- L3 manual later: `pro-ai-server gateway-route-test --task chat`

## Rollback Plan

Remove `/route-test` endpoint and tests.

## Dependencies

- TKT-P1-002

## Follow-Up Tickets Unlocked

- TKT-P1-007

