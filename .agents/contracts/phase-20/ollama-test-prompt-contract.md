# Contract: Ollama Test Prompt

## Phase

Phase 20: Production Installer Hardening

## Purpose

Verify that setup produced a working local AI endpoint, not just installed files.

## Required Behavior

- Send a short deterministic prompt through the configured API base.
- Use the selected chat model unless an explicit test model is provided.
- Treat valid JSON with non-empty generated text as success.
- Treat connection failures, missing model, invalid JSON, and empty output as actionable failures.
- Keep the prompt small enough for low-RAM phones.

## Suggested Prompt

`Reply with exactly: pro-ai-server-ready`

## Validation

- Unit tests cover success, connection failure, invalid JSON, missing model, and empty response.
- CLI tests cover success and failure messaging.
- Manual smoke records test prompt evidence.

