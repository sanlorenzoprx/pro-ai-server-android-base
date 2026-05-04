import json

from pro_ai_server import __version__
from pro_ai_server.gateway.app import build_health_response, handle_gateway_request
from pro_ai_server.gateway.settings import GatewaySettings


def test_build_health_response_uses_safe_settings_summary():
    settings = GatewaySettings(host="127.0.0.2", port=9000, ollama_api_base="http://phone.local:11434")

    response = build_health_response(settings)

    assert response.service == "pro-codeflow-gateway"
    assert response.status == "ok"
    assert response.version == __version__
    assert response.host == "127.0.0.2"
    assert response.port == 9000
    assert response.ollama_api_base == "http://phone.local:11434"
    assert response.model_profile == "professional"


def test_health_response_serializes_to_contract_shape():
    response = build_health_response(GatewaySettings())

    assert response.to_dict() == {
        "service": "pro-codeflow-gateway",
        "status": "ok",
        "version": __version__,
        "host": "127.0.0.1",
        "port": 8765,
        "ollama_api_base": "http://localhost:11434",
        "model_profile": "professional",
    }


def test_handle_gateway_request_returns_health_json():
    response = handle_gateway_request("GET", "/health", settings=GatewaySettings())

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert json.loads(response.body) == build_health_response(GatewaySettings()).to_dict()


def test_handle_gateway_request_returns_not_found_json():
    response = handle_gateway_request("GET", "/unknown", settings=GatewaySettings())

    assert response.status_code == 404
    assert json.loads(response.body) == {
        "error": "not_found",
        "message": "Unsupported gateway route: GET /unknown",
    }

