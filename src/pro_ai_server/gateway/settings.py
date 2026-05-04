from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pro_ai_server.models import model_plan_for_profile


DEFAULT_GATEWAY_HOST = "127.0.0.1"
DEFAULT_GATEWAY_PORT = 8765
DEFAULT_OLLAMA_API_BASE = "http://localhost:11434"
DEFAULT_GATEWAY_TIMEOUT_SECONDS = 30.0
DEFAULT_GATEWAY_MODEL_PROFILE = "professional"

ENV_GATEWAY_HOST = "PRO_AI_GATEWAY_HOST"
ENV_GATEWAY_PORT = "PRO_AI_GATEWAY_PORT"
ENV_OLLAMA_API_BASE = "PRO_AI_GATEWAY_OLLAMA_API_BASE"
ENV_TIMEOUT_SECONDS = "PRO_AI_GATEWAY_TIMEOUT_SECONDS"
ENV_MODEL_PROFILE = "PRO_AI_GATEWAY_MODEL_PROFILE"
ENV_CHAT_MODEL = "PRO_AI_GATEWAY_CHAT_MODEL"
ENV_AUTOCOMPLETE_MODEL = "PRO_AI_GATEWAY_AUTOCOMPLETE_MODEL"


@dataclass(frozen=True)
class GatewaySettings:
    host: str = DEFAULT_GATEWAY_HOST
    port: int | str = DEFAULT_GATEWAY_PORT
    ollama_api_base: str = DEFAULT_OLLAMA_API_BASE
    timeout_seconds: float | str = DEFAULT_GATEWAY_TIMEOUT_SECONDS
    model_profile: str = DEFAULT_GATEWAY_MODEL_PROFILE
    chat_model: str | None = None
    autocomplete_model: str | None = None
    route_overrides: Mapping[str, Mapping[str, str | None]] | None = None

    def __post_init__(self) -> None:
        host = _normalize_required_string(self.host, "gateway host")
        port = _normalize_port(self.port)
        ollama_api_base = _normalize_api_base(self.ollama_api_base)
        timeout_seconds = _normalize_positive_float(self.timeout_seconds, "gateway timeout")
        model_profile = _normalize_model_profile(self.model_profile)
        model_plan = model_plan_for_profile(model_profile)
        chat_model = _normalize_optional_model(self.chat_model, "chat model") or model_plan.chat_model
        autocomplete_model = (
            _normalize_optional_model(self.autocomplete_model, "autocomplete model")
            or model_plan.autocomplete_model
        )
        route_overrides = _normalize_route_overrides(self.route_overrides)

        object.__setattr__(self, "host", host)
        object.__setattr__(self, "port", port)
        object.__setattr__(self, "ollama_api_base", ollama_api_base)
        object.__setattr__(self, "timeout_seconds", timeout_seconds)
        object.__setattr__(self, "model_profile", model_profile)
        object.__setattr__(self, "chat_model", chat_model)
        object.__setattr__(self, "autocomplete_model", autocomplete_model)
        object.__setattr__(self, "route_overrides", route_overrides)

    @property
    def bind_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def gateway_settings_from_env(env: Mapping[str, str] | None = None) -> GatewaySettings:
    values = env or os.environ
    return GatewaySettings(
        host=values.get(ENV_GATEWAY_HOST, DEFAULT_GATEWAY_HOST),
        port=values.get(ENV_GATEWAY_PORT, DEFAULT_GATEWAY_PORT),
        ollama_api_base=values.get(ENV_OLLAMA_API_BASE, DEFAULT_OLLAMA_API_BASE),
        timeout_seconds=values.get(ENV_TIMEOUT_SECONDS, DEFAULT_GATEWAY_TIMEOUT_SECONDS),
        model_profile=values.get(ENV_MODEL_PROFILE, DEFAULT_GATEWAY_MODEL_PROFILE),
        chat_model=values.get(ENV_CHAT_MODEL),
        autocomplete_model=values.get(ENV_AUTOCOMPLETE_MODEL),
    )


def _normalize_required_string(value: Any, label: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{label} cannot be empty.")
    return normalized


def _normalize_port(value: int | str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("gateway port must be an integer.") from exc
    if port < 1 or port > 65535:
        raise ValueError("gateway port must be between 1 and 65535.")
    return port


def _normalize_api_base(value: str) -> str:
    normalized = _normalize_required_string(value, "Ollama API base").rstrip("/")
    if not normalized.startswith(("http://", "https://")):
        raise ValueError("Ollama API base must start with http:// or https://.")
    return normalized


def _normalize_positive_float(value: float | str, label: str) -> float:
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number.") from exc
    if normalized <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return normalized


def _normalize_model_profile(value: str) -> str:
    normalized = _normalize_required_string(value, "model profile").lower()
    model_plan_for_profile(normalized)
    return normalized


def _normalize_optional_model(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} cannot be empty.")
    return normalized


def _normalize_route_overrides(
    value: Mapping[str, Mapping[str, str | None]] | None,
) -> dict[str, dict[str, str | None]]:
    if value is None:
        return {}
    normalized: dict[str, dict[str, str | None]] = {}
    for task, route in value.items():
        task_name = str(task).strip().lower().replace("-", "_")
        if not task_name:
            raise ValueError("route override task cannot be empty.")
        normalized_route: dict[str, str | None] = {}
        for field in ("profile", "model", "fallback_model"):
            if field not in route:
                continue
            raw_value = route[field]
            if raw_value is None:
                normalized_route[field] = None
                continue
            field_value = str(raw_value).strip()
            if not field_value:
                raise ValueError(f"route override {task_name}.{field} cannot be empty.")
            normalized_route[field] = field_value
        normalized[task_name] = normalized_route
    return normalized
