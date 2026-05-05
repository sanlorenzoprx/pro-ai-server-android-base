from pathlib import Path

from pro_ai_server.continue_config import ContinueConfigWriteResult
from pro_ai_server.models import model_plan_for_profile
from pro_ai_server.ollama import ModelInventoryStatus, OllamaServerStatus, OllamaTestPromptStatus
from pro_ai_server.script_delivery import build_script_delivery_plan
from pro_ai_server.setup_receipt import SetupErrorState, SetupReceipt, build_setup_receipt, render_setup_receipt
from pro_ai_server.setup_workflow import mark_production_step_failed, plan_production_installer, plan_setup_workflow
from pro_ai_server.termux_scripts import generate_termux_scripts


def test_builds_minimal_plan_only_receipt():
    plan = plan_setup_workflow(configure_continue=False, create_usb_tunnel=False)

    receipt = build_setup_receipt(workflow_plan=plan)

    assert receipt.mode == "usb"
    assert receipt.model_profile == "professional"
    assert receipt.generated_termux_paths == ()
    assert receipt.continue_config_path is None
    assert receipt.pushed_scripts is False
    assert receipt.tunnel_requested is False
    assert receipt.artifacts == ()


def test_receipt_captures_continue_config_backup():
    plan = plan_setup_workflow()
    result = ContinueConfigWriteResult(
        config_path=Path("home") / ".continue" / "config.yaml",
        backup_path=Path("home") / ".continue" / "config.yaml.pro-ai-server-backup-20260502-131415",
        api_base="http://localhost:11434",
    )

    receipt = build_setup_receipt(workflow_plan=plan, continue_result=result)

    assert receipt.continue_config_path == result.config_path
    assert receipt.continue_backup_path == result.backup_path
    assert ("Continue config", str(result.config_path)) in tuple((item.label, item.value) for item in receipt.artifacts)
    assert ("Continue config backup", str(result.backup_path)) in tuple(
        (item.label, item.value) for item in receipt.artifacts
    )


def test_receipt_captures_script_push_and_tunnel():
    model_plan = model_plan_for_profile("professional")
    bundle = generate_termux_scripts(
        model_plan.chat_model,
        model_plan.autocomplete_model,
        script_dir=Path("out") / "termux",
    )
    delivery_plan = build_script_delivery_plan(local_generated_termux_dir=Path("out") / "termux", serial="device-123")
    written_paths = (Path("out") / "termux" / "start-pro-ai-server.sh", Path("out") / "termux" / "bootstrap.sh")

    receipt = build_setup_receipt(
        termux_bundle=bundle,
        written_termux_paths=written_paths,
        delivery_plan=delivery_plan,
        model_plan=model_plan,
        tunnel_requested=True,
    )

    assert receipt.generated_termux_paths == tuple(sorted(written_paths, key=lambda path: path.as_posix()))
    assert receipt.selected_device_serial == "device-123"
    assert receipt.pushed_scripts is True
    assert receipt.tunnel_requested is True
    assert receipt.post_push_termux_commands == (
        "~/bootstrap-phone-stack.sh",
        "~/bootstrap.sh",
        "~/install-models.sh",
        "~/start-pro-ai-server.sh",
    )
    assert any(item.label == "Run in Termux" for item in receipt.next_steps)
    assert any("Termux:Widget" in note for note in receipt.notes)


def test_render_setup_receipt_is_deterministic_text():
    receipt = SetupReceipt(
        mode="usb",
        model_profile="professional",
        generated_termux_paths=(Path("generated") / "termux" / "bootstrap.sh",),
        continue_config_path=Path("home") / ".continue" / "config.yaml",
        selected_device_serial="device-123",
        pushed_scripts=True,
        tunnel_requested=True,
        post_push_termux_commands=("~/bootstrap.sh",),
        warnings=("check battery settings",),
        notes=("scripts were generated for inspection",),
    )
    receipt = build_setup_receipt(
        mode=receipt.mode,
        model_plan=model_plan_for_profile(receipt.model_profile),
        written_termux_paths=receipt.generated_termux_paths,
        selected_device_serial=receipt.selected_device_serial,
        pushed_scripts=receipt.pushed_scripts,
        tunnel_requested=receipt.tunnel_requested,
        warnings=receipt.warnings,
        notes=receipt.notes,
    )

    rendered = render_setup_receipt(receipt)

    assert rendered == (
        "Pro AI Server setup receipt\n"
        "\n"
        "Summary\n"
        "- Mode: usb\n"
        "- Model profile: professional\n"
        "- Device model: not recorded\n"
        "- Selected device serial: device-123\n"
        "- Pushed scripts: yes\n"
        "- Tunnel requested: yes\n"
        "\n"
        "Artifacts\n"
        f"- Generated Termux files: {Path('generated') / 'termux' / 'bootstrap.sh'}\n"
        "\n"
        "Post-push Termux commands\n"
        "- none\n"
        "\n"
        "Next steps\n"
        "- USB tunnel: Keep adb reverse tcp:11434 active while using Continue.\n"
        "- Termux scripts: Run the delivered scripts from Termux.\n"
        "\n"
        "Warnings\n"
        "- check battery settings\n"
        "\n"
        "Notes\n"
        "- scripts were generated for inspection\n"
    )
    assert render_setup_receipt(receipt) == rendered


