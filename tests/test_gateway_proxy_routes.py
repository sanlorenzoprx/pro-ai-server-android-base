import json

from pro_ai_server.gateway import app as gateway_app
from pro_ai_server.gateway.ollama_client import OllamaProxyError, OllamaProxyResult
from pro_ai_server.gateway.settings import GatewaySettings


def test_handle_gateway_request_proxies_api_tags(monkeypatch):
    calls = []

    def fake_proxy(method, path, *, payload=None, settings=None):
        calls.append((method, path, payload, settings))
        return OllamaProxyResult(status_code=200, payload={"models": []})

    monkeypatch.setattr(gateway_app, "proxy_ollama_json", fake_proxy)

    response = gateway_app.handle_gateway_request("GET", "/api/tags", settings=GatewaySettings())

    assert response.status_code == 200
    assert json.loads(response.body) == {"models": []}
    assert calls[0][0:3] == ("GET", "/api/tags", None)


def test_handle_gateway_request_proxies_generate_and_injects_configured_model(monkeypatch):
    calls = []
    settings = GatewaySettings(chat_model="custom-chat:latest")

    def fake_proxy(method, path, *, payload=None, settings=None):
        calls.append((method, path, payload, settings))
        return OllamaProxyResult(status_code=200, payload={"response": "ok"})

    monkeypatch.setattr(gateway_app, "proxy_ollama_json", fake_proxy)

    response = gateway_app.handle_gateway_request(
        "POST",
        "/api/generate",
        body=json.dumps({"prompt": "hello", "stream": False}),
        settings=settings,
    )

    assert response.status_code == 200
    assert json.loads(response.body) == {"response": "ok"}
    assert calls[0][2] == {"prompt": "hello", "stream": False, "model": "custom-chat:latest"}


def test_handle_gateway_request_preserves_explicit_generate_model(monkeypatch):
    calls = []

    def fake_proxy(method, path, *, payload=None, settings=None):
        calls.append(payload)
        return OllamaProxyResult(status_code=200, payload={"response": "ok"})

    monkeypatch.setattr(gateway_app, "proxy_ollama_json", fake_proxy)

    gateway_app.handle_gateway_request(
        "POST",
        "/api/generate",
        body=json.dumps({"model": "user-model:latest", "prompt": "hello", "stream": False}),
        settings=GatewaySettings(chat_model="custom-chat:latest"),
    )

    assert calls[0]["model"] == "user-model:latest"


def test_handle_gateway_request_proxies_chat_and_injects_configured_model(monkeypatch):
    calls = []
    settings = GatewaySettings(chat_model="custom-chat:latest")

    def fake_proxy(method, path, *, payload=None, settings=None):
        calls.append(payload)
        return OllamaProxyResult(status_code=200, payload={"message": {"content": "ok"}})

    monkeypatch.setattr(gateway_app, "proxy_ollama_json", fake_proxy)

    response = gateway_app.handle_gateway_request(
        "POST",
        "/api/chat",
        body=json.dumps({"messages": [{"role": "user", "content": "hello"}], "stream": False}),
        settings=settings,
    )

    assert response.status_code == 200
    assert json.loads(response.body) == {"message": {"content": "ok"}}
    assert calls[0]["model"] == "custom-chat:latest"


def test_handle_gateway_request_rejects_streaming_proxy_requests():
    response = gateway_app.handle_gateway_request(
        "POST",
        "/api/chat",
        body=json.dumps({"model": "x", "messages": [], "stream": True}),
        settings=GatewaySettings(),
    )

    assert response.status_code == 400
    assert json.loads(response.body)["error"] == "unsupported_streaming"


def test_handle_gateway_request_maps_ollama_proxy_error(monkeypatch):
    def fake_proxy(method, path, *, payload=None, settings=None):
        raise OllamaProxyError(
            "ollama_unavailable",
            "Ollama is not reachable.",
            upstream="http://localhost:11434",
        )

    monkeypatch.setattr(gateway_app, "proxy_ollama_json", fake_proxy)

    response = gateway_app.handle_gateway_request("GET", "/api/tags", settings=GatewaySettings())

    assert response.status_code == 502
    assert json.loads(response.body) == {
        "error": "ollama_unavailable",
        "message": "Ollama is not reachable.",
        "upstream": "http://localhost:11434",
    }

