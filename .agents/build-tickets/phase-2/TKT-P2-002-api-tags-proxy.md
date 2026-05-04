# TKT-P2-002: Proxy GET /api/tags

## Target Area

`src/pro_ai_server/gateway/app.py`

## Definition of Done

- `GET /api/tags` proxies to Ollama.
- Success returns upstream JSON.
- Connection failures return structured errors.
- Unit tests do not need real Ollama.

