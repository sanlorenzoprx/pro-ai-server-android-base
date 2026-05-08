from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pro_ai_server.native_runtime import NativeRuntimeConfig, NativeRuntimeManifest
from pro_ai_server.ollama import DEFAULT_TEST_PROMPT


Command = tuple[str, ...]

DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT = "/data/local/tmp/pro-ai-server/native-runtime"


@dataclass(frozen=True)
class NativeAndroidRuntimeLayout:
    root: PurePosixPath
    bin_dir: PurePosixPath
    models_dir: PurePosixPath
    config_dir: PurePosixPath
    state_dir: PurePosixPath
    logs_dir: PurePosixPath
    remote_llama_server: PurePosixPath
    remote_model: PurePosixPath
    remote_manifest: PurePosixPath


@dataclass(frozen=True)
class NativeAndroidRuntimeAsset:
    key: str
    local_path: Path
    remote_path: PurePosixPath


@dataclass(frozen=True)
class NativeAndroidRuntimeInstallPlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    instructions: tuple[str, ...]
    support_libraries: tuple[Path, ...] = ()
    assets: tuple[NativeAndroidRuntimeAsset, ...] = ()


@dataclass(frozen=True)
class NativeAndroidRuntimeStartPlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    remote_pid_file: PurePosixPath
    remote_log_file: PurePosixPath
    remote_start_shell: str


@dataclass(frozen=True)
class NativeAndroidRuntimeStatusPlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    remote_pid_file: PurePosixPath
    remote_log_file: PurePosixPath


@dataclass(frozen=True)
class NativeAndroidRuntimeStopPlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    remote_pid_file: PurePosixPath


@dataclass(frozen=True)
class NativeAndroidRuntimeSmokePlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    api_base: str
    model: str
    prompt: str


@dataclass(frozen=True)
class NativeAndroidRuntimeSmokePathPlan:
    install_plan: NativeAndroidRuntimeInstallPlan
    start_plan: NativeAndroidRuntimeStartPlan
    smoke_plan: NativeAndroidRuntimeSmokePlan


def build_native_android_runtime_layout(
    config: NativeRuntimeConfig,
    *,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
) -> NativeAndroidRuntimeLayout:
    root = PurePosixPath(remote_root.rstrip("/"))
    bin_dir = root / "bin"
    models_dir = root / "models"
    config_dir = root / "config"
    state_dir = root / "state"
    logs_dir = root / "logs"
    return NativeAndroidRuntimeLayout(
        root=root,
        bin_dir=bin_dir,
        models_dir=models_dir,
        config_dir=config_dir,
        state_dir=state_dir,
        logs_dir=logs_dir,
        remote_llama_server=bin_dir / "llama-server",
        remote_model=models_dir / config.model.gguf_path.name,
        remote_manifest=config_dir / "native-runtime-manifest.json",
    )


def build_native_android_runtime_install_plan(
    config: NativeRuntimeConfig,
    manifest: NativeRuntimeManifest,
    *,
    local_llama_server: Path,
    local_manifest: Path,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
) -> NativeAndroidRuntimeInstallPlan:
    layout = build_native_android_runtime_layout(config, remote_root=remote_root)
    mkdir_targets = (
        layout.bin_dir,
        layout.models_dir,
        layout.config_dir,
        layout.state_dir,
        layout.logs_dir,
    )
    mkdir_command = _adb_command(("shell", "mkdir", "-p", *(str(path) for path in mkdir_targets)), serial)
    support_libraries = _discover_support_libraries(local_llama_server)
    assets = (
        NativeAndroidRuntimeAsset("llama-server", local_llama_server, layout.remote_llama_server),
        *(
            NativeAndroidRuntimeAsset(f"library:{library.name}", library, layout.bin_dir / library.name)
            for library in support_libraries
        ),
        NativeAndroidRuntimeAsset(config.model.gguf_path.name, config.model.gguf_path, layout.remote_model),
        NativeAndroidRuntimeAsset("manifest", local_manifest, layout.remote_manifest),
    )
    commands = (
        mkdir_command,
        *(_adb_command(("push", str(asset.local_path), str(asset.remote_path)), serial) for asset in assets),
        _adb_command(("shell", "chmod", "+x", str(layout.remote_llama_server)), serial),
        _adb_command(("forward", f"tcp:{config.port}", f"tcp:{config.port}"), serial),
    )
    return NativeAndroidRuntimeInstallPlan(
        layout=layout,
        commands=commands,
        instructions=(
            f"Remote root: {layout.root}",
            f"Remote runtime binary: {layout.remote_llama_server}",
            f"Support libraries: {len(support_libraries)} sibling .so file(s) copied to {layout.bin_dir}",
            f"Remote model: {layout.remote_model}",
            f"Remote manifest: {layout.remote_manifest}",
            f"Engine: {manifest.engine}",
            "After install, run the remote llama-server command from an Android shell or companion app lane.",
        ),
        support_libraries=support_libraries,
        assets=assets,
    )