def test_render_setup_receipt_handles_absent_optional_fields():
    rendered = render_setup_receipt(SetupReceipt())

    assert "- Mode: not recorded" in rendered
    assert "- Model profile: not recorded" in rendered
    assert "- Device model: not recorded" in rendered
    assert "- Selected device serial: not recorded" in rendered
    assert "Artifacts\n- none\n" in rendered
    assert "Warnings\n- none\n" in rendered


def test_receipt_can_include_production_installer_steps():
    production_plan = mark_production_step_failed(
        plan_production_installer(),
        "adb-verification",
        message="ADB shell command failed.",
        debug_detail="adb shell getprop returned exit code 1",
    )

    receipt = build_setup_receipt(workflow_plan=production_plan.setup_plan, production_plan=production_plan)
    rendered = render_setup_receipt(receipt)

    assert receipt.installer_steps == production_plan.steps
    assert "Production installer steps\n" in rendered
    assert "- host-checks: pending - Host checks\n" in rendered
    assert "- adb-verification: failure - ADB verification\n" in rendered
    assert "Recovery: Reconnect the phone" in rendered
    assert "Debug: adb shell getprop returned exit code 1" in rendered


def test_receipt_can_include_test_prompt_result():
    receipt = build_setup_receipt(
        workflow_plan=plan_setup_workflow(),
        test_prompt_status=OllamaTestPromptStatus(
            ok=True,
            model="qwen2.5-coder:3b",
            response="pro-ai-server-ready",
        ),
    )

    rendered = render_setup_receipt(receipt)

    assert receipt.test_prompt_ok is True
    assert receipt.test_prompt_response == "pro-ai-server-ready"
    assert "Test prompt\n- Result: pass\n- Response: pro-ai-server-ready\n" in rendered


def test_receipt_includes_production_success_context():
    receipt = build_setup_receipt(
        workflow_plan=plan_setup_workflow(),
        selected_device_serial="ABC123",
        device_model="Pixel 6",
        ollama_status=OllamaServerStatus(ok=True, model_names=("qwen2.5-coder:3b",)),
        test_prompt_status=OllamaTestPromptStatus(
            ok=True,
            model="qwen2.5-coder:3b",
            response="pro-ai-server-ready",
        ),
    )

    rendered = render_setup_receipt(receipt)

    assert "- Device model: Pixel 6" in rendered
    assert "- Selected device serial: ABC123" in rendered
    assert "Ollama server\n- Result: pass\n- Models: qwen2.5-coder:3b\n" in rendered
    assert "Test prompt\n- Result: pass\n- Response: pro-ai-server-ready\n" in rendered


def test_receipt_includes_partial_failure_context_and_error_state():
    receipt = build_setup_receipt(
        workflow_plan=plan_setup_workflow(),
        model_inventory_status=ModelInventoryStatus(
            ok=False,
            model_names=("qwen2.5-coder:3b",),
            missing_models=("qwen2.5-coder:1.5b-base",),
        ),
        test_prompt_status=OllamaTestPromptStatus(
            ok=False,
            model="qwen2.5-coder:3b",
            warnings=("Ollama did not return a test-prompt response.",),
        ),
        errors=(
            SetupErrorState(
                problem="Test prompt failed.",
                likely_cause="Ollama server is not running.",
                recovery_action="Run ~/start-pro-ai-server.sh in Termux.",
                debug_detail="curl returned connection refused",
            ),
        ),
    )

    rendered = render_setup_receipt(receipt)

    assert "Ollama server\n- Result: fail\n- Models: qwen2.5-coder:3b\n" in rendered
    assert "- Missing models: qwen2.5-coder:1.5b-base" in rendered
    assert "- Warning: Ollama did not return a test-prompt response." in rendered
    assert "Errors\n- Error 1: Test prompt failed." in rendered
    assert "Likely cause: Ollama server is not running." in rendered
    assert "Recovery: Run ~/start-pro-ai-server.sh in Termux." in rendered
    assert "Debug: curl returned connection refused" in rendered
