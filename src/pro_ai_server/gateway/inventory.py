from __future__ import annotations

from dataclasses import dataclass

from pro_ai_server.gateway.schemas import GatewayRoute


@dataclass(frozen=True)
class GatewayModelInventory:
    required_models: tuple[str, ...]
    available_models: tuple[str, ...]
    missing_models: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.missing_models


def extract_ollama_model_names(payload: dict[str, object]) -> tuple[str, ...]:
    models = payload.get("models", [])
    if not isinstance(models, list):
        return ()
    names = []
    for model in models:
        if not isinstance(model, dict):
            continue
        name = model.get("name") or model.get("model")
        if isinstance(name, str) and name.strip():
            names.append(name.strip())
    return tuple(names)


def assess_gateway_model_inventory(
    routes: dict[str, GatewayRoute],
    tags_payload: dict[str, object],
) -> GatewayModelInventory:
    available = tuple(sorted(set(extract_ollama_model_names(tags_payload))))
    required_set = set()
    for route in routes.values():
        required_set.add(route.model)
        if route.fallback_model:
            required_set.add(route.fallback_model)
    required = tuple(sorted(model for model in required_set if model))
    missing = tuple(model for model in required if model not in available)
    return GatewayModelInventory(required_models=required, available_models=available, missing_models=missing)
