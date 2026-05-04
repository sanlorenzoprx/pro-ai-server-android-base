import json

from pro_ai_server.gateway.app import build_route_test_response, handle_gateway_request
from pro_ai_server.gateway.settings import GatewaySettings


def test_build_route_test_response_for_known_task():
    response = build_route_test_response("chat", prompt="hello")

    assert response.requested_task == "chat"
    assert response.used_fallback is False
    assert response.prompt_received is True
    assert response.route.model == "qwen2.5-coder:3b"


def test_build_route_test_response_for_unknown_task_uses_chat_fallback():
    response = build_route_test_response("security-review")

    assert response.requested_task == "security_review"
    assert response.used_fallback is True
    assert response.route.task == "chat"


def test_route_test_response_uses_custom_settings_models():
    settings = GatewaySettings(chat_model="custom-chat:latest")

    response = build_route_test_response("chat", settings=settings)

    assert response.route.model == "custom-chat:latest"


def test_handle_gateway_request_returns_route_test_json():
    response = handle_gateway_request(
        "POST",
        "/route-test",
        body=json.dumps({"task": "autocomplete", "prompt": "pri"}),
        settings=GatewaySettings(),
    )

    assert response.status_code == 200
    payload = json.loads(response.body)
    assert payload["requested_task"] == "autocomplete"
    assert payload["task"] == "autocomplete"
    assert payload["model"] == "qwen2.5-coder:1.5b-base"
    assert payload["prompt_received"] is True


def test_handle_gateway_request_returns_bad_request_for_malformed_json():
    response = handle_gateway_request("POST", "/route-test", body="{not-json")

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "error": "bad_request",
        "message": "Request body must be valid JSON.",
    }


def test_handle_gateway_request_returns_bad_request_for_non_object_json():
    response = handle_gateway_request("POST", "/route-test", body=json.dumps(["chat"]))

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "error": "bad_request",
        "message": "Request body must be a JSON object.",
    }

