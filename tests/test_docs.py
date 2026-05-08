from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_doc(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").lower()


def test_readme_documents_current_mvp_cli_commands_and_bundled_adb_policy():
    readme = read_doc("README.md")

    for command in (
        "doctor",
        "validate-platform-tools",
        "scan --serial",
        "generate-scripts",
        "push-scripts",
        "configure-continue --mode usb",
        "tunnel",
        "setup --execute --yes",
        "setup-tailscale",
        "status",
        "diagnose --output",
    ):
        assert command in readme

    assert "bundled adb" in readme
    assert "fastboot is not used" in readme
    assert "back up existing continue configuration" in readme
    assert "cursor integration is supported through the continue extension" in readme
    assert "%userprofile%\\.continue\\config.yaml" in readme
    assert "lan exposes ollama" in readme
    assert "tailscale" in readme and "--host" in readme
    assert "--install-host --yes" in readme
    assert "--android-apk <path> --yes" in readme


def test_cli_workflow_documents_windows_first_flow_and_safety_claims():
    workflow = read_doc("docs/CLI_WORKFLOW.md")

    for command in (
        "pro-ai-server doctor",
        "pro-ai-server validate-platform-tools",
        "pro-ai-server validate-release",
        "pro-ai-server scan --serial",
        "pro-ai-server android-compatibility",
        "pro-ai-server android-validation-matrix",
        "pro-ai-server apk-manifest --android-version 13",
        "pro-ai-server termux-check",
        "pro-ai-server install-termux-apps",
        "pro-ai-server generate-scripts",
        "pro-ai-server push-scripts",
        "pro-ai-server configure-continue --mode usb",
        "pro-ai-server setup-tailscale",
        "pro-ai-server status",
        "pro-ai-server native-runtime-config --profile professional --prefer chat",
        "pro-ai-server native-runtime-assets --profile professional",
        "pro-ai-server native-runtime-doctor --profile professional",
        "pro-ai-server native-runtime-android-plan",
        "pro-ai-server native-runtime-android-install",
        "pro-ai-server native-runtime-android-start",
        "pro-ai-server native-runtime-android-status",
        "pro-ai-server native-runtime-android-smoke",
        "pro-ai-server native-runtime-android-smoke-path",
        "pro-ai-server native-runtime-android-stop",
        "pro-ai-server tunnel",
        "pro-ai-server setup",
        "pro-ai-server setup --production",
        "pro-ai-server installer-ui",
        "pro-ai-server setup --execute --yes",
        "pro-ai-server diagnose --output",
        "pro-ai-server server-endpoints",
        "pro-ai-server test-prompt",
        "scripts/smoke-production-installer.ps1",
    ):
        assert command in workflow

    for safety_claim in (
        "bundled adb",
        "fastboot is not used",
        "does not require `fastboot.exe`",
        "no fastboot",
        "includes cursor",
        "no separate cursor-specific config file is required",
        "backs it up first",
        "termux:widget still requires manual installation",
        "lan mode exposes ollama",
        "tailscale mode should use a private tailscale hostname",
        "lan and tailscale require an explicit host",
        "com.tailscale.ipn",
        "winget",
        "--android-apk",
        "--fdroid-apk",
        "--fdroid-url",
        "--fdroid-sha256",
        "--termux-apk",
        "--termux-api-apk",
        "--termux-url",
        "--termux-sha256",
        "--use-pinned-apk-manifest",
        "bootstrap-phone-stack.sh",
        ".termux/termux.properties",
        "install unknown apps",
        "docs/android_compatibility.md",
        "concise readiness view",
        "native `llama.cpp` lane",
        "phone mutation requires `--execute --yes`",
        "/data/local/tmp/pro-ai-server/native-runtime",
        "not the final companion apk experience",
        "127.0.0.1:11434",
        "adb forward tcp:11434 tcp:11434",
        "tiny non-streaming `/api/generate`",
        "guarded one-shot path",
        "advanced lan and tailscale modes are not shown in first-run ui",
        "missing model, invalid json, empty output, or connection failures",
        "-withphone",
    ):
        assert safety_claim in workflow


def test_troubleshooting_documents_phone_setup_and_mvp_failure_modes():
    troubleshooting = read_doc("docs/TROUBLESHOOTING.md")

    for expected in (
        "no device found",
        "unauthorized",
        "multiple devices require --serial",
        "pro-ai-server termux-check",
        "pro-ai-server install-termux-apps",
        "termux is missing",
        "termux:api is missing",
        "install unknown apps",
        "--fdroid-apk",
        "--fdroid-url",
        "--fdroid-sha256",
        "checksum verification",
        "termux home is not initialized",
        "ollama not responding on localhost:11434",
        "missing models",
        "test prompt failed",
        "usb tunnel failure",
        "pro-ai-server test-prompt",
        "scripts/smoke-production-installer.ps1",
        "continue backup",
        "lan mode exposes ollama",
        "tailscale hostname",
        "100.x.x.x",
        "bundled adb",
        "android studio",
        "pro-ai-server validate-platform-tools",
        "pro-ai-server validate-release",
        "no fastboot",
        "--serial",
        "termux:widget manual placement",
        "bootstrap-phone-stack.sh",
        "pro-ai-server-bootstrap.log",
        "--use-pinned-apk-manifest",
    ):
        assert expected in troubleshooting


def test_release_doc_documents_windows_first_release_gates_and_smoke_flow():
    release = read_doc("docs/RELEASE.md")

    for expected in (
        "pro-ai-server validate-release",
        "pro-ai-server validate-platform-tools",
        "pytest",
        "ruff check .",
        "pro-ai-server doctor",
        "bundled adb",
        "fastboot is not used",
        "fastboot.exe",
        "scripts/download-platform-tools.ps1",
        "android studio",
        "pro-ai-server generate-scripts",
        "pro-ai-server setup --production",
        "pro-ai-server installer-ui",
        "scripts/smoke-production-installer.ps1",
        "-withphone",
        "pro-ai-server diagnose --output",
        "test prompt",
    ):
        assert expected in release


def test_devstack_demo_documents_launch_script_and_smoke_path():
    demo = read_doc("docs/DEVSTACK_DEMO.md")
    workflows = read_doc("docs/AGENT_WORKFLOWS.md")

    for expected in (
        "android phone connected by usb",
        "pro-ai-server status",
        "pro-ai-server tunnel",
        "pro-ai-server test-prompt",
        "pro-ai-server devstack-ide-status",
        "pro-ai-server configure-devstack",
        "http://localhost:11434",
        "vs code or cursor",
        "continue extension",
        "coding assistance",
        "no monthly ai model bill",
        "performance depends on the phone hardware",
        "low-ram",
        "first-token latency",
    ):
        assert expected in demo

    assert "docs/devstack_demo.md" in workflows
    assert "usb-connected android phone" in workflows
    assert "no monthly ai model bill" in workflows


def test_devstack_offer_documents_launch_packages_and_boundaries():
    offer = read_doc("docs/DEVSTACK_OFFER.md")

    for expected in (
        "private ai coding assistant",
        "cursor or vs code",
        "continue",
        "local-first",
        "usb-first",
        "no monthly ai model bill",
        "low-ram",
        "trial entry",
        "free trial or `$1`",
        "starter install",
        "`$49-$99`",
        "pro install",
        "`$149-$199`",
        "target customer",
        "includes:",
        "exclusions:",
        "refund",
        "support boundary",
        "no guarantee",
        "cloud-model speed",
    ):
        assert expected in offer


def test_devstack_capture_checklist_documents_video_and_sales_beats():
    demo = read_doc("docs/DEVSTACK_DEMO.md")
    offer = read_doc("docs/DEVSTACK_OFFER.md")

    for expected in (
        "capture checklist",
        "screen recording",
        "phone shot",
        "ide shot",
        "status check",
        "chat moment",
        "autocomplete or code assistance",
        "short-form video beats",
        "sales-call demo beats",
        "cta",
        "trial entry, starter install, or pro install",
        "if this response takes a moment",
        "cut from the prompt to the completed response",
        "local-first over usb",
    ):
        assert expected in demo

    for expected in (
        "proof asset alignment",
        "phone shot",
        "status shot",
        "ide shot",
        "chat proof",
        "code assistance proof",
        "trial entry, starter install, or pro install",
        "hardware qualifier",
    ):
        assert expected in offer


def test_devstack_tracking_plan_documents_params_events_and_examples():
    tracking = read_doc("docs/DEVSTACK_TRACKING.md")
    offer = read_doc("docs/DEVSTACK_OFFER.md")

    for expected in (
        "`ref`",
        "`partner_type`",
        "`offer`",
        "`msg`",
        "`channel`",
        "`niche`",
        "`campaign`",
        "trial_entry",
        "starter_install",
        "pro_install",
        "private_coding_assistant",
        "no_monthly_model_bill",
        "usb_first_local",
        "cursor_vscode_continue",
        "landing_page_viewed",
        "cta_clicked",
        "lead_captured",
        "trial_started",
        "install_started",
        "install_completed",
        "demo_requested",
        "purchase_completed",
        "required properties",
        "example links",
        "measure before scaling",
        "refund or failed-install rate",
    ):
        assert expected in tracking

    for expected in (
        "docs/devstack_tracking.md",
        "trial_entry",
        "starter_install",
        "pro_install",
        "private_coding_assistant",
        "no_monthly_model_bill",
        "usb_first_local",
        "cursor_vscode_continue",
    ):
        assert expected in offer


def test_production_rc_doc_documents_hardware_packaged_exe_and_go_no_go():
    rc = read_doc("docs/PRODUCTION_RC.md")

    for expected in (
        "phase 22",
        "production release candidate",
        "windows first",
        "usb-first android phone",
        "http://localhost:11434",
        "vs code or cursor",
        "continue",
        "scripts/build-windows-exe.ps1",
        "dist\\pro-ai-server\\pro-ai-server.exe validate-release",
        "scripts/smoke-production-installer.ps1 -withphone",
        "pro-ai-server android-compatibility",
        "pro-ai-server setup --execute --yes",
        "bootstrap-phone-stack.sh",
        "--use-pinned-apk-manifest",
        "pro-ai-server install-termux-apps",
        "pro-ai-server tunnel",
        "pro-ai-server test-prompt",
        "pro-ai-server server-check",
        "pro-ai-server devstack-ide-status",
        "pro-ai-server configure-devstack",
        "hardware smoke matrix",
        "packaged exe evidence",
        "live ide evidence",
        "release evidence bundle",
        "go-with-limitations",
        "no-go",
    ):
        assert expected in rc


def test_production_rc_doc_documents_hardware_smoke_matrix_fields():
    rc = read_doc("docs/PRODUCTION_RC.md")

    for expected in (
        "completed",
        "blocked",
        "skipped",
        "device identity record",
        "phone model",
        "android version",
        "detected serial",
        "usb debugging authorization",
        "ram profile",
        "compatibility tier",
        "selected chat model",
        "selected autocomplete model",
        "run checklist",
        "adb detection",
        "termux readiness",
        "script push",
        "usb tunnel",
        "server status",
        "model inventory",
        "test prompt",
        "evidence log",
        "terminal smoke output",
        "diagnostics file",
        "recovery log",
        "blocks rc",
        "hardware smoke attempts",
        "initial android detection attempt",
        "remote desktop",
        "usb device redirection",
        "oem android usb driver",
        "moto g 5g hardware smoke attempt",
        "termux and termux:api",
        "install-termux-apps",
        "install unknown apps",
        "--fdroid-apk",
        "--fdroid-url",
        "--fdroid-sha256",
        "ollama endpoint",
    ):
        assert expected in rc


def test_android_compatibility_doc_documents_tiers_manifest_and_trust_lanes():
    compatibility = read_doc("docs/ANDROID_COMPATIBILITY.md")

    for expected in (
        "compatibility tiers",
        "green",
        "yellow",
        "red",
        "android 12",
        "arm64-v8a",
        "professional",
        "lightweight",
        "trust lane rules",
        "play store termux",
        "f-droid",
        "termux:api",
        "apk manifest template",
        "pinned apk manifest",
        "android validation lanes",
        "android-12-13-yellow",
        "android-12-13-green",
        "android-14-15-plus-yellow",
        "android-14-15-plus-green",
        "package_name",
        "min_android",
        "max_android",
        "sha256",
        "0.118.3",
        "0.53.0",
        "--use-pinned-apk-manifest",
        "checksum mismatch",
        "docs/production_rc.md",
    ):
        assert expected in compatibility


def test_production_smoke_script_documents_no_phone_and_phone_paths():
    smoke = read_doc("scripts/smoke-production-installer.ps1")

    for expected in (
        "param(",
        "$withphone",
        "ruff check",
        "pytest",
        "validate-release",
        "setup --production",
        "installer-ui",
        "--mock-failure",
        "diagnose --output diagnostics.txt",
        "termux-check",
        "push-scripts",
        "tunnel",
        "server-check",
        "test-prompt",
        "status",
    ):
        assert expected in smoke


def test_ci_runs_release_validation_and_core_build_gates():
    ci = read_doc(".github/workflows/ci.yml")

    for expected in (
        "python -m pip install -e \".[dev]\"",
        "ruff check .",
        "pytest",
        "pro-ai-server validate-release",
        "python -m pip wheel . --no-deps --wheel-dir dist",
    ):
        assert expected in ci
