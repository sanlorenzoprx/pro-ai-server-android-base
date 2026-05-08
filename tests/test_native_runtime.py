from pathlib import Path

import pytest

from pro_ai_server.native_runtime import (
    DEFAULT_NATIVE_RUNTIME_HOST,
    DEFAULT_NATIVE_RUNTIME_PORT,
    NativeRuntimeProcess,
    NativeRuntimeConfig,
    NativeRuntimeError,
    NativeRuntimeManifest,
    NativeRuntimeModel,
    NativeRuntimeProfileDefaults,
    build_llama_server_command,
    build_native_runtime_asset_report,
    build_native_runtime_config_for_model_plan,
    build_native_runtime_doctor_report,
    build_native_runtime_lifecycle_status,
    build_native_runtime_launch_plan,
    build_native_runtime_model,
    build_native_runtime_state,
    build_native_runtime_chat_response,
    build_native_runtime_generate_response,
    build_native_runtime_health_response,
    build_native_runtime_tags_response,
    default_native_runtime_state_path,
    load_native_runtime_manifest,
    native_runtime_defaults_for_profile,
    remove_native_runtime_state,
    render_native_runtime_asset_report,
    render_native_runtime_launch_plan,
    render_native_runtime_lifecycle_status,
    render_native_runtime_doctor_report,
    stop_native_runtime,
    start_native_runtime_process,
    validate_native_runtime_config,
    wait_for_native_runtime_readiness,
    write_native_runtime_state,
)
from pro_ai_server.models import model_plan_for_profile


def make_model() -> NativeRuntimeModel:
    return NativeRuntimeModel(
        contract_name="qwen2.5-coder:1.5b",
        gguf_path=Path("models") / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    )


def test_native_runtime_model_inventory_entry_uses_contract_name():
    model = make_model()

    assert model.to_inventory_entry() == {"name": "qwen2.5-coder:1.5b"}


def test_native_runtime_config_defaults_match_host_contract_shape():
    config = NativeRuntimeConfig(model=make_model())

    assert config.host == DEFAULT_NATIVE_RUNTIME_HOST
    assert config.port == DEFAULT_NATIVE_RUNTIME_PORT
    assert config.api_base == "http://127.0.0.1:11434"


def test_validate_native_runtime_config_accepts_valid_settings():
    validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), threads=6, gpu_layers=4))


def test_validate_native_runtime_config_rejects_invalid_values():
    with pytest.raises(ValueError, match="contract name"):
        validate_native_runtime_config(
            NativeRuntimeConfig(
                model=NativeRuntimeModel(contract_name=" ", gguf_path=Path("models") / "test.gguf")
            )
        )

    with pytest.raises(ValueError, match="port"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), port=0))

    with pytest.raises(ValueError, match="context length"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), context_length=0))

    with pytest.raises(ValueError, match="threads"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), threads=0))

    with pytest.raises(ValueError, match="GPU layers"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), gpu_layers=-1))


def test_native_runtime_response_builders_match_wrapper_contract_shapes():
    assert build_native_runtime_health_response() == {
        "status": "ok",
        "engine": "llama.cpp",
        "runtime": "native-wrapper",
    }
    assert build_native_runtime_tags_response(make_model()) == {
        "models": [{"name": "qwen2.5-coder:1.5b"}]
    }
    assert build_native_runtime_tags_response(None) == {"models": []}
    assert build_native_runtime_generate_response("pro-ai-server-ready") == {
        "response": "pro-ai-server-ready"
    }
    assert build_native_runtime_chat_response("hello") == {
        "message": {"role": "assistant", "content": "hello"}
    }


def test_native_runtime_error_dict_shape_is_stable():
    error = NativeRuntimeError(error="model_not_loaded", message="Requested model is not loaded.")

    assert error.to_dict() == {
        "error": "model_not_loaded",
        "message": "Requested model is not loaded.",
    }


def test_native_runtime_defaults_exist_for_known_profiles():
    lightweight = native_runtime_defaults_for_profile("lightweight")
    professional = native_runtime_defaults_for_profile("professional")
    maximum = native_runtime_defaults_for_profile("max")

    assert lightweight.chat_model_filename.endswith(".gguf")
    assert professional.context_length >= lightweight.context_length
    assert maximum.threads >= professional.threads


def test_load_native_runtime_manifest_reads_packaged_profile_defaults():
    manifest = load_native_runtime_manifest()

    assert manifest.engine == "llama.cpp"
    assert "lightweight" in manifest.profiles
    assert manifest.profiles["professional"].chat_model_filename == "qwen2.5-coder-3b-instruct-q4_k_m.gguf"