def build_native_android_runtime_start_plan(
    config: NativeRuntimeConfig,
    *,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
) -> NativeAndroidRuntimeStartPlan:
    layout = build_native_android_runtime_layout(config, remote_root=remote_root)
    remote_pid_file = layout.state_dir / "llama-server.pid"
    remote_log_file = layout.logs_dir / "llama-server.log"
    remote_start_shell = _remote_start_shell(config, layout, remote_pid_file, remote_log_file)
    return NativeAndroidRuntimeStartPlan(
        layout=layout,
        commands=(
            _adb_command(("shell", remote_start_shell), serial),
            _adb_command(("forward", f"tcp:{config.port}", f"tcp:{config.port}"), serial),
        ),
        remote_pid_file=remote_pid_file,
        remote_log_file=remote_log_file,
        remote_start_shell=remote_start_shell,
    )


def build_native_android_runtime_status_plan(
    config: NativeRuntimeConfig,
    *,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
) -> NativeAndroidRuntimeStatusPlan:
    layout = build_native_android_runtime_layout(config, remote_root=remote_root)
    remote_pid_file = layout.state_dir / "llama-server.pid"
    remote_log_file = layout.logs_dir / "llama-server.log"
    return NativeAndroidRuntimeStatusPlan(
        layout=layout,
        commands=(
            _adb_command(("shell", _remote_status_shell(remote_pid_file, remote_log_file)), serial),
            _adb_command(("forward", f"tcp:{config.port}", f"tcp:{config.port}"), serial),
        ),
        remote_pid_file=remote_pid_file,
        remote_log_file=remote_log_file,
    )


def build_native_android_runtime_stop_plan(
    config: NativeRuntimeConfig,
    *,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
) -> NativeAndroidRuntimeStopPlan:
    layout = build_native_android_runtime_layout(config, remote_root=remote_root)
    remote_pid_file = layout.state_dir / "llama-server.pid"
    return NativeAndroidRuntimeStopPlan(
        layout=layout,
        commands=(
            _adb_command(("shell", _remote_stop_shell(remote_pid_file)), serial),
            _adb_command(("forward", "--remove", f"tcp:{config.port}"), serial),
        ),
        remote_pid_file=remote_pid_file,
    )


def build_native_android_runtime_smoke_plan(
    config: NativeRuntimeConfig,
    *,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
    prompt: str = DEFAULT_TEST_PROMPT,
) -> NativeAndroidRuntimeSmokePlan:
    layout = build_native_android_runtime_layout(config, remote_root=remote_root)
    api_base = config.api_base
    return NativeAndroidRuntimeSmokePlan(
        layout=layout,
        commands=(
            _adb_command(("forward", f"tcp:{config.port}", f"tcp:{config.port}"), serial),
            _build_llamacpp_health_command(api_base),
            _build_llamacpp_models_command(api_base),
            _build_llamacpp_completion_command(prompt, api_base),
        ),
        api_base=api_base,
        model=config.model.gguf_path.name,
        prompt=prompt,
    )


def build_native_android_runtime_smoke_path_plan(
    config: NativeRuntimeConfig,
    manifest: NativeRuntimeManifest,
    *,
    local_llama_server: Path,
    local_manifest: Path,
    remote_root: str = DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    serial: str | None = None,
    prompt: str = DEFAULT_TEST_PROMPT,
) -> NativeAndroidRuntimeSmokePathPlan:
    return NativeAndroidRuntimeSmokePathPlan(
        install_plan=build_native_android_runtime_install_plan(
            config,
            manifest,
            local_llama_server=local_llama_server,
            local_manifest=local_manifest,
            remote_root=remote_root,
            serial=serial,
        ),
        start_plan=build_native_android_runtime_start_plan(
            config,
            remote_root=remote_root,
            serial=serial,
        ),
        smoke_plan=build_native_android_runtime_smoke_plan(
            config,
            remote_root=remote_root,
            serial=serial,
            prompt=prompt,
        ),
    )


