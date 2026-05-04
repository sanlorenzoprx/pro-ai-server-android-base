# Contract: Gateway CLI

## Phase

Phase 1: Gateway Skeleton

## Purpose

Expose the local gateway through the existing `pro-ai-server` CLI.

## Commands

### `pro-ai-server gateway-start`

Starts the local gateway with loopback defaults.

Expected options:

- `--host`
- `--port`
- `--ollama-api-base`

### `pro-ai-server gateway-status`

Checks the configured `/health` endpoint and prints a concise readiness result.

### `pro-ai-server gateway-route-test`

Runs a route test for a task type.

Expected options:

- `--task`
- `--prompt`

## Error Behavior

- Missing optional gateway dependencies should produce a clear install message.
- Unreachable gateway status should not crash with a traceback.
- Existing CLI commands must remain unchanged.

## Validation

- CLI tests for command registration and output.
- Manual smoke after gateway implementation.

