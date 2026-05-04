from __future__ import annotations

from collections.abc import Mapping

from pro_ai_server.gateway.schemas import GatewayRoute, RouteSelection
from pro_ai_server.gateway.settings import GatewaySettings
from pro_ai_server.models import model_plan_for_profile


DEFAULT_ROUTE_TASK = "chat"
GATEWAY_ROUTE_TASKS = (
    "autocomplete",
    "chat",
    "refactor",
    "test_generation",
    "documentation",
)


def build_default_route_catalog(settings: GatewaySettings | None = None) -> dict[str, GatewayRoute]:
    gateway_settings = settings or GatewaySettings()
    lightweight = model_plan_for_profile("lightweight")
    professional = model_plan_for_profile("professional")
    max_plan = model_plan_for_profile("max")

    routes = {
        "autocomplete": GatewayRoute(
            task="autocomplete",
            profile="fast",
            model=gateway_settings.autocomplete_model,
            fallback_model=professional.autocomplete_model,
        ),
        "chat": GatewayRoute(
            task="chat",
            profile="balanced",
            model=gateway_settings.chat_model,
            fallback_model=lightweight.chat_model,
        ),
        "refactor": GatewayRoute(
            task="refactor",
            profile="deep",
            model=max_plan.chat_model,
            fallback_model=gateway_settings.chat_model,
        ),
        "test_generation": GatewayRoute(
            task="test_generation",
            profile="balanced",
            model=gateway_settings.chat_model,
            fallback_model=lightweight.chat_model,
        ),
        "documentation": GatewayRoute(
            task="documentation",
            profile="fast",
            model=lightweight.chat_model,
            fallback_model=lightweight.autocomplete_model,
        ),
    }
    return apply_route_overrides(routes, gateway_settings.route_overrides)


def select_route(
    task: str | None,
    *,
    settings: GatewaySettings | None = None,
    routes: Mapping[str, GatewayRoute] | None = None,
) -> RouteSelection:
    requested_task = normalize_task(task)
    route_catalog = routes or build_default_route_catalog(settings)
    route = route_catalog.get(requested_task)
    if route is not None:
        return RouteSelection(requested_task=requested_task, route=route, used_fallback=False)

    return RouteSelection(
        requested_task=requested_task,
        route=route_catalog[DEFAULT_ROUTE_TASK],
        used_fallback=True,
    )


def normalize_task(task: str | None) -> str:
    normalized = (task or DEFAULT_ROUTE_TASK).strip().lower().replace("-", "_")
    return normalized or DEFAULT_ROUTE_TASK


def apply_route_overrides(
    routes: Mapping[str, GatewayRoute],
    overrides: Mapping[str, Mapping[str, str | None]] | None,
) -> dict[str, GatewayRoute]:
    updated = dict(routes)
    for task, override in (overrides or {}).items():
        normalized_task = normalize_task(task)
        base = updated.get(
            normalized_task,
            GatewayRoute(task=normalized_task, profile="custom", model="", fallback_model=None),
        )
        updated[normalized_task] = GatewayRoute(
            task=normalized_task,
            profile=override.get("profile") or base.profile,
            model=override.get("model") or base.model,
            fallback_model=override.get("fallback_model", base.fallback_model),
        )
    return updated
