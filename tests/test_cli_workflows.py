from typer.testing import CliRunner

from pro_ai_server import cli
from pro_ai_server.continue_config import ContinueConfigWriteResult
from pro_ai_server.diagnostics import DiagnosticsReport
from pro_ai_server.gateway.ollama_client import OllamaProxyResult
from pro_ai_server.ide import IdeCli, IdeExtensionStatus, IdeReadiness
from pro_ai_server.ollama import OllamaServerStatus
from pro_ai_server.release_validation import ReleaseValidationIssue, ReleaseValidationResult
from pro_ai_server.status import ProAiStatus, StatusItem


def test_setup_prints_plan_without_executing_actions():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["setup", "--mode", "usb", "--no-continue", "--no-tunnel"])

    assert result.exit_code == 0
    assert "Setup plan" in result.output
    assert "Plan only" in result.output
    assert "Generated Termux files" not in result.output


def test_setup_production_prints_state_machine_without_executing_actions():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["setup", "--production", "--mode", "usb", "--no-continue", "--no-tunnel"])

    assert result.exit_code == 0
    assert "Production installer plan" in result.output
    assert "host-checks" in result.output
    assert "android-phone-detection" in result.output
    assert "test-prompt" in result.output
    assert "Plan only" in result.output
    assert "Setup plan" not in result.output


def test_setup_production_rejects_lan_without_advanced_exposure():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["setup", "--production", "--mode", "lan", "--host", "192.168.1.50"])

    assert result.exit_code == 1
    assert "Production installer defaults to USB mode" in result.output
    assert "--advanced-exposure" in result.output


def test_setup_production_allows_lan_with_advanced_exposure():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        ["setup", "--production", "--advanced-exposure", "--mode", "lan", "--host", "192.168.1.50"],
    )

    assert result.exit_code == 0
    assert "Production installer plan" in result.output
    assert "LAN mode exposes Ollama" in result.output
    assert "Plan only" in result.output


def test_installer_ui_preview_prints_mockable_usb_flow():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["installer-ui"])

    assert result.exit_code == 0
    assert "Pro AI Server Installer" in result.output
    assert "Welcome and USB debugging checklist" in result.output
    assert "Advanced network modes visible: no" in result.output
    assert "Success receipt" in result.output


def test_installer_ui_preview_can_render_recoverable_error():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["installer-ui", "--mock-failure", "termux-readiness"])

    assert result.exit_code == 0
    assert "Recoverable error" in result.output
    assert "Mock failure at termux-readiness" in result.output
    assert "mocked step failure: termux-readiness" in result.output


def test_setup_execute_refuses_continue_config_without_yes():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["setup", "--execute"])

    assert result.exit_code == 1
    assert "Refusing to execute without --yes" in result.output


def test_diagnose_writes_output_file(tmp_path, monkeypatch):
    runner = CliRunner()
    output_path = tmp_path / "diagnostics.txt"

    monkeypatch.setattr(cli, "resolve_adb", lambda: None)
    monkeypatch.setattr(cli, "build_diagnostics_report", lambda _: DiagnosticsReport(text="diagnostic text"))

    result = runner.invoke(cli.app, ["diagnose", "--output", str(output_path)])

    assert result.exit_code == 0
    assert output_path.read_text(encoding="utf-8") == "diagnostic text"
    assert "Wrote diagnostics report" in result.output


