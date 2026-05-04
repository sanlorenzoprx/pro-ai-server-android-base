# Phase 1: Gateway Skeleton

## Goal

Create the first local gateway layer for Pro CodeFlow Server without building the full Ollama proxy yet.

The gateway should establish stable settings, route selection, health reporting, basic model metadata, route testing, CLI entry points, docs, and validation patterns.

## Non-Goals

- Do not implement full `/api/chat` or `/api/generate` proxy behavior.
- Do not add codebase RAG.
- Do not add autonomous agent implementation commands.
- Do not change existing Android setup, Continue config, tunnel, status, or diagnostics behavior.

## Build Tickets

| Ticket | Title | Depends On |
|---|---|---|
| TKT-P1-001 | Gateway settings contract and module | Phase 0.5 |
| TKT-P1-002 | Model route selection | TKT-P1-001 |
| TKT-P1-003 | Gateway health endpoint | TKT-P1-001 |
| TKT-P1-004 | Gateway models endpoint | TKT-P1-001, TKT-P1-002 |
| TKT-P1-005 | Route-test endpoint | TKT-P1-002 |
| TKT-P1-006 | Gateway CLI start/status commands | TKT-P1-003 |
| TKT-P1-007 | Gateway CLI route-test command | TKT-P1-005 |
| TKT-P1-008 | Gateway docs, smoke test, and report | TKT-P1-001 through TKT-P1-007 |

## Required Contracts

- `.agents/contracts/phase-1/gateway-api-contract.md`
- `.agents/contracts/phase-1/gateway-settings-contract.md`
- `.agents/contracts/phase-1/model-routing-contract.md`
- `.agents/contracts/phase-1/gateway-cli-contract.md`
- `.agents/contracts/phase-1/gateway-validation-contract.md`

## Validation

Default validation:

```bash
ruff check .
pytest
pro-ai-server validate-release
```

Gateway-specific validation after implementation:

```bash
pro-ai-server gateway-route-test --task chat
curl http://localhost:8765/health
```

## Closeout Criteria

- All Phase 1 build tickets are complete.
- Gateway contracts are updated if implementation changed them.
- Unit tests cover settings, route selection, endpoints, and CLI command routing.
- Manual smoke test evidence is recorded.
- Implementation report exists in `.agents/reports/`.
- Any failures have mistake records or rule updates.
