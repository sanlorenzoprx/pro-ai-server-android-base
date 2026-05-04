# Contract: Gateway Settings

## Phase

Phase 1: Gateway Skeleton

## Purpose

Define the gateway configuration surface before HTTP endpoints and CLI commands are added.

## Settings

| Setting | Default | Rule |
|---|---|---|
| host | `127.0.0.1` | Loopback by default |
| port | `8765` | Integer from 1 to 65535 |
| ollama_api_base | `http://localhost:11434` | Must be HTTP or HTTPS URL |
| timeout_seconds | `30` | Must be greater than zero |
| model_profile | `professional` | Must be a known profile from `models.py` |
| chat_model | profile default | Optional override |
| autocomplete_model | profile default | Optional override |

## Environment Overrides

The settings layer may read:

- `PRO_AI_GATEWAY_HOST`
- `PRO_AI_GATEWAY_PORT`
- `PRO_AI_GATEWAY_OLLAMA_API_BASE`
- `PRO_AI_GATEWAY_TIMEOUT_SECONDS`
- `PRO_AI_GATEWAY_MODEL_PROFILE`
- `PRO_AI_GATEWAY_CHAT_MODEL`
- `PRO_AI_GATEWAY_AUTOCOMPLETE_MODEL`

## LLM Selection Rule

The gateway must not hard-code one LLM as the only supported model. Defaults may come from `src/pro_ai_server/models.py`, but users must be able to override model names through settings.

## Validation

- Unit tests cover defaults.
- Unit tests cover normalization.
- Unit tests cover custom model overrides.
- Unit tests cover invalid values.