def test_validate_platform_tools_reports_missing_required_files(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["validate-platform-tools", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "one or more" in result.output
    assert "layouts" in result.output
    assert "adb.exe" in result.output


def test_termux_check_reports_ready_phone(monkeypatch):
    runner = CliRunner()
    outputs = {
        ("adb", "devices"): "List of devices attached\nABC123\tdevice\n",
        ("adb", "-s", "ABC123", "shell", "pm", "path", "com.termux"): "package:/data/app/com.termux/base.apk",
        ("adb", "-s", "ABC123", "shell", "pm", "path", "com.termux.api"): (
            "package:/data/app/com.termux.api/base.apk"
        ),
        (
            "adb",
            "-s",
            "ABC123",
            "shell",
            "test",
            "-d",
            "/data/data/com.termux/files/home",
            "&&",
            "echo",
            "yes",
            "||",
            "echo",
            "no",
        ): "yes",
        ("adb", "-s", "ABC123", "shell", "dumpsys", "package", "com.termux"): "versionName=0.118.1",
    }

    def fake_run(command, capture_output, text):
        import subprocess

        return subprocess.CompletedProcess(command, 0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["termux-check"])

    assert result.exit_code == 0
    assert "Device: ABC123" in result.output
    assert "Termux version: 0.118.1" in result.output
    assert "Termux:API installed" in result.output


def test_termux_check_exits_nonzero_when_api_is_missing(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command[-1] == "com.termux.api":
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        if command[-1] == "com.termux":
            return subprocess.CompletedProcess(command, 0, stdout="package:/data/app/com.termux/base.apk", stderr="")
        if command[-4:] == ["||", "echo", "no"]:
            return subprocess.CompletedProcess(command, 0, stdout="yes", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["termux-check"])

    assert result.exit_code == 1
    assert "Termux:API is not installed" in result.output


def test_validate_release_reports_issues(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "validate_release_layout",
        lambda _: ReleaseValidationResult(
            issues=(
                ReleaseValidationIssue(
                    code="missing-ci-workflow",
                    message="Missing GitHub Actions workflow.",
                    path=tmp_path / ".github" / "workflows" / "ci.yml",
                ),
            )
        ),
    )

    result = runner.invoke(cli.app, ["validate-release", "--root", str(tmp_path)])

    assert result.exit_code == 1
    assert "Release validation failed" in result.output
    assert "missing-ci-workflow" in result.output


def test_server_check_reports_missing_models(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        assert command == ["curl", "--silent", "--show-error", "http://localhost:11434/api/tags"]
        return subprocess.CompletedProcess(command, 0, stdout='{"models":[{"name":"qwen2.5-coder:3b"}]}', stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["server-check", "--profile", "professional"])

    assert result.exit_code == 1
    assert "qwen2.5-coder:3b" in result.output
    assert "qwen2.5-coder:1.5b-base" in result.output
    assert "ollama pull qwen2.5-coder:1.5b-base" in result.output


def test_server_check_accepts_custom_api_base(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        assert command == ["curl", "--silent", "--show-error", "http://pro-ai-phone:11434/api/tags"]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"models":[{"name":"qwen2.5-coder:3b"},{"name":"qwen2.5-coder:1.5b-base"}]}',
            stderr="",
        )

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["server-check", "--api-base", "http://pro-ai-phone:11434"])

    assert result.exit_code == 0
    assert "Ollama API: http://pro-ai-phone:11434" in result.output


def test_test_prompt_succeeds_with_profile_chat_model(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        assert command == [
            "curl",
            "--silent",
            "--show-error",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "-d",
            '{"model":"qwen2.5-coder:3b","prompt":"Reply with exactly: pro-ai-server-ready","stream":false}',
            "http://localhost:11434/api/generate",
        ]
        return subprocess.CompletedProcess(command, 0, stdout='{"response":"pro-ai-server-ready"}', stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["test-prompt", "--profile", "professional"])

    assert result.exit_code == 0
    assert "Test prompt succeeded" in result.output
    assert "pro-ai-server-ready" in result.output


def test_test_prompt_reports_missing_model(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        return subprocess.CompletedProcess(command, 0, stdout='{"error":"model test-model not found"}', stderr="")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["test-prompt", "--model", "test-model"])

    assert result.exit_code == 1
    assert "could not run model test-model" in result.output
    assert "ollama pull test-model" in result.output


def test_gateway_start_calls_server_with_configurable_models(monkeypatch):
    runner = CliRunner()
    captured = {}

    def fake_serve_gateway(settings):
        captured["settings"] = settings

    monkeypatch.setattr(cli, "serve_gateway", fake_serve_gateway)

    result = runner.invoke(
        cli.app,
        [
            "gateway-start",
            "--host",
            "127.0.0.2",
            "--port",
            "9000",
            "--chat-model",
            "custom-chat:latest",
            "--autocomplete-model",
            "custom-auto:latest",
        ],
    )

    assert result.exit_code == 0
    assert "Starting Pro CodeFlow gateway" in result.output
    assert captured["settings"].host == "127.0.0.2"
    assert captured["settings"].port == 9000
    assert captured["settings"].chat_model == "custom-chat:latest"
    assert captured["settings"].autocomplete_model == "custom-auto:latest"


def test_gateway_status_reports_ready_gateway(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "fetch_gateway_health",
        lambda settings: {
            "service": "pro-codeflow-gateway",
            "status": "ok",
            "version": "0.1.0",
        },
    )

    result = runner.invoke(cli.app, ["gateway-status"])

    assert result.exit_code == 0
    assert "OK Gateway ready" in result.output
    assert "pro-codeflow-gateway" in result.output


def test_gateway_status_reports_unreachable_gateway(monkeypatch):
    runner = CliRunner()

    def fake_fetch_gateway_health(settings):
        raise cli.GatewayStatusError("not reachable")

    monkeypatch.setattr(cli, "fetch_gateway_health", fake_fetch_gateway_health)

    result = runner.invoke(cli.app, ["gateway-status"])

    assert result.exit_code == 1
    assert "Gateway is not ready" in result.output
    assert "not reachable" in result.output


def test_gateway_route_test_prints_selected_route():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["gateway-route-test", "--task", "chat"])

    assert result.exit_code == 0
    assert "Task: chat" in result.output
    assert "Route: chat" in result.output
    assert "Profile: balanced" in result.output
    assert "Model: qwen2.5-coder:3b" in result.output


def test_gateway_route_test_prints_unknown_task_fallback():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["gateway-route-test", "--task", "security-review"])

    assert result.exit_code == 0
    assert "Task: security_review (fallback)" in result.output
    assert "Route: chat" in result.output


def test_gateway_route_test_accepts_custom_model_overrides():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "gateway-route-test",
            "--task",
            "chat",
            "--chat-model",
            "custom-chat:latest",
            "--prompt",
            "hello",
        ],
    )

    assert result.exit_code == 0
    assert "Model: custom-chat:latest" in result.output
    assert "Prompt received: yes" in result.output


