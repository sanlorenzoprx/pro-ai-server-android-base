# TKT-P1-003: Gateway Health Endpoint

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/gateway/app.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/gateway-api-contract.md`

## User / Operator Served

Developers and status checks that need to know whether the gateway process is alive.

## Pain Solved

The gateway needs a stable health contract before proxying or agent workflows are layered on top.

## Definition of Done

- `GET /health` returns stable JSON.
- Response includes service name, status, version, and settings summary safe for logs.
- Tests verify endpoint behavior without a real Ollama server.

## Expected Files to Change

- `src/pro_ai_server/gateway/app.py`
- `src/pro_ai_server/gateway/schemas.py`
- `tests/test_gateway_health.py`

## Contract Impact

- Endpoint: `GET /health`
- Schema: health response

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_gateway_health.py`
- L3 smoke later: `curl http://localhost:8765/health`

## Rollback Plan

Remove endpoint implementation and tests.

## Dependencies

- TKT-P1-001

## Follow-Up Tickets Unlocked

- TKT-P1-006

