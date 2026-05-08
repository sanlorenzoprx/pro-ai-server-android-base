from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from pro_ai_server.models import ModelPlan


DEFAULT_NATIVE_RUNTIME_HOST = "127.0.0.1"
DEFAULT_NATIVE_RUNTIME_PORT = 11434
DEFAULT_NATIVE_RUNTIME_STATE_PATH = Path(".cache") / "pro-ai-server" / "native-runtime-state.json"


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
class NativeRuntimeServerCommand:
    executable: Path
    args: tuple[str, ...]

    @property
    def command(self) -> tuple[str, ...]:
        return (str(self.executable), *self.args)

    def render(self) -> str:
        return " ".join(self.command)


@dataclass(frozen=True)
class NativeRuntimeLaunchCheck:
    key: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class NativeRuntimeLaunchPlan:
    config: NativeRuntimeConfig
    command: NativeRuntimeServerCommand
    checks: tuple[NativeRuntimeLaunchCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.ok for check in self.checks)


@dataclass(frozen=True)
class NativeRuntimeProcess:
    pid: int
    command: NativeRuntimeServerCommand


@dataclass(frozen=True)
class NativeRuntimeReadiness:
    ok: bool
    attempts: int
    detail: str


@dataclass(frozen=True)
class NativeRuntimeState:
    pid: int
    command: tuple[str, ...]
    api_base: str
    model: str
    gguf_path: Path
    started_at: str

    def to_dict(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "command": list(self.command),
            "api_base": self.api_base,
            "model": self.model,
            "gguf_path": str(self.gguf_path),
            "started_at": self.started_at,
        }


@dataclass(frozen=True)
class NativeRuntimeLifecycleStatus:
    state: NativeRuntimeState | None
    process_running: bool | None
    readiness: NativeRuntimeReadiness
    stale_state: bool = False


@dataclass(frozen=True)
class NativeRuntimeDoctorReport:
    manifest: NativeRuntimeManifest
    launch_plan: NativeRuntimeLaunchPlan
    lifecycle_status: NativeRuntimeLifecycleStatus

    @property
    def ready(self) -> bool:
        return self.launch_plan.ready and self.lifecycle_status.readiness.ok


@dataclass(frozen=True)
class NativeRuntimeAssetCheck:
    key: str
    path: Path
    ok: bool
    detail: str


@dataclass(frozen=True)
class NativeRuntimeAssetReport:
    manifest: NativeRuntimeManifest
    profile: str
    checks: tuple[NativeRuntimeAssetCheck, ...]

    @property
    def ready(self) -> bool:
        return all(check.ok for check in self.checks)


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


@dataclass(frozen=True)
class NativeRuntimeManifest:
    engine: str
    policy: str
    profiles: dict[str, NativeRuntimeProfileDefaults]


def load_native_runtime_manifest(path: Path | None = None) -> NativeRuntimeManifest:
    if path is None:
        text = resources.files("pro_ai_server").joinpath("native-runtime-manifest.json").read_text(encoding="utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    payload = json.loads(text)
    profiles = {
        str(profile): _profile_defaults_from_mapping(defaults)
        for profile, defaults in payload.get("profiles", {}).items()
    }
    if not profiles:
        raise ValueError("Native runtime manifest must define at least one profile.")
    return NativeRuntimeManifest(
        engine=str(payload.get("engine", "llama.cpp")),
        policy=str(payload.get("policy", "")),
        profiles=profiles,
    )


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


def native_runtime_defaults_for_profile(
    profile: str,
    *,
    manifest: NativeRuntimeManifest | None = None,
) -> NativeRuntimeProfileDefaults:
    runtime_manifest = manifest or load_native_runtime_manifest()
    normalized = profile.strip().lower()
    try:
        return runtime_manifest.profiles[normalized]
    except KeyError as exc:
        valid_profiles = ", ".join(runtime_manifest.profiles)
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
    manifest: NativeRuntimeManifest | None = None,
) -> NativeRuntimeConfig:
    defaults = native_runtime_defaults_for_profile(plan.profile, manifest=manifest)
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