def test_gateway_route_test_reads_config_file(tmp_path):
    runner = CliRunner()
    config = tmp_path / "config.yaml"
    config.write_text(
        "routing:\n  routes:\n    security_review:\n      model: custom-review:latest\n",
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["gateway-route-test", "--task", "security-review", "--config", str(config)])

    assert result.exit_code == 0
    assert "Model: custom-review:latest" in result.output


def test_gateway_proxy_test_reports_available_models(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "proxy_ollama_json",
        lambda method, path, settings: OllamaProxyResult(
            status_code=200,
            payload={
                "models": [
                    {"name": "qwen2.5-coder:3b"},
                    {"name": "qwen2.5-coder:1.5b"},
                ]
            },
        ),
    )

    result = runner.invoke(cli.app, ["gateway-proxy-test", "--task", "chat"])

    assert result.exit_code == 0
    assert "OK" in result.output
    assert "Route chat" in result.output


def test_gateway_proxy_test_reports_missing_models(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "proxy_ollama_json",
        lambda method, path, settings: OllamaProxyResult(status_code=200, payload={"models": []}),
    )

    result = runner.invoke(cli.app, ["gateway-proxy-test", "--task", "chat"])

    assert result.exit_code == 1
    assert "Missing models" in result.output
    assert "ollama pull qwen2.5-coder:3b" in result.output


def test_index_search_and_context_commands(tmp_path):
    runner = CliRunner()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("def gateway():\n    return 'context helper'\n", encoding="utf-8")
    db = tmp_path / ".pro-ai-server" / "index.sqlite"

    index_result = runner.invoke(cli.app, ["index", str(tmp_path), "--db", str(db)])
    assert index_result.exit_code == 0
    assert "Indexed files: 1" in index_result.output

    status_result = runner.invoke(cli.app, ["index-status", "--db", str(db)])
    assert status_result.exit_code == 0
    assert "Indexed chunks: 1" in status_result.output

    search_result = runner.invoke(cli.app, ["search", "gateway", "--db", str(db)])
    assert search_result.exit_code == 0
    assert "src/app.py#0" in search_result.output

    context_result = runner.invoke(cli.app, ["context", "gateway", "--db", str(db)])
    assert context_result.exit_code == 0
    assert "# Project Context" in context_result.output
    assert "context helper" in context_result.output


def test_agent_prime_writes_last_prime(tmp_path, monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "build_prime_report",
        lambda index_file_count, index_chunk_count: f"files={index_file_count};chunks={index_chunk_count}",
    )

    result = runner.invoke(cli.app, ["agent", "prime", "--root", str(tmp_path), "--db", str(tmp_path / "missing.sqlite")])

    assert result.exit_code == 0
    output = tmp_path / ".agents" / "memory" / "last-prime.md"
    assert output.read_text(encoding="utf-8") == "files=None;chunks=None"
    assert "Wrote agent prime" in result.output


