# TKT-P1-004: Gateway Models Endpoint

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

Developers inspecting which local coding models the gateway knows how to route to.

## Pain Solved

The gateway needs a model inventory view before it can become the Continue/Cursor-facing model router.

## Definition of Done

- `GET /models` returns stable JSON from configured route metadata.
- Response does not require a real Ollama server in Phase 1.
- Tests cover response shape.

## Expected Files to Change

- `src/pro_ai_server/gateway/app.py`
- `src/pro_ai_server/gateway/router.py`
- `tests/test_gateway_health.py` or `tests/test_gateway_models.py`

## Contract Impact

- Endpoint: `GET /models`
- Schema: model route inventory response

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_gateway_router.py tests/test_gateway_health.py`
- L3 release: `pro-ai-server validate-release`

## Rollback Plan

Remove `/models` endpoint and associated tests.

## Dependencies

- TKT-P1-001
- TKT-P1-002

## Follow-Up Tickets Unlocked

- Phase 2 Ollama proxy model inventory

