from pro_ai_server.gateway.router import (
    DEFAULT_ROUTE_TASK,
    GATEWAY_ROUTE_TASKS,
    build_default_route_catalog,
    select_route,
)
from pro_ai_server.gateway.schemas import GatewayRoute
from pro_ai_server.gateway.settings import GatewaySettings


def test_default_route_catalog_contains_expected_tasks():
    routes = build_default_route_catalog()

    assert tuple(routes) == GATEWAY_ROUTE_TASKS
    assert routes["chat"].profile == "balanced"
    assert routes["autocomplete"].profile == "fast"
    assert routes["refactor"].profile == "deep"
    assert routes["test_generation"].profile == "balanced"
    assert routes["documentation"].profile == "fast"


def test_select_route_returns_known_route():
    selection = select_route("refactor")

    assert selection.requested_task == "refactor"
    assert selection.route.task == "refactor"
    assert selection.route.profile == "deep"
    assert selection.route.model == "qwen2.5-coder:7b"
    assert selection.route.fallback_model == "qwen2.5-coder:3b"
    assert selection.used_fallback is False


def test_select_route_falls_back_to_chat_for_unknown_task():
    selection = select_route("code-review")

    assert selection.requested_task == "code_review"
    assert selection.route.task == DEFAULT_ROUTE_TASK
    assert selection.route.model == "qwen2.5-coder:3b"
    assert selection.used_fallback is True


def test_select_route_normalizes_task_names():
    selection = select_route(" Test-Generation ")

    assert selection.requested_task == "test_generation"
    assert selection.route.task == "test_generation"


def test_route_catalog_uses_gateway_model_overrides():
    settings = GatewaySettings(
        chat_model="local-deep-coder:latest",
        autocomplete_model="local-fast-coder:latest",
    )
    routes = build_default_route_catalog(settings)

    assert routes["chat"].model == "local-deep-coder:latest"
    assert routes["test_generation"].model == "local-deep-coder:latest"
    assert routes["refactor"].fallback_model == "local-deep-coder:latest"
    assert routes["autocomplete"].model == "local-fast-coder:latest"


def test_route_catalog_applies_per_task_route_overrides():
    settings = GatewaySettings(
        route_overrides={
            "security-review": {
                "profile": "deep",
                "model": "custom-review:latest",
                "fallback_model": "custom-chat:latest",
            },
            "chat": {"model": "custom-chat:latest"},
        }
    )
    routes = build_default_route_catalog(settings)

    assert routes["chat"].model == "custom-chat:latest"
    assert routes["security_review"].profile == "deep"
    assert routes["security_review"].model == "custom-review:latest"
    assert select_route("security-review", settings=settings).route.model == "custom-review:latest"


def test_select_route_accepts_custom_catalog():
    custom = {
        "chat": GatewayRoute(
            task="chat",
            profile="custom",
            model="custom-chat:latest",
            fallback_model=None,
        )
    }

    selection = select_route("chat", routes=custom)

    assert selection.route.model == "custom-chat:latest"


def test_gateway_route_serializes_to_dict_without_none_fallback():
    route = GatewayRoute(task="chat", profile="custom", model="custom-chat:latest")

    assert route.to_dict() == {
        "task": "chat",
        "profile": "custom",
        "model": "custom-chat:latest",
    }