def test_agent_context_uses_project_memory_and_index(tmp_path):
    runner = CliRunner()
    (tmp_path / ".agents" / "memory").mkdir(parents=True)
    (tmp_path / ".agents" / "memory" / "project-memory.md").write_text("Memory", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("gateway agent context", encoding="utf-8")
    db = tmp_path / ".pro-ai-server" / "index.sqlite"
    runner.invoke(cli.app, ["index", str(tmp_path), "--db", str(db)])

    result = runner.invoke(cli.app, ["agent", "context", "gateway", "--root", str(tmp_path), "--db", str(db)])

    assert result.exit_code == 0
    assert "Memory" in result.output
    assert "src/app.py:1-1 chunk 0" in result.output


def test_agent_plan_writes_plan_from_memory_prime_and_index(tmp_path):
    runner = CliRunner()
    (tmp_path / ".agents" / "memory").mkdir(parents=True)
    (tmp_path / ".agents" / "memory" / "project-memory.md").write_text("Memory", encoding="utf-8")
    (tmp_path / ".agents" / "memory" / "last-prime.md").write_text("Prime", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("gateway plan context", encoding="utf-8")
    db = tmp_path / ".pro-ai-server" / "index.sqlite"
    runner.invoke(cli.app, ["index", str(tmp_path), "--db", str(db)])

    result = runner.invoke(cli.app, ["agent", "plan", "Add Gateway Plan", "--root", str(tmp_path), "--db", str(db)])

    assert result.exit_code == 0
    plan_path = tmp_path / ".agents" / "plans" / "add-gateway-plan.plan.md"
    plan = plan_path.read_text(encoding="utf-8")
    assert "Wrote agent plan" in result.output
    assert "# Plan: Add Gateway Plan" in plan
    assert "Memory" in plan
    assert "Prime" in plan
    assert "gateway plan context" in plan


def test_agent_plan_accepts_explicit_slug(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["agent", "plan", "Add Gateway Plan", "--root", str(tmp_path), "--slug", "gateway-retry"])

    assert result.exit_code == 0
    assert (tmp_path / ".agents" / "plans" / "gateway-retry.plan.md").exists()


def test_agent_report_writes_implementation_report(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        [
            "agent",
            "report",
            "TKT-P8-001",
            "--root",
            str(tmp_path),
            "--summary",
            "Implemented ticket status.",
            "--file-updated",
            "src/pro_ai_server/cli.py",
            "--validation",
            "pytest tests/test_agent_reporter.py",
        ],
    )

    assert result.exit_code == 0
    report_path = tmp_path / ".agents" / "reports" / "TKT-P8-001-report.md"
    report = report_path.read_text(encoding="utf-8")
    assert "Wrote implementation report" in result.output
    assert "Implemented ticket status." in report
    assert "- src/pro_ai_server/cli.py" in report
    assert "- pytest tests/test_agent_reporter.py" in report


def test_agent_status_prints_ticket_summary(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-8"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P8-001-ticket-status.md").write_text("# Ticket Status", encoding="utf-8")

    result = runner.invoke(cli.app, ["agent", "status", "--root", str(tmp_path), "--phase", "phase-8"])

    assert result.exit_code == 0
    assert "Agent Ticket Status" in result.output
    assert "Planned: 1" in result.output
    assert "TKT-P8-001" in result.output


def test_agent_improve_prints_self_improvement_review(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-9"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P9-001-improve.md").write_text("# Improve", encoding="utf-8")

    result = runner.invoke(cli.app, ["agent", "improve", "--root", str(tmp_path), "--phase", "phase-9"])

    assert result.exit_code == 0
    assert "Agent Self-Improvement Review" in result.output
    assert "Planned: 1" in result.output


def test_agent_improve_writes_self_improvement_review(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["agent", "improve", "--root", str(tmp_path), "--write"])

    assert result.exit_code == 0
    output = tmp_path / ".agents" / "reports" / "self-improvement-review.md"
    assert output.exists()
    assert "Wrote self-improvement review" in result.output
    assert "Agent Self-Improvement Review" in output.read_text(encoding="utf-8")


def test_agent_ticketize_previews_accepted_recommendation(tmp_path):
    runner = CliRunner()
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "self-improvement-review.md").write_text(
        "## Recommendations\n\n- Add missing validation evidence.\n- Test optional inputs.\n",
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["agent", "ticketize", "--root", str(tmp_path), "--accept", "validation"])

    assert result.exit_code == 0
    assert "Ticketize Recommendations" in result.output
    assert "TKT-P10-001" in result.output
    assert "Add missing validation evidence" in result.output
    assert not (tmp_path / ".agents" / "build-tickets" / "phase-10").exists()


def test_agent_ticketize_defaults_to_next_available_ticket_number(tmp_path):
    runner = CliRunner()
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "self-improvement-review.md").write_text(
        "## Recommendations\n\n- Add missing validation evidence.\n",
        encoding="utf-8",
    )
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-10"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P10-005-existing.md").write_text("# Existing", encoding="utf-8")

    result = runner.invoke(cli.app, ["agent", "ticketize", "--root", str(tmp_path), "--accept", "validation"])

    assert result.exit_code == 0
    assert "TKT-P10-006" in result.output


