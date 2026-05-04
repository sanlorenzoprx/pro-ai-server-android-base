"""Local gateway foundation for Pro CodeFlow Server."""

from pro_ai_server.gateway.app import (
    build_health_response,
    build_models_response,
    build_route_test_response,
    handle_gateway_request,
)
from pro_ai_server.gateway.config import GatewayConfig, load_gateway_config
from pro_ai_server.gateway.inventory import GatewayModelInventory, assess_gateway_model_inventory
from pro_ai_server.gateway.ollama_client import OllamaProxyError, OllamaProxyResult, proxy_ollama_json
from pro_ai_server.gateway.router import build_default_route_catalog, select_route
from pro_ai_server.gateway.schemas import (
    GatewayHttpResponse,
    GatewayRoute,
    HealthResponse,
    ModelsResponse,
    RouteSelection,
    RouteTestResponse,
)
from pro_ai_server.gateway.server import GatewayStatusError, fetch_gateway_health, serve_gateway
from pro_ai_server.gateway.settings import GatewaySettings, gateway_settings_from_env

__all__ = [
    "GatewayHttpResponse",
    "GatewayRoute",
    "GatewaySettings",
    "GatewayConfig",
    "GatewayModelInventory",
    "GatewayStatusError",
    "HealthResponse",
    "ModelsResponse",
    "OllamaProxyError",
    "OllamaProxyResult",
    "RouteSelection",
    "RouteTestResponse",
    "build_default_route_catalog",
    "build_health_response",
    "build_models_response",
    "build_route_test_response",
    "fetch_gateway_health",
    "gateway_settings_from_env",
    "handle_gateway_request",
    "load_gateway_config",
    "proxy_ollama_json",
    "select_route",
    "assess_gateway_model_inventory",
    "serve_gateway",
]