def build_llama_server_command(
    config: NativeRuntimeConfig,
    *,
    executable: Path = Path("llama-server"),
) -> NativeRuntimeServerCommand:
    validate_native_runtime_config(config)
    args = [
        "--model",
        str(config.model.gguf_path),
        "--host",
        config.host,
        "--port",
        str(config.port),
        "--ctx-size",
        str(config.context_length),
        "--threads",
        str(config.threads),
    ]
    if config.gpu_layers:
        args.extend(("--n-gpu-layers", str(config.gpu_layers)))
    return NativeRuntimeServerCommand(executable=executable, args=tuple(args))


def build_native_runtime_launch_plan(
    config: NativeRuntimeConfig,
    *,
    executable: Path = Path("llama-server"),
) -> NativeRuntimeLaunchPlan:
    command = build_llama_server_command(config, executable=executable)
    checks = (
        _path_check("llama-server", executable, "llama.cpp server executable"),
        _path_check("model-file", config.model.gguf_path, "GGUF model file"),
    )
    return NativeRuntimeLaunchPlan(config=config, command=command, checks=checks)


def build_native_runtime_asset_report(
    profile: str,
    *,
    models_root: Path = Path("models"),
    executable: Path = Path("llama-server"),
    manifest: NativeRuntimeManifest | None = None,
) -> NativeRuntimeAssetReport:
    runtime_manifest = manifest or load_native_runtime_manifest()
    defaults = native_runtime_defaults_for_profile(profile, manifest=runtime_manifest)
    model_files = _unique_model_filenames(defaults)
    checks = [
        _asset_check("llama-server", executable, "llama.cpp server executable"),
    ]
    checks.extend(
        _asset_check(f"model:{filename}", models_root / filename, "GGUF model file")
        for filename in model_files
    )
    return NativeRuntimeAssetReport(
        manifest=runtime_manifest,
        profile=profile.strip().lower(),
        checks=tuple(checks),
    )


def render_native_runtime_launch_plan(plan: NativeRuntimeLaunchPlan) -> tuple[str, ...]:
    lines = [
        "Native runtime launch plan",
        f"Ready: {plan.ready}",
        f"Model: {plan.config.model.contract_name}",
        f"API base: {plan.config.api_base}",
        f"Command: {plan.command.render()}",
    ]
    lines.extend(
        f"- {'OK' if check.ok else 'Missing'} {check.key}: {check.detail}"
        for check in plan.checks
    )
    return tuple(lines)


def render_native_runtime_asset_report(report: NativeRuntimeAssetReport) -> tuple[str, ...]:
    lines = [
        "Native runtime asset readiness",
        f"Ready: {report.ready}",
        f"Engine: {report.manifest.engine}",
        f"Profile: {report.profile}",
    ]
    lines.extend(
        f"- {'OK' if check.ok else 'Missing'} {check.key}: {check.detail}"
        for check in report.checks
    )
    if not report.ready:
        lines.append("Next: place missing assets at the shown paths, then rerun this command before Android smoke.")
    return tuple(lines)