def test_agent_ticketize_writes_all_recommendations(tmp_path):
    runner = CliRunner()
    report_dir = tmp_path / ".agents" / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "self-improvement-review.md").write_text(
        "## Recommendations\n\n- Add missing validation evidence.\n- Test optional inputs.\n",
        encoding="utf-8",
    )

    result = runner.invoke(cli.app, ["agent", "ticketize", "--root", str(tmp_path), "--all", "--write"])

    assert result.exit_code == 0
    assert "Wrote 2 ticket draft" in result.output
    assert (tmp_path / ".agents" / "build-tickets" / "phase-10" / "TKT-P10-001-add-missing-validation-evidence.md").exists()
    assert (tmp_path / ".agents" / "build-tickets" / "phase-10" / "TKT-P10-002-test-optional-inputs.md").exists()


def test_agent_ticketize_reports_missing_review(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["agent", "ticketize", "--root", str(tmp_path), "--all"])

    assert result.exit_code == 1
    assert "Self-improvement review not found" in result.output


def test_agent_decide_records_ticket_decision(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-11"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P11-001-example.md").write_text("# Example", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P11-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Recorded accepted decision for TKT-P11-001" in result.output
    assert (tmp_path / ".agents" / "queue" / "ticket-decisions.json").exists()
    assert (tmp_path / ".agents" / "queue" / "ticket-decisions.jsonl").exists()


def test_agent_decide_rejects_invalid_decision(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        ["agent", "decide", "TKT-P11-001", "--decision", "maybe", "--reason", "Nope.", "--root", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert "Decision must be one of" in result.output


def test_agent_queue_prints_decision_summary(tmp_path):
    runner = CliRunner()
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P11-001",
            "--decision",
            "deferred",
            "--reason",
            "Needs review.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "queue", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Agent Ticket Decision Queue" in result.output
    assert "Deferred: 1" in result.output
    assert "TKT-P11-001" in result.output


def test_agent_history_prints_decision_events(tmp_path):
    runner = CliRunner()
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P11-001",
            "--decision",
            "deferred",
            "--reason",
            "Needs review.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "history", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Agent Ticket Decision History" in result.output
    assert "Events: 1" in result.output
    assert "TKT-P11-001" in result.output


def test_agent_handoff_prints_ready_ticket(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-13"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P13-001-handoff.md").write_text("# TKT-P13-001 Handoff", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P13-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "handoff", "--root", str(tmp_path), "--phase", "phase-13"])

    assert result.exit_code == 0
    assert "Agent Implementation Handoff" in result.output
    assert "TKT-P13-001" in result.output
    assert "Ready: 1" in result.output


def test_agent_next_action_prints_selected_ticket(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-14"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P14-001-next-action.md").write_text("# TKT-P14-001 Next Action", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P14-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "next-action", "--root", str(tmp_path), "--phase", "phase-14"])

    assert result.exit_code == 0
    assert "Agent Next Action" in result.output
    assert "Status: ready" in result.output
    assert "TKT-P14-001" in result.output


def test_agent_next_action_resume_policy_prioritizes_active_session(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-16"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P16-001-available.md").write_text("# TKT-P16-001 Available", encoding="utf-8")
    (ticket_dir / "TKT-P16-002-started.md").write_text("# TKT-P16-002 Started", encoding="utf-8")
    for ticket_id in ("TKT-P16-001", "TKT-P16-002"):
        runner.invoke(
            cli.app,
            [
                "agent",
                "decide",
                ticket_id,
                "--decision",
                "accepted",
                "--reason",
                "Ready.",
                "--root",
                str(tmp_path),
            ],
        )
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P16-002",
            "--event",
            "started",
            "--note",
            "Resume.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(
        cli.app,
        ["agent", "next-action", "--root", str(tmp_path), "--phase", "phase-16", "--session-policy", "resume"],
    )

    assert result.exit_code == 0
    assert "TKT-P16-002" in result.output
    assert "Session: started" in result.output


def test_agent_packet_prints_execution_packet(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-14"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P14-001-packet.md").write_text(
        "# TKT-P14-001 Packet\n\n## Objective\n\nBuild it.",
        encoding="utf-8",
    )
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P14-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "packet", "--root", str(tmp_path), "--phase", "phase-14"])

    assert result.exit_code == 0
    assert "Agent Execution Packet" in result.output
    assert "TKT-P14-001" in result.output
    assert "Build it." in result.output
    assert "Validation Commands" in result.output


