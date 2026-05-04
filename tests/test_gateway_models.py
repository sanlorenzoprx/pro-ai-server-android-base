import json

from pro_ai_server.gateway.app import build_models_response, handle_gateway_request
from pro_ai_server.gateway.settings import GatewaySettings


def test_build_models_response_lists_route_metadata_without_ollama():
    response = build_models_response(GatewaySettings())

    assert response.count == 5
    assert [model["task"] for model in response.models] == [
        "autocomplete",
        "chat",
        "refactor",
        "test_generation",
        "documentation",
    ]
    assert response.models[1] == {
        "task": "chat",
        "profile": "balanced",
        "model": "qwen2.5-coder:3b",
        "fallback_model": "qwen2.5-coder:1.5b",
    }


def test_models_response_uses_custom_gateway_models():
    settings = GatewaySettings(chat_model="custom-chat:latest", autocomplete_model="custom-auto:latest")

    response = build_models_response(settings)
    by_task = {model["task"]: model for model in response.models}

    assert by_task["chat"]["model"] == "custom-chat:latest"
    assert by_task["test_generation"]["model"] == "custom-chat:latest"
    assert by_task["autocomplete"]["model"] == "custom-auto:latest"


def test_handle_gateway_request_returns_models_json():
    response = handle_gateway_request("GET", "/models", settings=GatewaySettings())

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["count"] == 5
    assert payload["models"][0]["task"] == "autocomplete"

