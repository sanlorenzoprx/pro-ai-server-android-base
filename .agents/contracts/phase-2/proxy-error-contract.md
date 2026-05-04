# Contract: Proxy Errors

## Phase

Phase 2: Ollama Proxy

## Error Shape

```json
{
  "error": "ollama_unavailable",
  "message": "Ollama is not reachable.",
  "upstream": "http://localhost:11434"
}
```

## Error Codes

- `bad_request`
- `unsupported_streaming`
- `ollama_unavailable`
- `ollama_timeout`
- `ollama_http_error`
- `invalid_ollama_response`

## HTTP Status Mapping

- Bad JSON: `400`
- Streaming requested in Phase 2: `400`
- Ollama unavailable or timeout: `502`
- Ollama HTTP error: same upstream status if available, otherwise `502`
- Invalid Ollama response: `502`

