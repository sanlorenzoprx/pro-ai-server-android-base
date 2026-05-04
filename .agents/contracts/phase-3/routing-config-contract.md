# Contract: Routing Config

## Config Locations

- User: `~/.pro-ai-server/config.yaml`
- Project: `.pro-ai-server/config.yaml`

Project config overrides user config.

## Shape

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
```

## Rule

No LLM is required by code. Configured model names must flow through settings and route selection.

