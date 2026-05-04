# Contract: Proxy Validation

## Phase

Phase 2: Ollama Proxy

## Required Checks

```bash
ruff check .
pytest
pro-ai-server validate-release
```

## Required Tests

- Ollama client success path.
- Ollama client unavailable/timeout/error paths.
- `/api/tags` proxy response.
- `/api/generate` injects configurable model when missing.
- `/api/chat` injects configurable model when missing.
- Streaming requests return structured `unsupported_streaming` errors.

