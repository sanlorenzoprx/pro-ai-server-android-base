from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pro_ai_server.gateway.settings import GatewaySettings


Transport = Callable[[Request, float], tuple[int, str]]


@dataclass(frozen=True)
class OllamaProxyResult:
    status_code: int
    payload: dict[str, object]


class OllamaProxyError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 502, upstream: str) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.upstream = upstream
        super().__init__(message)

    def to_dict(self) -> dict[str, object]:
        return {
            "error": self.code,
            "message": self.message,
            "upstream": self.upstream,
        }


def proxy_ollama_json(
    method: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    settings: GatewaySettings | None = None,
    transport: Transport | None = None,
) -> OllamaProxyResult:
    gateway_settings = settings or GatewaySettings()
    url = _ollama_url(gateway_settings, path)
    request = _build_request(method, url, payload)
    try:
        status_code, response_body = (transport or _default_transport)(request, gateway_settings.timeout_seconds)
    except TimeoutError as exc:
        raise OllamaProxyError(
            "ollama_timeout",
            f"Ollama request timed out at {gateway_settings.ollama_api_base}.",
            upstream=gateway_settings.ollama_api_base,
        ) from exc
    except HTTPError as exc:
        raise OllamaProxyError(
            "ollama_http_error",
            f"Ollama returned HTTP {exc.code}.",
            status_code=exc.code,
            upstream=gateway_settings.ollama_api_base,
        ) from exc
    except URLError as exc:
        raise OllamaProxyError(
            "ollama_unavailable",
            f"Ollama is not reachable at {gateway_settings.ollama_api_base}: {exc.reason}",
            upstream=gateway_settings.ollama_api_base,
        ) from exc
    except OSError as exc:
        raise OllamaProxyError(
            "ollama_unavailable",
            f"Ollama is not reachable at {gateway_settings.ollama_api_base}: {exc}",
            upstream=gateway_settings.ollama_api_base,
        ) from exc

    try:
        decoded = json.loads(response_body or "{}")
    except json.JSONDecodeError as exc:
        raise OllamaProxyError(
            "invalid_ollama_response",
            "Ollama response was not valid JSON.",
            upstream=gateway_settings.ollama_api_base,
        ) from exc
    if not isinstance(decoded, dict):
        raise OllamaProxyError(
            "invalid_ollama_response",
            "Ollama response must be a JSON object.",
            upstream=gateway_settings.ollama_api_base,
        )
    return OllamaProxyResult(status_code=status_code, payload=decoded)


def _ollama_url(settings: GatewaySettings, path: str) -> str:
    normalized_path = "/" + path.lstrip("/")
    return f"{settings.ollama_api_base}{normalized_path}"


def _build_request(method: str, url: str, payload: dict[str, object] | None) -> Request:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    return Request(url, data=data, headers=headers, method=method.strip().upper())


def _default_transport(request: Request, timeout: float) -> tuple[int, str]:
    with urlopen(request, timeout=timeout) as response:
        return response.getcode(), response.read().decode("utf-8")

