# Pro CodeFlow Gateway

The Pro CodeFlow gateway is the local routing layer that will sit between Continue/Cursor and the configured Ollama-compatible runtime.

The gateway uses stdlib HTTP and pure routing/proxy functions. It supports the Phase 1 local endpoints plus Phase 2 non-streaming Ollama proxy endpoints.

## Defaults

| Setting | Default |
|---|---|
| Host | `127.0.0.1` |
| Port | `8765` |
| Ollama API base | `http://localhost:11434` |
| Model profile | `professional` |

Model choices are configurable. Defaults come from `src/pro_ai_server/models.py`, but users can override chat and autocomplete models.

## CLI

Start the gateway:

```powershell
pro-ai-server gateway-start
```

Check health:

```powershell
pro-ai-server gateway-status
```

Test routing:

```powershell
pro-ai-server gateway-route-test --task chat
pro-ai-server gateway-route-test --task autocomplete
pro-ai-server gateway-route-test --task refactor
```

Use custom model choices:

```powershell
pro-ai-server gateway-route-test --task chat --chat-model custom-chat:latest
pro-ai-server gateway-start --chat-model custom-chat:latest --autocomplete-model custom-auto:latest
```

Check whether configured route models are available in Ollama:

```powershell
pro-ai-server gateway-proxy-test --task chat
pro-ai-server gateway-proxy-test --all
pro-ai-server gateway-proxy-test --task security-review --config .pro-ai-server/config.yaml
```

## Config Files

Config locations:

```text
~/.pro-ai-server/config.yaml
.pro-ai-server/config.yaml
```

Project config overrides user config. CLI options override both.

Example:

```yaml
gateway:
  host: "127.0.0.1"
  port: 8765
  ollama_api_base: "http://localhost:11434"
  timeout_seconds: 30
  model_profile: "professional"
  chat_model: "custom-chat:latest"
  autocomplete_model: "custom-auto:latest"

routing:
  routes:
    chat:
      profile: "balanced"
      model: "custom-chat:latest"
      fallback_model: "qwen2.5-coder:1.5b"
    security_review:
      profile: "deep"
      model: "custom-review:latest"
      fallback_model: "custom-chat:latest"
```

Configured routes are merged after defaults. Unknown tasks still fall back to `chat`.

## Endpoints

### `GET /health`

Returns service status and safe settings summary.

### `GET /models`

Returns configured route/model metadata. Phase 1 does not require a live Ollama server for this endpoint.

### `POST /route-test`

Request:

```json
{
  "task": "chat",
  "prompt": "optional prompt text"
}
```

Response includes the selected task route, model, fallback model, and whether fallback was used.

### `GET /api/tags`

Proxies to the configured Ollama API base:

```powershell
curl http://localhost:8765/api/tags
```

### `POST /api/generate`

Proxies a non-streaming generate request:

```powershell
curl -X POST http://localhost:8765/api/generate `
  -H "Content-Type: application/json" `
  -d '{ "model": "qwen2.5-coder:3b", "prompt": "Say hello", "stream": false }'
```

If `model` is omitted, the gateway injects the settings-backed selected model.

### `POST /api/chat`

Proxies a non-streaming chat request:

```powershell
curl -X POST http://localhost:8765/api/chat `
  -H "Content-Type: application/json" `
  -d '{ "model": "qwen2.5-coder:3b", "messages": [{ "role": "user", "content": "Say hello" }], "stream": false }'
```

If `model` is omitted, the gateway injects the settings-backed selected model.

## Streaming Boundary

Streaming proxy responses are not supported yet. Requests with `"stream": true` return a structured `unsupported_streaming` error. This keeps Phase 2 honest because the current stdlib response wrapper buffers full JSON responses.

## Validation

Default checks:

```powershell
ruff check .
pytest
pro-ai-server validate-release
```

Gateway smoke:

```powershell
pro-ai-server gateway-route-test --task chat
pro-ai-server gateway-route-test --task security-review
pro-ai-server gateway-proxy-test --task chat
```

When the gateway is running:

```powershell
curl http://localhost:8765/health
curl http://localhost:8765/models
```

## Next Boundary

Future work should add streaming support and richer proxy compatibility for:

- chunked Ollama responses
- request/response logging
- model inventory reconciliation
- Continue-specific compatibility checks
