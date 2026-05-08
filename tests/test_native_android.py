from pathlib import Path

from pro_ai_server.models import model_plan_for_profile
from pro_ai_server.native_android import (
    DEFAULT_ANDROID_NATIVE_RUNTIME_ROOT,
    build_native_android_runtime_install_plan,
    build_native_android_runtime_layout,
    build_native_android_runtime_smoke_plan,
    build_native_android_runtime_smoke_path_plan,
    build_native_android_runtime_start_plan,
    build_native_android_runtime_status_plan,
    build_native_android_runtime_stop_plan,
    render_native_android_runtime_install_plan,
    render_native_android_runtime_smoke_plan,
    render_native_android_runtime_smoke_path_plan,
    render_native_android_runtime_start_plan,
    render_native_android_runtime_status_plan,
    render_native_android_runtime_stop_plan,
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
    assert [asset.key for asset in plan.assets] == [
        "llama-server",
        "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf",
        "manifest",
    ]
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


def test_build_native_android_runtime_install_plan_pushes_sibling_support_libraries(tmp_path):
    manifest = load_native_runtime_manifest()
    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("lightweight"),
        models_root=Path("models"),
        prefer="autocomplete",
        manifest=manifest,
    )
    binary = tmp_path / "llama-server"
    library_a = tmp_path / "libggml.so"
    library_b = tmp_path / "libllama-common.so"
    binary.write_text("binary")
    library_b.write_text("lib")
    library_a.write_text("lib")

    plan = build_native_android_runtime_install_plan(
        config,
        manifest,
        local_llama_server=binary,
        local_manifest=Path("native-runtime-manifest.json"),
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
    )

    assert plan.support_libraries == (library_a, library_b)
    assert ("adb", "-s", "ABC123", "push", str(library_a), "/data/local/tmp/pro-ai/bin/libggml.so") in plan.commands
    assert (
        "adb",
        "-s",
        "ABC123",
        "push",
        str(library_b),
        "/data/local/tmp/pro-ai/bin/libllama-common.so",
    ) in plan.commands


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


def test_build_native_android_runtime_start_plan_runs_remote_llama_server_and_forwards_port():
    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("professional"),
        models_root=Path("models"),
    )

    plan = build_native_android_runtime_start_plan(
        config,
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
    )

    assert plan.commands[0][0:4] == ("adb", "-s", "ABC123", "shell")
    assert "/data/local/tmp/pro-ai/bin/llama-server" in plan.remote_start_shell
    assert "--model /data/local/tmp/pro-ai/models/qwen2.5-coder-3b-instruct-q4_k_m.gguf" in plan.remote_start_shell
    assert "export LD_LIBRARY_PATH=/data/local/tmp/pro-ai/bin:$LD_LIBRARY_PATH" in plan.remote_start_shell
    assert "nohup" in plan.remote_start_shell
    assert "echo $!" in plan.remote_start_shell
    assert plan.commands[1] == ("adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434")


def test_render_native_android_runtime_start_plan_is_operator_readable():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))
    plan = build_native_android_runtime_start_plan(config)

    rendered = "\n".join(render_native_android_runtime_start_plan(plan))

    assert "Native Android runtime start plan" in rendered
    assert "Remote PID file:" in rendered
    assert "Remote log file:" in rendered
    assert "Commands:" in rendered


def test_build_native_android_runtime_status_plan_checks_remote_pid_and_log():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))

    plan = build_native_android_runtime_status_plan(
        config,
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
    )

    assert plan.commands[0][0:4] == ("adb", "-s", "ABC123", "shell")
    assert "kill -0 $pid" in plan.commands[0][4]
    assert "tail -n 20 /data/local/tmp/pro-ai/logs/llama-server.log" in plan.commands[0][4]
    assert plan.commands[1] == ("adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434")


def test_build_native_android_runtime_stop_plan_stops_recorded_pid_and_removes_forward():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))

    plan = build_native_android_runtime_stop_plan(
        config,
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
    )

    assert plan.commands[0][0:4] == ("adb", "-s", "ABC123", "shell")
    assert "kill $pid" in plan.commands[0][4]
    assert "rm -f /data/local/tmp/pro-ai/state/llama-server.pid" in plan.commands[0][4]
    assert plan.commands[1] == ("adb", "-s", "ABC123", "forward", "--remove", "tcp:11434")


def test_render_native_android_runtime_status_and_stop_plans_are_operator_readable():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))
    status_plan = build_native_android_runtime_status_plan(config)
    stop_plan = build_native_android_runtime_stop_plan(config)

    rendered_status = "\n".join(render_native_android_runtime_status_plan(status_plan))
    rendered_stop = "\n".join(render_native_android_runtime_stop_plan(stop_plan))

    assert "Native Android runtime status plan" in rendered_status
    assert "Remote log file:" in rendered_status
    assert "Native Android runtime stop plan" in rendered_stop
    assert "Remote PID file:" in rendered_stop


def test_build_native_android_runtime_smoke_plan_checks_forwarded_api():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))

    plan = build_native_android_runtime_smoke_plan(
        config,
        remote_root="/data/local/tmp/pro-ai",
        serial="ABC123",
        prompt="ready?",
    )

    assert plan.commands[0] == ("adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434")
    assert plan.commands[1] == ("curl", "--silent", "--show-error", "--max-time", "30", "http://127.0.0.1:11434/health")
    assert plan.commands[2] == (
        "curl",
        "--silent",
        "--show-error",
        "--max-time",
        "30",
        "http://127.0.0.1:11434/v1/models",
    )
    assert plan.commands[3][0:9] == (
        "curl",
        "--silent",
        "--show-error",
        "--max-time",
        "90",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
    )
    assert "ready?" in plan.commands[3][10]
    assert plan.commands[3][-1] == "http://127.0.0.1:11434/completion"


def test_render_native_android_runtime_smoke_plan_is_operator_readable():
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"))
    plan = build_native_android_runtime_smoke_plan(config)

    rendered = "\n".join(render_native_android_runtime_smoke_plan(plan))

    assert "Native Android runtime smoke plan" in rendered
    assert "API base:" in rendered
    assert "Expected model:" in rendered
    assert "Commands:" in rendered


def test_build_native_android_runtime_smoke_path_plan_chains_install_start_and_smoke():
    manifest = load_native_runtime_manifest()
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"), manifest=manifest)

    plan = build_native_android_runtime_smoke_path_plan(
        config,
        manifest,
        local_llama_server=Path("llama-server"),
        local_manifest=Path("native-runtime-manifest.json"),
        serial="ABC123",
    )

    assert plan.install_plan.commands
    assert plan.start_plan.commands
    assert plan.smoke_plan.commands
    assert plan.install_plan.layout == plan.start_plan.layout == plan.smoke_plan.layout
    assert plan.smoke_plan.commands[0] == ("adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434")


def test_render_native_android_runtime_smoke_path_plan_is_operator_readable():
    manifest = load_native_runtime_manifest()
    config = build_native_runtime_config_for_model_plan(model_plan_for_profile("professional"), manifest=manifest)
    plan = build_native_android_runtime_smoke_path_plan(
        config,
        manifest,
        local_llama_server=Path("llama-server"),
        local_manifest=Path("native-runtime-manifest.json"),
    )

    rendered = "\n".join(render_native_android_runtime_smoke_path_plan(plan))

    assert "Native Android runtime smoke path" in rendered
    assert "Native Android runtime install plan" in rendered
    assert "Native Android runtime start plan" in rendered
    assert "Native Android runtime smoke plan" in rendered