def render_native_android_runtime_install_plan(plan: NativeAndroidRuntimeInstallPlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime install plan",
        f"Remote root: {plan.layout.root}",
        f"Remote binary: {plan.layout.remote_llama_server}",
        f"Support libraries: {len(plan.support_libraries)}",
        f"Remote model: {plan.layout.remote_model}",
        f"Remote manifest: {plan.layout.remote_manifest}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    lines.append("Instructions:")
    lines.extend(f"- {instruction}" for instruction in plan.instructions)
    return tuple(lines)


def render_native_android_runtime_status_plan(plan: NativeAndroidRuntimeStatusPlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime status plan",
        f"Remote root: {plan.layout.root}",
        f"Remote PID file: {plan.remote_pid_file}",
        f"Remote log file: {plan.remote_log_file}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    return tuple(lines)


def render_native_android_runtime_stop_plan(plan: NativeAndroidRuntimeStopPlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime stop plan",
        f"Remote root: {plan.layout.root}",
        f"Remote PID file: {plan.remote_pid_file}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    return tuple(lines)


def render_native_android_runtime_start_plan(plan: NativeAndroidRuntimeStartPlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime start plan",
        f"Remote root: {plan.layout.root}",
        f"Remote PID file: {plan.remote_pid_file}",
        f"Remote log file: {plan.remote_log_file}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    return tuple(lines)


def render_native_android_runtime_smoke_plan(plan: NativeAndroidRuntimeSmokePlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime smoke plan",
        f"Remote root: {plan.layout.root}",
        f"API base: {plan.api_base}",
        f"Expected model: {plan.model}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    return tuple(lines)


def render_native_android_runtime_smoke_path_plan(plan: NativeAndroidRuntimeSmokePathPlan) -> tuple[str, ...]:
    lines = ["Native Android runtime smoke path"]
    lines.extend(render_native_android_runtime_install_plan(plan.install_plan))
    lines.extend(render_native_android_runtime_start_plan(plan.start_plan))
    lines.extend(render_native_android_runtime_smoke_plan(plan.smoke_plan))
    return tuple(lines)


def _adb_command(args: tuple[str, ...], serial: str | None) -> Command:
    if serial:
        return ("adb", "-s", serial, *args)
    return ("adb", *args)


def _build_llamacpp_health_command(api_base_url: str) -> Command:
    return ("curl", "--silent", "--show-error", "--max-time", "30", f"{api_base_url.rstrip('/')}/health")


def _build_llamacpp_models_command(api_base_url: str) -> Command:
    return ("curl", "--silent", "--show-error", "--max-time", "30", f"{api_base_url.rstrip('/')}/v1/models")


def _build_llamacpp_completion_command(prompt: str, api_base_url: str) -> Command:
    payload = json.dumps(
        {
            "prompt": prompt,
            "n_predict": 16,
            "stream": False,
        },
        separators=(",", ":"),
    )
    return (
        "curl",
        "--silent",
        "--show-error",
        "--max-time",
        "90",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-d",
        payload,
        f"{api_base_url.rstrip('/')}/completion",
    )


def _remote_start_shell(
    config: NativeRuntimeConfig,
    layout: NativeAndroidRuntimeLayout,
    remote_pid_file: PurePosixPath,
    remote_log_file: PurePosixPath,
) -> str:
    args = [
        str(layout.remote_llama_server),
        "--model",
        str(layout.remote_model),
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
    command = " ".join(args)
    return (
        f"mkdir -p {layout.state_dir} {layout.logs_dir}; "
        f"export LD_LIBRARY_PATH={layout.bin_dir}:$LD_LIBRARY_PATH; "
        f"nohup {command} > {remote_log_file} 2>&1 < /dev/null & "
        f"echo $! > {remote_pid_file}"
    )


def _remote_status_shell(remote_pid_file: PurePosixPath, remote_log_file: PurePosixPath) -> str:
    return (
        f"if [ -f {remote_pid_file} ]; then "
        f"pid=$(cat {remote_pid_file}); "
        f"if kill -0 $pid 2>/dev/null; then echo running:$pid; else echo stale:$pid; fi; "
        f"else echo missing; fi; "
        f"tail -n 20 {remote_log_file} 2>/dev/null || true"
    )


def _remote_stop_shell(remote_pid_file: PurePosixPath) -> str:
    return (
        f"if [ -f {remote_pid_file} ]; then "
        f"pid=$(cat {remote_pid_file}); "
        f"kill $pid 2>/dev/null || true; "
        f"rm -f {remote_pid_file}; "
        f"echo stopped:$pid; "
        f"else echo missing; fi"
    )


def _discover_support_libraries(local_llama_server: Path) -> tuple[Path, ...]:
    binary_dir = local_llama_server.parent
    if not binary_dir.exists():
        return ()
    return tuple(sorted(binary_dir.glob("*.so"), key=lambda path: path.name))
