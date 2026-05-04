from __future__ import annotations

import json

from pro_ai_server import __version__
from pro_ai_server.gateway.ollama_client import OllamaProxyError, proxy_ollama_json
from pro_ai_server.gateway.router import build_default_route_catalog, select_route
from pro_ai_server.gateway.schemas import GatewayHttpResponse, HealthResponse, ModelsResponse, RouteTestResponse
from pro_ai_server.gateway.settings import GatewaySettings


GATEWAY_SERVICE_NAME = "pro-codeflow-gateway"


def build_health_response(settings: GatewaySettings | None = None) -> HealthResponse:
    gateway_settings = settings or GatewaySettings()
    return HealthResponse(
        service=GATEWAY_SERVICE_NAME,
        status="ok",
        version=__version__,
        host=gateway_settings.host,
        port=gateway_settings.port,
        ollama_api_base=gateway_settings.ollama_api_base,
        model_profile=gateway_settings.model_profile,
    )


def build_models_response(settings: GatewaySettings | None = None) -> ModelsResponse:
    gateway_settings = settings or GatewaySettings()
    routes = build_default_route_catalog(gateway_settings)
    return ModelsResponse(models=tuple(route.to_dict() for route in routes.values()))


def build_route_test_response(
    task: str | None,
    *,
    prompt: str | None = None,
    settings: GatewaySettings | None = None,
) -> RouteTestResponse:
    selection = select_route(task, settings=settings)
    return RouteTestResponse(
        requested_task=selection.requested_task,
        route=selection.route,
        used_fallback=selection.used_fallback,
        prompt_received=bool(prompt),
    )


def handle_gateway_request(
    method: str,
    path: str,
    *,
    body: str | None = None,
    settings: GatewaySettings | None = None,
) -> GatewayHttpResponse:
    normalized_method = method.strip().upper()
    normalized_path = path.split("?", maxsplit=1)[0].rstrip("/") or "/"

    if normalized_method == "GET" and normalized_path == "/health":
        return _json_response(200, build_health_response(settings).to_dict())

    if normalized_method == "GET" and normalized_path == "/models":
        return _json_response(200, build_models_response(settings).to_dict())

    if normalized_method == "POST" and normalized_path == "/route-test":
        request = _parse_json_object(body)
        if isinstance(request, GatewayHttpResponse):
            return request
        return _json_response(
            200,
            build_route_test_response(
                _optional_string(request.get("task")),
                prompt=_optional_string(request.get("prompt")),
                settings=settings,
            ).to_dict(),
        )

    if normalized_method == "GET" and normalized_path == "/api/tags":
        return _proxy_ollama_request("GET", "/api/tags", settings=settings)

    if normalized_method == "POST" and normalized_path in {"/api/generate", "/api/chat"}:
        request = _parse_json_object(body)
        if isinstance(request, GatewayHttpResponse):
            return request
        prepared = _prepare_ollama_payload(request, settings=settings)
        if isinstance(prepared, GatewayHttpResponse):
            return prepared
        return _proxy_ollama_request("POST", normalized_path, payload=prepared, settings=settings)

    return _json_response(
        404,
        {
            "error": "not_found",
            "message": f"Unsupported gateway route: {normalized_method} {normalized_path}",
        },
    )


def _json_response(status_code: int, payload: dict[str, object]) -> GatewayHttpResponse:
    return GatewayHttpResponse(status_code=status_code, body=json.dumps(payload, sort_keys=True))


def _proxy_ollama_request(
    method: str,
    path: str,
    *,
    payload: dict[str, object] | None = None,
    settings: GatewaySettings | None = None,
) -> GatewayHttpResponse:
    try:
        result = proxy_ollama_json(method, path, payload=payload, settings=settings)
    except OllamaProxyError as exc:
        return _json_response(exc.status_code, exc.to_dict())
    return _json_response(result.status_code, result.payload)


def _prepare_ollama_payload(
    request: dict[str, object],
    *,
    settings: GatewaySettings | None = None,
) -> dict[str, object] | GatewayHttpResponse:
    if request.get("stream") is True:
        return _json_response(
            400,
            {
                "error": "unsupported_streaming",
                "message": "Streaming proxy responses are not supported in Phase 2. Set stream to false.",
            },
        )

    prepared = dict(request)
    if not str(prepared.get("model", "")).strip():
        task = _optional_string(prepared.get("task") or prepared.get("task_type"))
        prepared["model"] = select_route(task, settings=settings).route.model
    return prepared


def _parse_json_object(body: str | None) -> dict[str, object] | GatewayHttpResponse:
    try:
        parsed = json.loads(body or "{}")
    except json.JSONDecodeError:
        return _json_response(400, {"error": "bad_request", "message": "Request body must be valid JSON."})
    if not isinstance(parsed, dict):
        return _json_response(400, {"error": "bad_request", "message": "Request body must be a JSON object."})
    return parsed


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
