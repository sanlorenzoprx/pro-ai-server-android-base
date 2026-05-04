from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from pro_ai_server.gateway.settings import GatewaySettings


@dataclass(frozen=True)
class GatewayConfig:
    settings: GatewaySettings
    sources: tuple[Path, ...] = ()


def default_user_config_path(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".pro-ai-server" / "config.yaml"


def default_project_config_path(project_root: Path | None = None) -> Path:
    return (project_root or Path.cwd()) / ".pro-ai-server" / "config.yaml"


def load_gateway_config(
    *,
    project_root: Path | None = None,
    home: Path | None = None,
    explicit_path: Path | None = None,
) -> GatewayConfig:
    if explicit_path is not None:
        data = _read_yaml_mapping(explicit_path)
        return GatewayConfig(settings=_settings_from_config_data(data), sources=(explicit_path,))

    sources = [default_user_config_path(home), default_project_config_path(project_root)]
    merged: dict[str, Any] = {}
    found: list[Path] = []
    for source in sources:
        if not source.exists():
            continue
        found.append(source)
        merged = _deep_merge(merged, _read_yaml_mapping(source))
    return GatewayConfig(settings=_settings_from_config_data(merged), sources=tuple(found))


def _settings_from_config_data(data: dict[str, Any]) -> GatewaySettings:
    gateway = _mapping_or_empty(data.get("gateway"), "gateway")
    routing = _mapping_or_empty(data.get("routing"), "routing")
    routes = _mapping_or_empty(routing.get("routes"), "routing.routes")
    return GatewaySettings(
        host=gateway.get("host", GatewaySettings.host),
        port=gateway.get("port", GatewaySettings.port),
        ollama_api_base=gateway.get("ollama_api_base", GatewaySettings.ollama_api_base),
        timeout_seconds=gateway.get("timeout_seconds", GatewaySettings.timeout_seconds),
        model_profile=gateway.get("model_profile", GatewaySettings.model_profile),
        chat_model=gateway.get("chat_model"),
        autocomplete_model=gateway.get("autocomplete_model"),
        route_overrides=routes,
    )


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Gateway config must be a YAML mapping: {path}")
    return loaded


def _mapping_or_empty(value: object, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Gateway config section {label} must be a mapping.")
    return value


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
