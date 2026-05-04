from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthResponse:
    service: str
    status: str
    version: str
    host: str
    port: int
    ollama_api_base: str
    model_profile: str

    def to_dict(self) -> dict[str, str | int]:
        return {
            "service": self.service,
            "status": self.status,
            "version": self.version,
            "host": self.host,
            "port": self.port,
            "ollama_api_base": self.ollama_api_base,
            "model_profile": self.model_profile,
        }


@dataclass(frozen=True)
class GatewayHttpResponse:
    status_code: int
    body: str
    content_type: str = "application/json"


@dataclass(frozen=True)
class ModelsResponse:
    models: tuple[dict[str, str], ...]

    @property
    def count(self) -> int:
        return len(self.models)

    def to_dict(self) -> dict[str, object]:
        return {
            "count": self.count,
            "models": list(self.models),
        }


@dataclass(frozen=True)
class GatewayRoute:
    task: str
    profile: str
    model: str
    fallback_model: str | None = None

    def to_dict(self) -> dict[str, str]:
        data = {
            "task": self.task,
            "profile": self.profile,
            "model": self.model,
        }
        if self.fallback_model is not None:
            data["fallback_model"] = self.fallback_model
        return data


@dataclass(frozen=True)
class RouteSelection:
    requested_task: str
    route: GatewayRoute
    used_fallback: bool

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "requested_task": self.requested_task,
            "used_fallback": self.used_fallback,
            **self.route.to_dict(),
        }


@dataclass(frozen=True)
class RouteTestResponse:
    requested_task: str
    route: GatewayRoute
    used_fallback: bool
    prompt_received: bool = False

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "requested_task": self.requested_task,
            "used_fallback": self.used_fallback,
            "prompt_received": self.prompt_received,
            **self.route.to_dict(),
        }
