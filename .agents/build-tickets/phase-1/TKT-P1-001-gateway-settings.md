# TKT-P1-001: Gateway Settings Contract and Module

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/gateway/settings.py`

## Phase

Phase 1: Gateway Skeleton

## Source Docs

- `.agents/phase-plans/phase-1-gateway-skeleton.md`
- `.agents/contracts/phase-1/gateway-settings-contract.md`
- `.agents/contracts/phase-1/gateway-api-contract.md`
- `.agents/contracts/phase-1/gateway-cli-contract.md`

## User / Operator Served

Developers running a local gateway between Continue/Cursor and the local Ollama runtime.

## Pain Solved

Gateway host, port, Ollama base URL, and timeout defaults need one stable source before endpoints and CLI commands are added.

## Definition of Done

- Gateway settings dataclass or equivalent exists.
- Defaults are deterministic and testable.
- Environment or config override behavior is documented if included.
- Tests cover defaults and normalization.

## Expected Files to Change

- `src/pro_ai_server/gateway/__init__.py`
- `src/pro_ai_server/gateway/settings.py`
- `tests/test_gateway_settings.py`

## Contract Impact

- Config: defines gateway host, port, Ollama API base, and timeout.
- Model selection: carries profile defaults and explicit model overrides forward; gateway code must not hard-code one LLM.
- CLI: later gateway commands use these defaults.
- Network/security: default host must be loopback.

## Validation

- L1 lint: `ruff check .`
- L2 unit tests: `pytest tests/test_gateway_settings.py`
- L3 release: `pro-ai-server validate-release`

## Rollback Plan

Remove the new gateway package files and tests.

## Dependencies

- Phase 0.5 Build Bridge

## Follow-Up Tickets Unlocked

- TKT-P1-002
- TKT-P1-003
