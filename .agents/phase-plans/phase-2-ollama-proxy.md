# Phase 2: Ollama Proxy

## Goal

Proxy basic non-streaming Ollama-compatible requests through the local Pro CodeFlow gateway.

## Non-Goals

- Do not implement streaming responses yet.
- Do not add FastAPI/Uvicorn unless stdlib becomes insufficient.
- Do not add codebase RAG or agent planning behavior.
- Do not remove existing Phase 1 gateway endpoints.

## Build Tickets

| Ticket | Title | Depends On |
|---|---|---|
| TKT-P2-001 | Ollama client and structured errors | Phase 1 |
| TKT-P2-002 | Proxy `GET /api/tags` | TKT-P2-001 |
| TKT-P2-003 | Proxy `POST /api/generate` | TKT-P2-001 |
| TKT-P2-004 | Proxy `POST /api/chat` | TKT-P2-001 |
| TKT-P2-005 | Proxy docs, validation, and closeout | TKT-P2-001 through TKT-P2-004 |

## Required Contracts

- `.agents/contracts/phase-2/ollama-proxy-contract.md`
- `.agents/contracts/phase-2/proxy-error-contract.md`
- `.agents/contracts/phase-2/proxy-validation-contract.md`

## Validation

```bash
ruff check .
pytest
pro-ai-server validate-release
```

Proxy smoke, when Ollama is available:

```bash
curl http://localhost:8765/api/tags
```

## Closeout Criteria

- All Phase 2 build tickets are complete.
- Proxy tests use mocks and do not require a real Ollama server.
- Non-streaming boundary is documented.
- Full validation passes.

