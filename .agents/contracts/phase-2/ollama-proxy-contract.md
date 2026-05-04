# Contract: Ollama Proxy

## Phase

Phase 2: Ollama Proxy

## Endpoints

- `GET /api/tags`
- `POST /api/generate`
- `POST /api/chat`

## Behavior

- Proxy requests to `GatewaySettings.ollama_api_base`.
- Preserve JSON response payloads when Ollama responds successfully.
- Use gateway timeout settings.
- Do not require a real Ollama server in unit tests.
- Reject streaming requests in Phase 2 with a structured error.

## Model Selection Rule

The proxy must not hard-code one LLM.

- If the request includes `model`, preserve it.
- If no `model` is provided for `/api/generate` or `/api/chat`, use settings-backed route selection.
- `task` or `task_type` may be used to choose a route.
- Defaults come from `src/pro_ai_server/models.py` through `GatewaySettings`.

