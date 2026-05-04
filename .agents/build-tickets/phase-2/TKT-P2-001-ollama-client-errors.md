# TKT-P2-001: Ollama Client and Structured Errors

## Target Repo

Pro CodeFlow Server

## Target Area

`src/pro_ai_server/gateway/ollama_client.py`

## Phase

Phase 2: Ollama Proxy

## Definition of Done

- Dependency-free Ollama client exists.
- Client supports JSON GET and POST.
- Unit tests mock transport and cover success/errors.
- Errors have structured code, message, status, and upstream.

## Validation

- `pytest tests/test_gateway_ollama_client.py`
- `ruff check .`
- `pytest`
- `pro-ai-server validate-release`

