from pro_ai_server.gateway.inventory import assess_gateway_model_inventory, extract_ollama_model_names
from pro_ai_server.gateway.router import build_default_route_catalog
from pro_ai_server.gateway.settings import GatewaySettings


def test_extract_ollama_model_names_supports_name_and_model_keys():
    assert extract_ollama_model_names({"models": [{"name": "a"}, {"model": "b"}]}) == ("a", "b")


def test_assess_gateway_model_inventory_reports_missing_models():
    routes = build_default_route_catalog(GatewaySettings(chat_model="custom-chat:latest"))

    result = assess_gateway_model_inventory(routes, {"models": [{"name": "custom-chat:latest"}]})

    assert result.available_models == ("custom-chat:latest",)
    assert "qwen2.5-coder:1.5b-base" in result.missing_models
    assert result.ok is False


def test_assess_gateway_model_inventory_accepts_all_models_present():
    settings = GatewaySettings(chat_model="chat:1", autocomplete_model="auto:1")
    routes = build_default_route_catalog(settings)
    required = sorted({route.model for route in routes.values()} | {route.fallback_model for route in routes.values()})
    payload = {"models": [{"name": model} for model in required if model]}

    result = assess_gateway_model_inventory(routes, payload)

    assert result.ok is True
    assert result.missing_models == ()

