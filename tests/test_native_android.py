from pathlib import Path

from pro_ai_server.models import model_plan_for_profile
from pro_ai_server.native_android import (
    DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    build_native_android_runtime_install_plan,
    build_native_android_runtime_layout,
    render_native_android_runtime_install_plan,
)
from pro_ai_server.native_runtime import build_native_runtime_config_for_model_plan, load_native_runtime_manifest


def test_build_native_android_runtime_layout_uses_expected_directories():
    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("professional"),
        models_root=Path("models"),
    )

    layout = build_native_android_runtime_layout(config)

    assert str(layout.root) == DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT
    assert str(layout.remote_llama_server).endswith("/bin/llama-server")
    assert str(layout.remote_model).endswith("/models/qwen2.5-coder-3b-instruct-q4_k_m.gguf")
    assert str(layout.remote_manifest).endswith("/config/native-runtime-manifest.json")


def test_build_native_android_runtime_install_plan_includes_serial_and_pushes_assets():
    manifest = load_native_runtime_manifest()
    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("lightweight"),
        models_root=Path("models"),
        prefer="autocomplete",
        manifest=manifest,
    )

    plan = build_native_android_runtime_install_plan(
        config,
        manifest,
        local_llama_server=Path("bin") / "llama-server",
        local_manifest=Path("native-runtime-manifest.json"),
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
    )

    assert plan.commands[0][:3] == ("adb", "-s", "ABC123")
    assert (
        "adb",
        "-s",
        "ABC123",
        "push",
        str(Path("bin") / "llama-server"),
        "/data/local/tmp/pro-ai/bin/llama-server",
    ) in plan.commands
    assert (
        "adb",
        "-s",
        "ABC123",
        "push",
        str(Path("models") / "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"),
        "/data/local/tmp/pro-ai/models/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
    ) in plan.commands
    assert ("adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434") in plan.commands


def test_render_native_android_runtime_install_plan_is_operator_readable():
    manifest = load_native_runtime_manifest()
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"), manifest=manifest)
    plan = build_native_android_runtime_install_plan(
        config,
        manifest,
        local_llama_server=Path("llama-server"),
        local_manifest=Path("native-runtime-manifest.json"),
    )

    rendered = "\n".join(render_native_android_runtime_install_plan(plan))

    assert "Native Android runtime install plan" in rendered
    assert "Remote binary:" in rendered
    assert "Commands:" in rendered
    assert "Instructions:" in rendered