def test_agent_packet_skips_finished_session_by_default(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-16"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P16-001-finished.md").write_text("# TKT-P16-001 Finished", encoding="utf-8")
    (ticket_dir / "TKT-P16-002-available.md").write_text("# TKT-P16-002 Available", encoding="utf-8")
    for ticket_id in ("TKT-P16-001", "TKT-P16-002"):
        runner.invoke(
            cli.app,
            [
                "agent",
                "decide",
                ticket_id,
                "--decision",
                "accepted",
                "--reason",
                "Ready.",
                "--root",
                str(tmp_path),
            ],
        )
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P16-001",
            "--event",
            "finished",
            "--note",
            "Waiting report.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "packet", "--root", str(tmp_path), "--phase", "phase-16"])

    assert result.exit_code == 0
    assert "TKT-P16-002" in result.output
    assert "TKT-P16-001" not in result.output


def test_agent_packet_writes_default_output(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-14"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P14-001-packet.md").write_text("# TKT-P14-001 Packet", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P14-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "packet", "--root", str(tmp_path), "--phase", "phase-14", "--write"])

    output = tmp_path / ".agents" / "execution" / "TKT-P14-001.execution.md"
    assert result.exit_code == 0
    assert "Wrote execution packet" in result.output
    assert output.exists()
    assert "Agent Execution Packet" in output.read_text(encoding="utf-8")


