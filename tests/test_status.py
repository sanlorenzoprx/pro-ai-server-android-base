from pro_ai_server.ide import IdeCli, IdeExtensionStatus
from pro_ai_server.native_runtime import NativeRuntimeLifecycleStatus, NativeRuntimeReadiness, NativeRuntimeState
from pro_ai_server.ollama import OllamaServerStatus
from pro_ai_server.status import build_status_report, render_status_report


def test_status_report_marks_ready_phone_tunnel_server_and_ide():
    report = build_status_report(
        "List of devices attached\nABC123\tdevice\n",
        "ABC123 tcp:11434 tcp:11434\n",
        OllamaServerStatus(ok=True, model_names=("qwen2.5-coder:3b",)),
        (
            IdeExtensionStatus(
                ide=IdeCli(command="cursor", path="C:/bin/cursor.cmd"),
                extension_id="Continue.continue",
                installed=True,
            ),
        ),
        adb_path="adb",
    )

    rendered = "\n".join(render_status_report(report))

    assert report.ok
    assert "OK Phone: connected (ABC123)" in rendered
    assert "OK USB tunnel: adb forward tcp:11434 is active" in rendered
    assert "OK Exposure: USB/local endpoint only" in rendered
    assert "OK Ollama: responding on /api/tags (1 model)" in rendered
    assert "Unknown Native runtime: not configured" in rendered
    assert "OK IDE: Continue ready in cursor" in rendered


def test_status_report_marks_missing_pieces():
    report = build_status_report(
        "",
        "",
        OllamaServerStatus(ok=False, warnings=("Ollama did not return a response.",)),
        (
            IdeExtensionStatus(
                ide=IdeCli(command="cursor", path="C:/bin/cursor.cmd"),
                extension_id="Continue.continue",
                installed=False,
            ),
        ),
        adb_path="adb",
    )

    rendered = "\n".join(render_status_report(report))

    assert not report.ok
    assert "Needs attention Phone: No ADB devices found" in rendered
    assert "Needs attention USB tunnel: adb forward tcp:11434 is not active" in rendered
    assert "OK Exposure: USB/local endpoint only" in rendered
    assert "Needs attention Ollama: Ollama did not return a response." in rendered
    assert "Unknown Native runtime: not configured" in rendered
    assert "Needs attention IDE: Continue extension missing in cursor" in rendered


def test_status_report_marks_non_localhost_endpoint_as_advanced_exposure():
    report = build_status_report(
        "List of devices attached\nABC123\tdevice\n",
        "",
        OllamaServerStatus(ok=True, model_names=("qwen2.5-coder:3b",)),
        (),
        adb_path="adb",
        api_base="http://192.168.1.50:11434",
    )

    rendered = "\n".join(render_status_report(report))

    assert "Unknown Exposure: advanced endpoint configured: http://192.168.1.50:11434" in rendered


def test_status_report_marks_ready_native_runtime():
    native_status = NativeRuntimeLifecycleStatus(
        state=NativeRuntimeState(
            pid=4321,
            command=("llama-server",),
            api_base="http://127.0.0.1:11434",
            model="qwen2.5-coder:3b",
            gguf_path="model.gguf",
            started_at="2026-05-07T00:00:00+00:00",
        ),
        process_running=True,
        readiness=NativeRuntimeReadiness(ok=True, attempts=1, detail="runtime responded on /api/tags"),
    )
    report = build_status_report(
        "List of devices attached\nABC123\tdevice\n",
        "ABC123 tcp:11434 tcp:11434\n",
        OllamaServerStatus(ok=True, model_names=("qwen2.5-coder:3b",)),
        (),
        adb_path="adb",
        native_runtime_status=native_status,
    )

    rendered = "\n".join(render_status_report(report))

    assert "OK Native runtime: ready (qwen2.5-coder:3b, PID 4321)" in rendered


def test_status_report_marks_stale_native_runtime_state():
    native_status = NativeRuntimeLifecycleStatus(
        state=NativeRuntimeState(
            pid=4321,
            command=("llama-server",),
            api_base="http://127.0.0.1:11434",
            model="qwen2.5-coder:3b",
            gguf_path="model.gguf",
            started_at="2026-05-07T00:00:00+00:00",
        ),
        process_running=False,
        readiness=NativeRuntimeReadiness(ok=False, attempts=1, detail="connection refused"),
        stale_state=True,
    )
    report = build_status_report(
        "List of devices attached\nABC123\tdevice\n",
        "ABC123 tcp:11434 tcp:11434\n",
        OllamaServerStatus(ok=True, model_names=("qwen2.5-coder:3b",)),
        (),
        adb_path="adb",
        native_runtime_status=native_status,
    )

    rendered = "\n".join(render_status_report(report))

    assert not report.ok
    assert "Needs attention Native runtime: stale state for PID 4321" in rendered
