from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.models import ModelPlan


DEFAULT_NATIVE_RUNTIME_HOST = "127.0.0.1"
DEFAULT_NATIVE_RUNTIME_PORT = 11434


@dataclass(frozen=True)
class NativeRuntimeModel:
    contract_name: str
    gguf_path: Path

    def to_inventory_entry(self) -> dict[str, str]:
        return {"name": self.contract_name}


@dataclass(frozen=True)
class NativeRuntimeConfig:
    model: NativeRuntimeModel
    host: str = DEFAULT_NATIVE_RUNTIME_HOST
    port: int = DEFAULT_NATIVE_RUNTIME_PORT
    context_length: int = 4096
    threads: int = 4
    gpu_layers: int = 0

    @property
    def api_base(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class NativeRuntimeError:
    error: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "error": self.error,
            "message": self.message,
        }


@dataclass(frozen=True)
class NativeRuntimeProfileDefaults:
    chat_model_filename: str
    autocomplete_model_filename: str
    context_length: int
    threads: int
    gpu_layers: int = 0


NATIVE_RUNTIME_PROFILE_DEFAULTS: dict[str, NativeRuntimeProfileDefaults] = {
    "lightweight": NativeRuntimeProfileDefaults(
        chat_model_filename="qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        autocomplete_model_filename="qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
        context_length=4096,
        threads=4,
    ),
    "professional": NativeRuntimeProfileDefaults(
        chat_model_filename="qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        autocomplete_model_filename="qwen2.5-coder-1.5b-base-q4_k_m.gguf",
        context_length=8192,
        threads=6,
    ),
    "max": NativeRuntimeProfileDefaults(
        chat_model_filename="qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        autocomplete_model_filename="qwen2.5-coder-1.5b-base-q4_k_m.gguf",
        context_length=8192,
        threads=8,
    ),
}


def validate_native_runtime_config(config: NativeRuntimeConfig) -> None:
    if not config.model.contract_name.strip():
        raise ValueError("Native runtime model contract name must not be empty.")
    if config.port <= 0:
        raise ValueError("Native runtime port must be positive.")
    if config.context_length <= 0:
        raise ValueError("Native runtime context length must be positive.")
    if config.threads <= 0:
        raise ValueError("Native runtime threads must be positive.")
    if config.gpu_layers < 0:
        raise ValueError("Native runtime GPU layers must not be negative.")


def native_runtime_defaults_for_profile(profile: str) -> NativeRuntimeProfileDefaults:
    normalized = profile.strip().lower()
    try:
        return NATIVE_RUNTIME_PROFILE_DEFAULTS[normalized]
    except KeyError as exc:
        valid_profiles = ", ".join(NATIVE_RUNTIME_PROFILE_DEFAULTS)
        raise ValueError(f"Unknown native runtime profile '{profile}'. Expected one of: {valid_profiles}.") from exc


def build_native_runtime_model(
    contract_name: str,
    filename: str,
    *,
    models_root: Path = Path("models"),
) -> NativeRuntimeModel:
    return NativeRuntimeModel(
        contract_name=contract_name,
        gguf_path=models_root / filename,
    )


def build_native_runtime_config_for_model_plan(
    plan: ModelPlan,
    *,
    models_root: Path = Path("models"),
    prefer: str = "chat",
    host: str = DEFAULT_NATIVE_RUNTIME_HOST,
    port: int = DEFAULT_NATIVE_RUNTIME_PORT,
) -> NativeRuntimeConfig:
    defaults = native_runtime_defaults_for_profile(plan.profile)
    normalized_prefer = prefer.strip().lower()
    if normalized_prefer not in {"chat", "autocomplete"}:
        raise ValueError("Native runtime prefer value must be 'chat' or 'autocomplete'.")

    if normalized_prefer == "chat":
        model = build_native_runtime_model(plan.chat_model, defaults.chat_model_filename, models_root=models_root)
    else:
        model = build_native_runtime_model(
            plan.autocomplete_model,
            defaults.autocomplete_model_filename,
            models_root=models_root,
        )

    config = NativeRuntimeConfig(
        model=model,
        host=host,
        port=port,
        context_length=defaults.context_length,
        threads=defaults.threads,
        gpu_layers=defaults.gpu_layers,
    )
    validate_native_runtime_config(config)
    return config


def build_native_runtime_health_response() -> dict[str, str]:
    return {
        "status": "ok",
        "engine": "llama.cpp",
        "runtime": "native-wrapper",
    }


def build_native_runtime_tags_response(model: NativeRuntimeModel | None) -> dict[str, object]:
    models = [] if model is None else [model.to_inventory_entry()]
    return {"models": models}


def build_native_runtime_generate_response(response: str) -> dict[str, str]:
    return {"response": response}


def build_native_runtime_chat_response(content: str) -> dict[str, object]:
    return {
        "message": {
            "role": "assistant",
            "content": content,
        }
    }