def test_agent_session_records_work_session_event(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-15"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P15-001-session.md").write_text("# TKT-P15-001 Session", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P15-001",
            "--event",
            "pickup",
            "--note",
            "Taking it.",
            "--root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "Recorded picked-up session event for TKT-P15-001" in result.output
    assert (tmp_path / ".agents" / "execution" / "work-sessions.json").exists()


def test_agent_sessions_prints_current_work_sessions(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-15"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P15-001-session.md").write_text("# TKT-P15-001 Session", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P15-001",
            "--event",
            "started",
            "--note",
            "Working.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "sessions", "--root", str(tmp_path), "--phase", "phase-15"])

    assert result.exit_code == 0
    assert "Agent Work Sessions" in result.output
    assert "Started: 1" in result.output
    assert "TKT-P15-001" in result.output


def test_agent_session_history_prints_events(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-15"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P15-001-session.md").write_text("# TKT-P15-001 Session", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P15-001",
            "--event",
            "finished",
            "--note",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "session-history", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert "Agent Work Session History" in result.output
    assert "Events: 1" in result.output
    assert "TKT-P15-001" in result.output


def test_agent_reconcile_prints_session_report_warnings(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-17"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P17-001-reconcile.md").write_text("# TKT-P17-001 Reconcile", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P17-001",
            "--event",
            "finished",
            "--note",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "reconcile", "--root", str(tmp_path), "--phase", "phase-17"])

    assert result.exit_code == 0
    assert "Agent Session Report Reconciliation" in result.output
    assert "Warnings: 1" in result.output
    assert "finished-session-unreported" in result.output


def test_agent_reconcile_can_fail_on_warning(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-17"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P17-001-reconcile.md").write_text("# TKT-P17-001 Reconcile", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P17-001",
            "--event",
            "finished",
            "--note",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(
        cli.app,
        ["agent", "reconcile", "--root", str(tmp_path), "--phase", "phase-17", "--fail-on-warning"],
    )

    assert result.exit_code == 1
    assert "finished-session-unreported" in result.output


def test_agent_session_archive_previews_candidates(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-19"
    ticket_dir.mkdir(parents=True)
    ticket_path = ticket_dir / "TKT-P19-001-archive.md"
    ticket_path.write_text("# TKT-P19-001 Archive", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P19-001",
            "--event",
            "finished",
            "--note",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )
    runner.invoke(
        cli.app,
        [
            "agent",
            "report",
            "TKT-P19-001",
            "--summary",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "session-archive", "--root", str(tmp_path), "--phase", "phase-19"])

    assert result.exit_code == 0
    assert "Agent Session Archive" in result.output
    assert "Mode: preview" in result.output
    assert "Archive candidates: 1" in result.output
    assert "TKT-P19-001" in result.output


def test_agent_session_archive_write_removes_current_session(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-19"
    ticket_dir.mkdir(parents=True)
    ticket_path = ticket_dir / "TKT-P19-001-archive.md"
    ticket_path.write_text("# TKT-P19-001 Archive", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P19-001",
            "--event",
            "finished",
            "--note",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )
    runner.invoke(
        cli.app,
        [
            "agent",
            "report",
            "TKT-P19-001",
            "--summary",
            "Done.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "session-archive", "--root", str(tmp_path), "--phase", "phase-19", "--write"])
    sessions = runner.invoke(cli.app, ["agent", "sessions", "--root", str(tmp_path), "--phase", "phase-19"])

    assert result.exit_code == 0
    assert "Mode: write" in result.output
    assert "Archive candidates: 1" in result.output
    assert "TKT-P19-001" in (tmp_path / ".agents" / "execution" / "archived-work-sessions.jsonl").read_text(encoding="utf-8")
    assert "| none | none | none | none | none |" in sessions.output


def test_agent_autopilot_previews_next_ticket(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-18"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P18-001-autopilot.md").write_text("# TKT-P18-001 Autopilot", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P18-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "autopilot", "--root", str(tmp_path), "--phase", "phase-18"])

    assert result.exit_code == 0
    assert "Agent Autopilot" in result.output
    assert "Mode: preview" in result.output
    assert "TKT-P18-001" in result.output
    assert not (tmp_path / ".agents" / "execution" / "TKT-P18-001.execution.md").exists()


def test_agent_autopilot_execute_writes_packet_and_starts_session(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-18"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P18-001-autopilot.md").write_text("# TKT-P18-001 Autopilot", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P18-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(
        cli.app,
        ["agent", "autopilot", "--root", str(tmp_path), "--phase", "phase-18", "--execute", "--start-session"],
    )

    assert result.exit_code == 0
    assert "Mode: execute" in result.output
    assert "Session events: picked-up, started" in result.output
    assert (tmp_path / ".agents" / "execution" / "TKT-P18-001.execution.md").exists()


def test_agent_autopilot_stops_on_reconciliation_warning(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-18"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P18-001-autopilot.md").write_text("# TKT-P18-001 Autopilot", encoding="utf-8")
    runner.invoke(
        cli.app,
        [
            "agent",
            "decide",
            "TKT-P18-001",
            "--decision",
            "accepted",
            "--reason",
            "Ready.",
            "--root",
            str(tmp_path),
        ],
    )
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P18-001",
            "--event",
            "finished",
            "--note",
            "Needs report.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "autopilot", "--root", str(tmp_path), "--phase", "phase-18"])

    assert result.exit_code == 0
    assert "Reconciliation warnings must be resolved" in result.output
    assert "Reconciliation warnings: 1" in result.output


def test_agent_autopilot_stops_on_active_session_by_default(tmp_path):
    runner = CliRunner()
    ticket_dir = tmp_path / ".agents" / "build-tickets" / "phase-18"
    ticket_dir.mkdir(parents=True)
    (ticket_dir / "TKT-P18-001-autopilot.md").write_text("# TKT-P18-001 Autopilot", encoding="utf-8")
    (ticket_dir / "TKT-P18-002-next.md").write_text("# TKT-P18-002 Next", encoding="utf-8")
    for ticket_id in ("TKT-P18-001", "TKT-P18-002"):
        runner.invoke(
            cli.app,
            [
                "agent",
                "decide",
                ticket_id,
                "--decision",
                "accepted",
                "--reason",
                "Ready.",
                "--root",
                str(tmp_path),
            ],
        )
    runner.invoke(
        cli.app,
        [
            "agent",
            "session",
            "TKT-P18-001",
            "--event",
            "started",
            "--note",
            "Working.",
            "--root",
            str(tmp_path),
        ],
    )

    result = runner.invoke(cli.app, ["agent", "autopilot", "--root", str(tmp_path), "--phase", "phase-18"])

    assert result.exit_code == 0
    assert "Active work session" in result.output
    assert "Ticket: -" in result.output


def test_doctor_reports_missing_continue_extension(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: None)
    monkeypatch.setattr(cli.shutil, "which", lambda command: "C:/bin/python.exe" if command == "python" else None)
    monkeypatch.setattr(cli, "detect_ide_clis", lambda: (IdeCli(command="cursor", path="C:/bin/cursor.cmd"),))
    monkeypatch.setattr(
        cli,
        "detect_continue_extension_status",
        lambda ide: IdeExtensionStatus(
            ide=ide,
            extension_id="Continue.continue",
            installed=False,
        ),
    )

    result = runner.invoke(cli.app, ["doctor"])

    assert result.exit_code == 0
    assert "IDE CLI found: cursor" in result.output
    assert "Continue extension not installed" in result.output
    assert "install-continue-extension --ide cursor" in result.output
    assert "DevStack launch IDEs: VS Code and Cursor" in result.output


def test_devstack_ide_status_prints_launch_matrix(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "launch_ide_readiness_matrix",
        lambda: (
            IdeReadiness(
                ide=IdeCli(command="code", path="C:/bin/code.cmd"),
                launch_supported=True,
                follow_up=False,
                continue_installed=True,
                state="ready",
                next_action="Run configure-continue.",
            ),
        ),
    )

    result = runner.invoke(cli.app, ["devstack-ide-status"])

    assert result.exit_code == 0
    assert "DevStack IDE readiness" in result.output
    assert "code: ready (launch, CLI installed)" in result.output
    assert "Run configure-continue" in result.output


def test_install_continue_extension_command_installs_selected_ide(monkeypatch):
    runner = CliRunner()
    ide = IdeCli(command="cursor", path="C:/bin/cursor.cmd")

    monkeypatch.setattr(cli, "installed_ide_clis", lambda: (ide,))
    monkeypatch.setattr(
        cli,
        "detect_continue_extension_status",
        lambda current_ide: IdeExtensionStatus(
            ide=current_ide,
            extension_id="Continue.continue",
            installed=False,
        ),
    )
    monkeypatch.setattr(
        cli,
        "install_continue_extension",
        lambda current_ide: IdeExtensionStatus(
            ide=current_ide,
            extension_id="Continue.continue",
            installed=True,
        ),
    )

    result = runner.invoke(cli.app, ["install-continue-extension", "--ide", "cursor"])

    assert result.exit_code == 0
    assert "Installing Continue extension in cursor" in result.output
    assert "Installed" in result.output


def test_configure_continue_warns_when_no_continue_ready_ide_is_detected(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "write_continue_config",
        lambda plan, mode, host: ContinueConfigWriteResult(
            config_path=tmp_path / ".continue" / "config.yaml",
            backup_path=None,
            api_base="http://localhost:11434",
        ),
    )
    monkeypatch.setattr(cli, "installed_ide_clis", lambda: (IdeCli(command="cursor", path="C:/bin/cursor.cmd"),))
    monkeypatch.setattr(
        cli,
        "detect_continue_extension_status",
        lambda ide: IdeExtensionStatus(ide=ide, extension_id="Continue.continue", installed=False),
    )

    result = runner.invoke(cli.app, ["configure-continue", "--mode", "usb"])

    assert result.exit_code == 0
    assert "No supported IDE with the Continue extension was detected" in result.output


def test_status_prints_concise_readiness_report(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "run_optional_command", lambda command: "output")
    monkeypatch.setattr(cli, "assess_ollama_server_status", lambda output: OllamaServerStatus(ok=True))
    monkeypatch.setattr(cli, "detect_ide_clis", lambda: ())
    monkeypatch.setattr(
        cli,
        "build_status_report",
        lambda devices, reverse, ollama, ides, adb_path, api_base="http://localhost:11434": ProAiStatus(
            items=(
                StatusItem("Phone", True, "connected (ABC123)"),
                StatusItem("Ollama", True, "responding on /api/tags (0 models)"),
            )
        ),
    )

    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0
    assert "Pro AI Server Status" in result.output
    assert "OK Phone: connected (ABC123)" in result.output
    assert "OK Ollama: responding on /api/tags" in result.output


def test_setup_tailscale_reports_already_installed_on_host_and_phone(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        outputs = {
            ("adb", "devices"): "List of devices attached\nABC123\tdevice\n",
            ("tailscale", "version"): "1.96.4",
            ("adb", "-s", "ABC123", "shell", "pm", "path", "com.tailscale.ipn"): (
                "package:/data/app/com.tailscale.ipn/base.apk"
            ),
        }
        return subprocess.CompletedProcess(command, 0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["setup-tailscale"])

    assert result.exit_code == 0
    assert "Tailscale is available on this Windows host" in result.output
    assert "Tailscale is installed on Android device ABC123" in result.output


def test_setup_tailscale_installs_android_apk_with_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    apk = tmp_path / "tailscale.apk"
    apk.write_text("apk", encoding="utf-8")
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["tailscale", "version"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "com.tailscale.ipn"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["setup-tailscale", "--android-apk", str(apk), "--yes"])

    assert result.exit_code == 0
    assert ["adb", "-s", "ABC123", "install", "-r", str(apk)] in commands
    assert "Installed" in result.output


def test_setup_tailscale_refuses_android_apk_install_without_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    apk = tmp_path / "tailscale.apk"
    apk.write_text("apk", encoding="utf-8")

    def fake_run(command, capture_output, text):
        import subprocess

        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["tailscale", "version"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["setup-tailscale", "--android-apk", str(apk)])

    assert result.exit_code == 1
    assert "without --yes" in result.output


def test_setup_tailscale_opens_play_store_when_phone_app_is_missing(monkeypatch):
    runner = CliRunner()
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["tailscale", "version"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not found")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "com.tailscale.ipn"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["setup-tailscale"])

    assert result.exit_code == 0
    assert [
        "adb",
        "-s",
        "ABC123",
        "shell",
        "am",
        "start",
        "-a",
        "android.intent.action.VIEW",
        "-d",
        "market://details?id=com.tailscale.ipn",
    ] in commands
    assert "Opened" in result.output