def test_load_native_runtime_manifest_reads_custom_file(tmp_path):
    manifest_path = tmp_path / "native-runtime-manifest.json"
    manifest_path.write_text(
        """{
          "engine": "test-engine",
          "policy": "test policy",
          "profiles": {
            "test": {
              "chat_model_filename": "chat.gguf",
              "autocomplete_model_filename": "autocomplete.gguf",
              "context_length": 2048,
              "threads": 2,
              "gpu_layers": 1
            }
          }
        }""",
        encoding="utf-8",
    )

    manifest = load_native_runtime_manifest(manifest_path)

    assert manifest.engine == "test-engine"
    assert manifest.policy == "test policy"
    assert manifest.profiles["test"] == NativeRuntimeProfileDefaults(
        chat_model_filename="chat.gguf",
        autocomplete_model_filename="autocomplete.gguf",
        context_length=2048,
        threads=2,
        gpu_layers=1,
    )


def test_load_native_runtime_manifest_rejects_empty_profiles(tmp_path):
    manifest_path = tmp_path / "native-runtime-manifest.json"
    manifest_path.write_text('{"profiles": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="at least one profile"):
        load_native_runtime_manifest(manifest_path)


def test_native_runtime_defaults_reject_unknown_profile():
    with pytest.raises(ValueError, match="Unknown native runtime profile"):
        native_runtime_defaults_for_profile("tiny")


def test_build_native_runtime_model_uses_models_root_and_filename():
    model = build_native_runtime_model(
        "qwen2.5-coder:3b",
        "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        models_root=Path("bundled-models"),
    )

    assert model.contract_name == "qwen2.5-coder:3b"
    assert model.gguf_path == Path("bundled-models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"


def test_build_native_runtime_config_for_model_plan_prefers_chat_model():
    plan = model_plan_for_profile("professional")

    config = build_native_runtime_config_for_model_plan(
        plan,
        models_root=Path("bundled-models"),
        prefer="chat",
    )

    assert config.model.contract_name == "qwen2.5-coder:3b"
    assert config.model.gguf_path == Path("bundled-models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    assert config.context_length == 8192
    assert config.threads == 6


def test_build_native_runtime_config_for_model_plan_can_use_custom_manifest():
    manifest = NativeRuntimeManifest(
        engine="test",
        policy="test",
        profiles={
            "professional": NativeRuntimeProfileDefaults(
                chat_model_filename="custom-chat.gguf",
                autocomplete_model_filename="custom-autocomplete.gguf",
                context_length=2048,
                threads=2,
                gpu_layers=1,
            )
        },
    )

    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("professional"),
        models_root=Path("custom-models"),
        manifest=manifest,
    )

    assert config.model.contract_name == "qwen2.5-coder:3b"
    assert config.model.gguf_path == Path("custom-models") / "custom-chat.gguf"
    assert config.context_length == 2048
    assert config.threads == 2
    assert config.gpu_layers == 1


def test_build_native_runtime_config_for_model_plan_can_prefer_autocomplete_model():
    plan = model_plan_for_profile("lightweight")

    config = build_native_runtime_config_for_model_plan(
        plan,
        models_root=Path("bundled-models"),
        prefer="autocomplete",
    )

    assert config.model.contract_name == "qwen2.5-coder:0.5b"
    assert config.model.gguf_path == Path("bundled-models") / "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"


def test_build_native_runtime_asset_report_checks_binary_and_profile_models(tmp_path):
    llama_server = tmp_path / "llama-server"
    models_root = tmp_path / "models"
    model_file = models_root / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    llama_server.write_text("binary", encoding="utf-8")
    models_root.mkdir()
    model_file.write_text("model", encoding="utf-8")

    report = build_native_runtime_asset_report(
        "professional",
        models_root=models_root,
        executable=llama_server,
    )

    assert not report.ready
    assert [check.key for check in report.checks] == [
        "llama-server",
        "model:qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "model:qwen2.5-coder-1.5b-base-q4_k_m.gguf",
    ]
    assert report.checks[0].ok is True
    assert report.checks[1].ok is True
    assert report.checks[2].ok is False


def test_render_native_runtime_asset_report_is_operator_readable(tmp_path):
    report = build_native_runtime_asset_report(
        "lightweight",
        models_root=tmp_path / "models",
        executable=tmp_path / "llama-server",
    )

    rendered = "\n".join(render_native_runtime_asset_report(report))

    assert "Native runtime asset readiness" in rendered
    assert "Ready: False" in rendered
    assert "Profile: lightweight" in rendered
    assert "Missing llama-server" in rendered
    assert "Next: place missing assets" in rendered


def test_build_native_runtime_config_for_model_plan_rejects_invalid_preference():
    with pytest.raises(ValueError, match="prefer value"):
        build_native_runtime_config_for_model_plan(model_plan_for_profile("lightweight"), prefer="summary")


def test_build_llama_server_command_uses_wrapper_config_values():
    config = NativeRuntimeConfig(
        model=NativeRuntimeModel(
            contract_name="qwen2.5-coder:3b",
            gguf_path=Path("models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        ),
        host="127.0.0.1",
        port=11434,
        context_length=8192,
        threads=6,
    )

    command = build_llama_server_command(config, executable=Path("bin") / "llama-server")

    assert command.command == (
        str(Path("bin") / "llama-server"),
        "--model",
        str(Path("models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"),
        "--host",
        "127.0.0.1",
        "--port",
        "11434",
        "--ctx-size",
        "8192",
        "--threads",
        "6",
    )


def test_build_llama_server_command_includes_gpu_layers_when_enabled():
    command = build_llama_server_command(NativeRuntimeConfig(model=make_model(), gpu_layers=8))

    assert "--n-gpu-layers" in command.args
    assert command.args[-1] == "8"


def test_build_native_runtime_launch_plan_marks_missing_inputs():
    config = NativeRuntimeConfig(model=make_model())

    plan = build_native_runtime_launch_plan(config, executable=Path("missing-llama-server"))

    assert plan.ready is False
    assert [check.key for check in plan.checks] == ["llama-server", "model-file"]
    assert all(check.ok is False for check in plan.checks)


def test_build_native_runtime_launch_plan_marks_ready_inputs(tmp_path):
    executable = tmp_path / "llama-server"
    model_file = tmp_path / "model.gguf"
    executable.write_text("binary", encoding="utf-8")
    model_file.write_text("model", encoding="utf-8")
    config = NativeRuntimeConfig(
        model=NativeRuntimeModel(contract_name="qwen2.5-coder:1.5b", gguf_path=model_file)
    )

    plan = build_native_runtime_launch_plan(config, executable=executable)

    assert plan.ready is True
    assert all(check.ok for check in plan.checks)


def test_render_native_runtime_launch_plan_includes_readiness_and_command():
    plan = build_native_runtime_launch_plan(NativeRuntimeConfig(model=make_model()))

    rendered = "\n".join(render_native_runtime_launch_plan(plan))

    assert "Native runtime launch plan" in rendered
    assert "Ready: False" in rendered
    assert "Model: qwen2.5-coder:1.5b" in rendered
    assert "Command: llama-server --model" in rendered
    assert "Missing llama-server" in rendered
    assert "Missing model-file" in rendered


def test_start_native_runtime_process_rejects_unready_plan_without_force():
    plan = build_native_runtime_launch_plan(NativeRuntimeConfig(model=make_model()))

    with pytest.raises(ValueError, match="not ready"):
        start_native_runtime_process(plan)


def test_start_native_runtime_process_uses_command_with_force():
    class FakeProcess:
        pid = 1234

    calls = []

    def fake_popen(command, **kwargs):
        calls.append((command, kwargs))
        return FakeProcess()

    plan = build_native_runtime_launch_plan(NativeRuntimeConfig(model=make_model()))

    process = start_native_runtime_process(plan, force=True, popen=fake_popen)

    assert process.pid == 1234
    assert calls[0][0][0] == "llama-server"
    assert calls[0][1]["close_fds"] is True


def test_wait_for_native_runtime_readiness_accepts_tags_response():
    readiness = wait_for_native_runtime_readiness(
        "http://127.0.0.1:11434",
        timeout_seconds=0.01,
        interval_seconds=0,
        fetch_tags=lambda api_base: '{"models":[]}',
        sleep=lambda _seconds: None,
    )

    assert readiness.ok is True
    assert readiness.attempts == 1


def test_wait_for_native_runtime_readiness_reports_timeout():
    readiness = wait_for_native_runtime_readiness(
        "http://127.0.0.1:11434",
        timeout_seconds=-1,
        interval_seconds=0,
        fetch_tags=lambda api_base: "{}",
        sleep=lambda _seconds: None,
    )

    assert readiness.ok is False
    assert readiness.attempts == 1
    assert "models" in readiness.detail


def test_default_native_runtime_state_path_uses_cache_directory():
    assert default_native_runtime_state_path(Path("repo")) == (
        Path("repo") / ".cache" / "pro-ai-server" / "native-runtime-state.json"
    )


def test_write_and_load_native_runtime_state_round_trip(tmp_path):
    state_path = tmp_path / "native-runtime-state.json"
    process = NativeRuntimeProcess(pid=1234, command=build_llama_server_command(NativeRuntimeConfig(model=make_model())))
    config = NativeRuntimeConfig(model=make_model())

    state = build_native_runtime_state(process, config)
    written = write_native_runtime_state(state, state_path)

    assert written == state_path
    loaded = build_native_runtime_lifecycle_status(
        state_path,
        fetch_tags=lambda api_base: '{"models":[]}',
        process_exists=lambda pid: True,
    )
    assert loaded.state is not None
    assert loaded.state.pid == 1234
    assert loaded.process_running is True
    assert loaded.readiness.ok is True


def test_build_native_runtime_lifecycle_status_reports_missing_state(tmp_path):
    status = build_native_runtime_lifecycle_status(tmp_path / "missing.json")

    assert status.state is None
    assert status.process_running is None
    assert status.readiness.ok is False


def test_build_native_runtime_lifecycle_status_marks_stale_state(tmp_path):
    state_path = tmp_path / "native-runtime-state.json"
    process = NativeRuntimeProcess(pid=1234, command=build_llama_server_command(NativeRuntimeConfig(model=make_model())))
    state = build_native_runtime_state(process, NativeRuntimeConfig(model=make_model()))
    write_native_runtime_state(state, state_path)

    status = build_native_runtime_lifecycle_status(
        state_path,
        fetch_tags=lambda api_base: "{}",
        process_exists=lambda pid: False,
    )

    assert status.stale_state is True
    rendered = "\n".join(render_native_runtime_lifecycle_status(status))
    assert "Warning: recorded PID is not running" in rendered


def test_stop_native_runtime_terminates_recorded_pid_and_removes_state(tmp_path):
    state_path = tmp_path / "native-runtime-state.json"
    process = NativeRuntimeProcess(pid=1234, command=build_llama_server_command(NativeRuntimeConfig(model=make_model())))
    state = build_native_runtime_state(process, NativeRuntimeConfig(model=make_model()))
    write_native_runtime_state(state, state_path)
    terminated = []

    stopped_state, removed = stop_native_runtime(state_path, terminate=lambda pid: terminated.append(pid))

    assert stopped_state is not None
    assert stopped_state.pid == 1234
    assert terminated == [1234]
    assert removed is True
    assert not state_path.exists()


def test_stop_native_runtime_handles_missing_state(tmp_path):
    state, removed = stop_native_runtime(tmp_path / "missing.json")

    assert state is None
    assert removed is False


def test_remove_native_runtime_state_reports_when_file_is_absent(tmp_path):
    assert remove_native_runtime_state(tmp_path / "missing.json") is False


def test_build_native_runtime_doctor_report_combines_launch_and_lifecycle(tmp_path):
    executable = tmp_path / "llama-server"
    models_root = tmp_path / "models"
    model_file = models_root / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    state_path = tmp_path / "native-runtime-state.json"
    models_root.mkdir()
    executable.write_text("binary", encoding="utf-8")
    model_file.write_text("model", encoding="utf-8")
    process = NativeRuntimeProcess(
        pid=1234,
        command=build_llama_server_command(NativeRuntimeConfig(model=make_model())),
    )
    state = build_native_runtime_state(process, NativeRuntimeConfig(model=make_model()))
    write_native_runtime_state(state, state_path)

    report = build_native_runtime_doctor_report(
        model_plan_for_profile("professional"),
        models_root=models_root,
        executable=executable,
        state_path=state_path,
        fetch_tags=lambda api_base: '{"models":[]}',
        process_exists=lambda pid: True,
    )

    assert report.launch_plan.ready is True
    assert report.lifecycle_status.readiness.ok is True
    assert report.ready is True


def test_render_native_runtime_doctor_report_includes_preflight_summary():
    report = build_native_runtime_doctor_report(
        model_plan_for_profile("professional"),
        state_path=Path("missing-state.json"),
        fetch_tags=lambda api_base: "{}",
        process_exists=lambda pid: False,
    )

    rendered = "\n".join(render_native_runtime_doctor_report(report))

    assert "Native runtime doctor" in rendered
    assert "Engine: llama.cpp" in rendered
    assert "Profile ready: False" in rendered
    assert "Lifecycle ready: False" in rendered
    assert "Overall ready: False" in rendered
