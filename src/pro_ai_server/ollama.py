from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pro_ai_server.models import ModelPlan


Command = tuple[str, ...]

DEFAULT_OLLAMA_API_BASE_URL = "http://localhost:11434"
START_OLLAMA_INSTRUCTION = (
    "Start Ollama in Termux with the generated start script, then verify the selected "
    "connection mode and tunnel are active."
)
DEFAULT_TEST_PROMPT = "Reply with exactly: pro-ai-server-ready"


@dataclass(frozen=True)
class OllamaServerStatus:
    ok: bool
    model_names: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    instructions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelInventoryStatus:
    ok: bool
    model_names: tuple[str, ...] = ()
    missing_models: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    instructions: tuple[str, ...] = ()


@dataclass(frozen=True)
class OllamaTestPromptStatus:
    ok: bool
    model: str
    response: str | None = None
    warnings: tuple[str, ...] = ()
    instructions: tuple[str, ...] = ()


def build_ollama_tags_command(api_base_url: str = DEFAULT_OLLAMA_API_BASE_URL) -> Command:
    return ("curl", "--silent", "--show-error", f"{api_base_url.rstrip('/')}/api/tags")


def build_ollama_tags_commands(api_base_url: str = DEFAULT_OLLAMA_API_BASE_URL) -> tuple[Command, ...]:
    return (build_ollama_tags_command(api_base_url),)


def build_ollama_generate_command(
    model: str,
    *,
    prompt: str = DEFAULT_TEST_PROMPT,
    api_base_url: str = DEFAULT_OLLAMA_API_BASE_URL,
) -> Command:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
        separators=(",", ":"),
    )
    return (
        "curl",
        "--silent",
        "--show-error",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-d",
        payload,
        f"{api_base_url.rstrip('/')}/api/generate",
    )


def parse_ollama_tags_model_names(tags_json: str) -> tuple[str, ...]:
    try:
        payload = json.loads(tags_json)
    except json.JSONDecodeError:
        return ()

    if not isinstance(payload, dict):
        return ()

    models = payload.get("models")
    if not isinstance(models, list):
        return ()

    names: list[str] = []
    for model in models:
        name = _model_name(model)
        if name:
            names.append(name)
    return tuple(names)


def assess_ollama_server_status(tags_output: str) -> OllamaServerStatus:
    stripped = tags_output.strip()
    if not stripped:
        return _server_not_ready("Ollama did not return a response.")

    if _looks_like_error_string(stripped):
        return _server_not_ready(f"Ollama tags request failed: {stripped}")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _server_not_ready("Ollama returned invalid JSON from /api/tags.")

    if not isinstance(payload, dict):
        return _server_not_ready("Ollama returned an unexpected /api/tags response.")

    if isinstance(payload.get("error"), str):
        return _server_not_ready(f"Ollama returned an error: {payload['error']}")

    models = payload.get("models")
    if not isinstance(models, list):
        return _server_not_ready("Ollama /api/tags response did not include a models list.")

    return OllamaServerStatus(ok=True, model_names=parse_ollama_tags_model_names(stripped))


def assess_ollama_test_prompt_response(model: str, generate_output: str) -> OllamaTestPromptStatus:
    stripped = generate_output.strip()
    if not stripped:
        return _test_prompt_not_ready(model, "Ollama did not return a test-prompt response.")

    if _looks_like_error_string(stripped):
        return _test_prompt_not_ready(model, f"Ollama test-prompt request failed: {stripped}")

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return _test_prompt_not_ready(model, "Ollama returned invalid JSON from /api/generate.")

    if not isinstance(payload, dict):
        return _test_prompt_not_ready(model, "Ollama returned an unexpected /api/generate response.")

    if isinstance(payload.get("error"), str):
        warning = payload["error"]
        if "not found" in warning.lower() or "pull" in warning.lower():
            return OllamaTestPromptStatus(
                ok=False,
                model=model,
                warnings=(f"Ollama could not run model {model}: {warning}",),
                instructions=(f"Run in Termux: ollama pull {model}",),
            )
        return _test_prompt_not_ready(model, f"Ollama returned an error: {warning}")

    response = payload.get("response")
    if not isinstance(response, str) or not response.strip():
        return _test_prompt_not_ready(model, "Ollama /api/generate response did not include generated text.")

    return OllamaTestPromptStatus(ok=True, model=model, response=response.strip())


def assess_model_inventory(plan: ModelPlan, tags_output: str) -> ModelInventoryStatus:
    server_status = assess_ollama_server_status(tags_output)
    if not server_status.ok:
        return ModelInventoryStatus(
            ok=False,
            model_names=server_status.model_names,
            warnings=server_status.warnings,
            instructions=server_status.instructions,
        )

    required_models = _required_models(plan)
    present = set(server_status.model_names)
    missing = tuple(model for model in required_models if model not in present)
    if not missing:
        return ModelInventoryStatus(ok=True, model_names=server_status.model_names)

    return ModelInventoryStatus(
        ok=False,
        model_names=server_status.model_names,
        missing_models=missing,
        warnings=(f"Ollama is missing required model(s): {', '.join(missing)}.",),
        instructions=tuple(f"Run in Termux: ollama pull {model}" for model in missing),
    )


def _model_name(model: Any) -> str | None:
    if not isinstance(model, dict):
        return None
    for key in ("name", "model"):
        value = model.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _required_models(plan: ModelPlan) -> tuple[str, ...]:
    seen: set[str] = set()
    required: list[str] = []
    for model in (plan.chat_model, plan.autocomplete_model):
        if model not in seen:
            seen.add(model)
            required.append(model)
    return tuple(required)


def _looks_like_error_string(output: str) -> bool:
    lowered = output.lower()
    return (
        lowered.startswith("error:")
        or "connection refused" in lowered
        or "could not connect" in lowered
        or "failed to connect" in lowered
    )


def _server_not_ready(warning: str) -> OllamaServerStatus:
    return OllamaServerStatus(
        ok=False,
        warnings=(warning,),
        instructions=(START_OLLAMA_INSTRUCTION,),
    )


def _test_prompt_not_ready(model: str, warning: str) -> OllamaTestPromptStatus:
    return OllamaTestPromptStatus(
        ok=False,
        model=model,
        warnings=(warning,),
        instructions=(START_OLLAMA_INSTRUCTION,),
    )
