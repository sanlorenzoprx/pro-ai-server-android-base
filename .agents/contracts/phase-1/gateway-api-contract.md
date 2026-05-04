# Contract: Gateway API

## Phase

Phase 1: Gateway Skeleton

## Purpose

Define the first HTTP surface for the local Pro CodeFlow Server gateway.

## Endpoints

### `GET /health`

Returns:

```json
{
  "service": "pro-codeflow-gateway",
  "status": "ok",
  "version": "0.1.0",
  "host": "127.0.0.1",
  "port": 8765
}
```

### `GET /models`

Returns configured route/model metadata. Phase 1 may return planned route metadata without contacting Ollama.

### `POST /route-test`

Request:

```json
{
  "task": "chat",
  "prompt": "optional prompt text"
}
```

Response:

```json
{
  "task": "chat",
  "profile": "balanced",
  "model": "qwen2.5-coder:3b",
  "fallback_model": "qwen2.5-coder:1.5b"
}
```

The model names above are default examples from the current model profile layer. Gateway implementation must treat selected LLMs as settings/configuration so users can choose other local or remote-compatible Ollama models later.

## Error Behavior

- Unknown tasks fall back to the default chat route and include the selected fallback behavior.
- Malformed requests return a structured validation error from the chosen web framework.
- Phase 1 does not require a live Ollama server.

## Security / Privacy

- Default bind host is `127.0.0.1`.
- Network exposure beyond loopback requires explicit future configuration.

## Validation

- Unit tests for all endpoint response shapes.
- Manual smoke: `curl http://localhost:8765/health`.