def start_native_runtime_process(
    plan: NativeRuntimeLaunchPlan,
    *,
    force: bool = False,
    popen: Any = subprocess.Popen,
) -> NativeRuntimeProcess:
    if not plan.ready and not force:
        missing = ", ".join(check.key for check in plan.checks if not check.ok)
        raise ValueError(f"Native runtime launch plan is not ready: {missing}.")
    process = popen(
        list(plan.command.command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
    )
    return NativeRuntimeProcess(pid=int(process.pid), command=plan.command)


def wait_for_native_runtime_readiness(
    api_base: str,
    *,
    timeout_seconds: float = 30.0,
    interval_seconds: float = 1.0,
    fetch_tags: Any | None = None,
    sleep: Any = time.sleep,
) -> NativeRuntimeReadiness:
    fetch = fetch_tags or _fetch_tags
    attempts = 0
    deadline = time.monotonic() + timeout_seconds
    last_error = "runtime did not respond before timeout"
    while True:
        attempts += 1
        try:
            payload = fetch(api_base)
        except OSError as exc:
            last_error = str(exc)
        else:
            if isinstance(payload, str) and '"models"' in payload:
                return NativeRuntimeReadiness(ok=True, attempts=attempts, detail="runtime responded on /api/tags")
            last_error = "runtime /api/tags response did not include models"

        if time.monotonic() >= deadline:
            return NativeRuntimeReadiness(ok=False, attempts=attempts, detail=last_error)
        sleep(max(0.0, interval_seconds))


def default_native_runtime_state_path(root: Path = Path(".")) -> Path:
    return root / DEFAULT_NATIVE_RUNTIME_STATE_PATH


def build_native_runtime_state(
    process: NativeRuntimeProcess,
    config: NativeRuntimeConfig,
    *,
    now: Any | None = None,
) -> NativeRuntimeState:
    current_time = now or datetime.now(timezone.utc)
    started_at = current_time.isoformat()
    return NativeRuntimeState(
        pid=process.pid,
        command=process.command.command,
        api_base=config.api_base,
        model=config.model.contract_name,
        gguf_path=config.model.gguf_path,
        started_at=started_at,
    )


def write_native_runtime_state(state: NativeRuntimeState, path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_native_runtime_state(path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH) -> NativeRuntimeState | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return NativeRuntimeState(
        pid=int(payload["pid"]),
        command=tuple(str(part) for part in payload.get("command", ())),
        api_base=str(payload["api_base"]),
        model=str(payload["model"]),
        gguf_path=Path(str(payload["gguf_path"])),
        started_at=str(payload["started_at"]),
    )


def remove_native_runtime_state(path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH) -> bool:
    if not path.exists():
        return False
    path.unlink()
    return True


def is_process_running(pid: int, *, exists: Any | None = None) -> bool:
    process_exists = exists or _process_exists
    return bool(process_exists(pid))


def build_native_runtime_lifecycle_status(
    state_path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH,
    *,
    fetch_tags: Any | None = None,
    process_exists: Any | None = None,
) -> NativeRuntimeLifecycleStatus:
    state = load_native_runtime_state(state_path)
    if state is None:
        return NativeRuntimeLifecycleStatus(
            state=None,
            process_running=None,
            readiness=NativeRuntimeReadiness(ok=False, attempts=0, detail="no native runtime state file"),
        )
    running = is_process_running(state.pid, exists=process_exists)
    readiness = wait_for_native_runtime_readiness(
        state.api_base,
        timeout_seconds=0,
        interval_seconds=0,
        fetch_tags=fetch_tags,
        sleep=lambda _seconds: None,
    )
    return NativeRuntimeLifecycleStatus(
        state=state,
        process_running=running,
        readiness=readiness,
        stale_state=not running,
    )


def render_native_runtime_lifecycle_status(status: NativeRuntimeLifecycleStatus) -> tuple[str, ...]:
    lines = ["Native runtime status"]
    if status.state is None:
        lines.append("State: missing")
        lines.append(f"Readiness: {status.readiness.detail}")
        return tuple(lines)
    lines.extend(
        (
            "State: recorded",
            f"PID: {status.state.pid}",
            f"Process running: {status.process_running}",
            f"Model: {status.state.model}",
            f"API base: {status.state.api_base}",
            f"GGUF path: {status.state.gguf_path}",
            f"Started at: {status.state.started_at}",
            f"Runtime ready: {status.readiness.ok}",
            f"Readiness detail: {status.readiness.detail}",
        )
    )
    if status.stale_state:
        lines.append("Warning: recorded PID is not running; state is stale.")
    return tuple(lines)


def build_native_runtime_doctor_report(
    plan: ModelPlan,
    *,
    models_root: Path = Path("models"),
    prefer: str = "chat",
    host: str = DEFAULT_NATIVE_RUNTIME_HOST,
    port: int = DEFAULT_NATIVE_RUNTIME_PORT,
    executable: Path = Path("llama-server"),
    manifest_path: Path | None = None,
    state_path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH,
    fetch_tags: Any | None = None,
    process_exists: Any | None = None,
) -> NativeRuntimeDoctorReport:
    manifest = load_native_runtime_manifest(manifest_path)
    config = build_native_runtime_config_for_model_plan(
        plan,
        models_root=models_root,
        prefer=prefer,
        host=host,
        port=port,
        manifest=manifest,
    )
    launch_plan = build_native_runtime_launch_plan(config, executable=executable)
    lifecycle_status = build_native_runtime_lifecycle_status(
        state_path,
        fetch_tags=fetch_tags,
        process_exists=process_exists,
    )
    return NativeRuntimeDoctorReport(
        manifest=manifest,
        launch_plan=launch_plan,
        lifecycle_status=lifecycle_status,
    )


def render_native_runtime_doctor_report(report: NativeRuntimeDoctorReport) -> tuple[str, ...]:
    lines = [
        "Native runtime doctor",
        f"Engine: {report.manifest.engine}",
        f"Profile ready: {report.launch_plan.ready}",
        f"Lifecycle ready: {report.lifecycle_status.readiness.ok}",
        f"Overall ready: {report.ready}",
    ]
    lines.extend(render_native_runtime_launch_plan(report.launch_plan)[1:])
    lines.extend(render_native_runtime_lifecycle_status(report.lifecycle_status)[1:])
    return tuple(lines)


def stop_native_runtime(
    state_path: Path = DEFAULT_NATIVE_RUNTIME_STATE_PATH,
    *,
    terminate: Any | None = None,
) -> tuple[NativeRuntimeState | None, bool]:
    state = load_native_runtime_state(state_path)
    if state is None:
        return None, False
    terminator = terminate or _terminate_process
    terminator(state.pid)
    removed = remove_native_runtime_state(state_path)
    return state, removed


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


def _profile_defaults_from_mapping(defaults: dict[str, Any]) -> NativeRuntimeProfileDefaults:
    profile_defaults = NativeRuntimeProfileDefaults(
        chat_model_filename=str(defaults["chat_model_filename"]),
        autocomplete_model_filename=str(defaults["autocomplete_model_filename"]),
        context_length=int(defaults["context_length"]),
        threads=int(defaults["threads"]),
        gpu_layers=int(defaults.get("gpu_layers", 0)),
    )
    if not profile_defaults.chat_model_filename.strip():
        raise ValueError("Native runtime profile chat model filename must not be empty.")
    if not profile_defaults.autocomplete_model_filename.strip():
        raise ValueError("Native runtime profile autocomplete model filename must not be empty.")
    if profile_defaults.context_length <= 0:
        raise ValueError("Native runtime profile context length must be positive.")
    if profile_defaults.threads <= 0:
        raise ValueError("Native runtime profile threads must be positive.")
    if profile_defaults.gpu_layers < 0:
        raise ValueError("Native runtime profile GPU layers must not be negative.")
    return profile_defaults


def _path_check(key: str, path: Path, label: str) -> NativeRuntimeLaunchCheck:
    if path.exists():
        return NativeRuntimeLaunchCheck(key=key, ok=True, detail=f"{label} found at {path}")
    return NativeRuntimeLaunchCheck(key=key, ok=False, detail=f"{label} not found at {path}")


def _asset_check(key: str, path: Path, label: str) -> NativeRuntimeAssetCheck:
    if path.exists():
        return NativeRuntimeAssetCheck(key=key, path=path, ok=True, detail=f"{label} found at {path}")
    return NativeRuntimeAssetCheck(key=key, path=path, ok=False, detail=f"{label} not found at {path}")


def _unique_model_filenames(defaults: NativeRuntimeProfileDefaults) -> tuple[str, ...]:
    seen: set[str] = set()
    filenames: list[str] = []
    for filename in (defaults.chat_model_filename, defaults.autocomplete_model_filename):
        if filename not in seen:
            seen.add(filename)
            filenames.append(filename)
    return tuple(filenames)


def _fetch_tags(api_base: str) -> str:
    from urllib.request import urlopen

    with urlopen(f"{api_base.rstrip('/')}/api/tags", timeout=2.0) as response:
        return response.read().decode("utf-8")


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (OSError, SystemError, ValueError):
        return False
    return True


def _terminate_process(pid: int) -> None:
    if pid <= 0:
        raise ValueError("Native runtime PID must be positive.")
    try:
        os.kill(pid, 15)
    except (OSError, SystemError, ValueError):
        return
