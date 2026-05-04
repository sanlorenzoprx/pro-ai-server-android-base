import pytest

from pro_ai_server.gateway.settings import (
    DEFAULT_GATEWAY_HOST,
    DEFAULT_GATEWAY_PORT,
    DEFAULT_OLLAMA_API_BASE,
    GatewaySettings,
    gateway_settings_from_env,
)


def test_gateway_settings_defaults_are_loopback_and_professional_profile():
    settings = GatewaySettings()

    assert settings.host == DEFAULT_GATEWAY_HOST
    assert settings.port == DEFAULT_GATEWAY_PORT
    assert settings.ollama_api_base == DEFAULT_OLLAMA_API_BASE
    assert settings.timeout_seconds == 30
    assert settings.model_profile == "professional"
    assert settings.chat_model == "qwen2.5-coder:3b"
    assert settings.autocomplete_model == "qwen2.5-coder:1.5b-base"


def test_gateway_settings_normalizes_values():
    settings = GatewaySettings(
        host=" 127.0.0.1 ",
        port="8766",
        ollama_api_base="http://localhost:11434/",
        timeout_seconds="12.5",
        model_profile=" MAX ",
    )

    assert settings.host == "127.0.0.1"
    assert settings.port == 8766
    assert settings.ollama_api_base == "http://localhost:11434"
    assert settings.timeout_seconds == 12.5
    assert settings.model_profile == "max"
    assert settings.chat_model == "qwen2.5-coder:7b"


def test_gateway_settings_allows_model_overrides_without_changing_profile_defaults():
    settings = GatewaySettings(
        model_profile="lightweight",
        chat_model="custom-chat:latest",
        autocomplete_model="custom-autocomplete:latest",
    )

    assert settings.model_profile == "lightweight"
    assert settings.chat_model == "custom-chat:latest"
    assert settings.autocomplete_model == "custom-autocomplete:latest"


def test_gateway_settings_from_env_reads_overrides():
    settings = gateway_settings_from_env(
        {
            "PRO_AI_GATEWAY_HOST": "127.0.0.2",
            "PRO_AI_GATEWAY_PORT": "9000",
            "PRO_AI_GATEWAY_OLLAMA_API_BASE": "http://phone.local:11434/",
            "PRO_AI_GATEWAY_TIMEOUT_SECONDS": "5",
            "PRO_AI_GATEWAY_MODEL_PROFILE": "lightweight",
            "PRO_AI_GATEWAY_CHAT_MODEL": "my-chat:1",
            "PRO_AI_GATEWAY_AUTOCOMPLETE_MODEL": "my-auto:1",
        }
    )

    assert settings.host == "127.0.0.2"
    assert settings.port == 9000
    assert settings.ollama_api_base == "http://phone.local:11434"
    assert settings.timeout_seconds == 5
    assert settings.model_profile == "lightweight"
    assert settings.chat_model == "my-chat:1"
    assert settings.autocomplete_model == "my-auto:1"


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("host", " ", "host"),
        ("port", 0, "port"),
        ("port", 70000, "port"),
        ("ollama_api_base", "localhost:11434", "Ollama API base"),
        ("timeout_seconds", 0, "timeout"),
        ("model_profile", "unknown", "Unknown model profile"),
        ("chat_model", " ", "chat model"),
        ("autocomplete_model", " ", "autocomplete model"),
    ],
)
def test_gateway_settings_rejects_invalid_values(field, value, match):
    with pytest.raises(ValueError, match=match):
        GatewaySettings(**{field: value})

