# TKT-P2-004: Proxy POST /api/chat

## Target Area

`src/pro_ai_server/gateway/app.py`

## Definition of Done

- `POST /api/chat` proxies non-streaming JSON to Ollama.
- If no model is provided, the gateway injects the settings-backed selected model.
- Streaming requests return `unsupported_streaming`.
- Tests cover custom model configuration.

