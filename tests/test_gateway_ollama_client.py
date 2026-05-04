import json
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from pro_ai_server.gateway.ollama_client import (
    OllamaProxyError,
    OllamaProxyResult,
    proxy_ollama_json,
)
from pro_ai_server.gateway.settings import GatewaySettings


def test_proxy_ollama_json_get_success():
    def transport(request: Request, timeout: float):
        assert request.full_url == "http://localhost:11434/api/tags"
        assert request.get_method() == "GET"
        assert timeout == 30
        return 200, '{"models":[]}'

    result = proxy_ollama_json("GET", "/api/tags", settings=GatewaySettings(), transport=transport)

    assert result == OllamaProxyResult(status_code=200, payload={"models": []})


def test_proxy_ollama_json_post_success_sends_json_body():
    captured = {}

    def transport(request: Request, timeout: float):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return 200, '{"response":"ok"}'

    result = proxy_ollama_json(
        "POST",
        "/api/generate",
        payload={"model": "custom:latest", "prompt": "hi"},
        settings=GatewaySettings(),
        transport=transport,
    )

    assert captured["body"] == {"model": "custom:latest", "prompt": "hi"}
    assert result.payload == {"response": "ok"}


def test_proxy_ollama_json_maps_url_error_to_structured_error():
    def transport(request: Request, timeout: float):
        raise URLError("connection refused")

    with pytest.raises(OllamaProxyError) as error:
        proxy_ollama_json("GET", "/api/tags", settings=GatewaySettings(), transport=transport)

    assert error.value.code == "ollama_unavailable"
    assert error.value.status_code == 502
    assert "connection refused" in error.value.message


def test_proxy_ollama_json_maps_timeout_to_structured_error():
    def transport(request: Request, timeout: float):
        raise TimeoutError("timed out")

    with pytest.raises(OllamaProxyError) as error:
        proxy_ollama_json("GET", "/api/tags", settings=GatewaySettings(), transport=transport)

    assert error.value.code == "ollama_timeout"
    assert error.value.status_code == 502


def test_proxy_ollama_json_maps_http_error_to_structured_error():
    def transport(request: Request, timeout: float):
        raise HTTPError(request.full_url, 503, "unavailable", hdrs=None, fp=None)

    with pytest.raises(OllamaProxyError) as error:
        proxy_ollama_json("GET", "/api/tags", settings=GatewaySettings(), transport=transport)

    assert error.value.code == "ollama_http_error"
    assert error.value.status_code == 503


def test_proxy_ollama_json_rejects_invalid_json_response():
    def transport(request: Request, timeout: float):
        return 200, "not json"

    with pytest.raises(OllamaProxyError) as error:
        proxy_ollama_json("GET", "/api/tags", settings=GatewaySettings(), transport=transport)

    assert error.value.code == "invalid_ollama_response"
    assert error.value.status_code == 502

