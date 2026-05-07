from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pro_ai_server.native_runtime import NativeRuntimeConfig, NativeRuntimeManifest


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
class NativeAndroidRuntimeInstallPlan:
    layout: NativeAndroidRuntimeLayout
    commands: tuple[Command, ...]
    instructions: tuple[str, ...]


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
    commands = (
        mkdir_command,
        _adb_command(("push", str(local_llama_server), str(layout.remote_llama_server)), serial),
        _adb_command(("push", str(config.model.gguf_path), str(layout.remote_model)), serial),
        _adb_command(("push", str(local_manifest), str(layout.remote_manifest)), serial),
        _adb_command(("shell", "chmod", "+x", str(layout.remote_llama_server)), serial),
        _adb_command(("forward", f"tcp:{config.port}", f"tcp:{config.port}"), serial),
    )
    return NativeAndroidRuntimeInstallPlan(
        layout=layout,
        commands=commands,
        instructions=(
            f"Remote root: {layout.root}",
            f"Remote runtime binary: {layout.remote_llama_server}",
            f"Remote model: {layout.remote_model}",
            f"Remote manifest: {layout.remote_manifest}",
            f"Engine: {manifest.engine}",
            "After install, run the remote llama-server command from an Android shell or companion app lane.",
        ),
    )


def render_native_android_runtime_install_plan(plan: NativeAndroidRuntimeInstallPlan) -> tuple[str, ...]:
    lines = [
        "Native Android runtime install plan",
        f"Remote root: {plan.layout.root}",
        f"Remote binary: {plan.layout.remote_llama_server}",
        f"Remote model: {plan.layout.remote_model}",
        f"Remote manifest: {plan.layout.remote_manifest}",
        "Commands:",
    ]
    lines.extend(" ".join(command) for command in plan.commands)
    lines.append("Instructions:")
    lines.extend(f"- {instruction}" for instruction in plan.instructions)
    return tuple(lines)


def _adb_command(args: tuple[str, ...], serial: str | None) -> Command:
    if serial:
        return ("adb", "-s", serial, *args)
    return ("adb", *args)
