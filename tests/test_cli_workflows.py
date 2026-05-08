import hashlib
from pathlib import Path

from typer.testing import CliRunner

from pro_ai_server import cli
from pro_ai_server import native_runtime
from pro_ai_server.android_compatibility import ApkManifest, ApkManifestEntry
from pro_ai_server.continue_config import ContinueConfigWriteResult
from pro_ai_server.diagnostics import DiagnosticsReport
from pro_ai_server.gateway.ollama_client import OllamaProxyResult
from pro_ai_server.ide import IdeCli, IdeExtensionStatus, IdeReadiness
from pro_ai_server.native_runtime import NativeRuntimeProcess, NativeRuntimeReadiness
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


def test_setup_production_uses_compatibility_model_tier_without_explicit_profile(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        outputs = {
            ("adb", "devices"): "List of devices attached\nABC123\tdevice\n",
            ("adb", "-s", "ABC123", "shell", "cat", "/proc/meminfo"): "MemTotal: 5806680 kB",
            ("adb", "-s", "ABC123", "shell", "df", "-k", "/data"): (
                "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-2 100 1 67108864 1% /data"
            ),
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.cpu.abi"): "arm64-v8a\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.release"): "13\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.manufacturer"): "motorola\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.model"): "moto g 5G (2022)\n",
            ("adb", "-s", "ABC123", "shell", "dumpsys", "battery"): "level: 68",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux",
            ): "",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux.api",
            ): "",
        }
        return subprocess.CompletedProcess(command, 0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["setup", "--production", "--mode", "usb", "--no-continue", "--no-tunnel"])

    assert result.exit_code == 0
    assert "Production installer plan" in result.output
    assert "Production compatibility tier: yellow" in result.output
    assert "Production model profile: lightweight" in result.output
    assert "qwen2.5-coder:1.5b chat" in result.output
    assert "host-checks" in result.output
    assert "android-phone-detection" in result.output
    assert "test-prompt" in result.output
    assert "Plan only" in result.output
    assert "Setup plan" not in result.output


def test_setup_production_respects_explicit_profile_override_without_compatibility_scan(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: None)

    result = runner.invoke(
        cli.app,
        ["setup", "--production", "--mode", "usb", "--profile", "professional", "--no-continue", "--no-tunnel"],
    )

    assert result.exit_code == 0
    assert "Production model profile" not in result.output
    assert "professional profile" in result.output


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


def test_apk_manifest_command_prints_pinned_setup_options():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["apk-manifest", "--android-version", "13"])

    assert result.exit_code == 0
    assert "Pinned APK manifest" in result.output
    assert "--termux-url" in result.output
    assert "com.termux_1002.apk" in result.output
    assert "TBD" not in result.output


def test_android_validation_matrix_prints_required_android_lanes():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["android-validation-matrix"])

    assert result.exit_code == 0
    assert "android-12-13" in result.output
    assert "android-14-15-plus" in result.output


def test_setup_production_execute_installs_pushes_requests_phone_stack_and_verifies_endpoint(monkeypatch, tmp_path):
    runner = CliRunner()
    termux_apk = tmp_path / "termux.apk"
    termux_api_apk = tmp_path / "termux-api.apk"
    termux_apk.write_text("apk", encoding="utf-8")
    termux_api_apk.write_text("apk", encoding="utf-8")
    commands = []
    installed_packages = {"org.fdroid.fdroid"}

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"]:
            return subprocess.CompletedProcess(command, 0, stdout="package:/data/app/org.fdroid.fdroid/base.apk", stderr="")
        if command in (
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux.api"],
        ):
            if command[-1] in installed_packages:
                return subprocess.CompletedProcess(command, 0, stdout=f"package:/data/app/{command[-1]}/base.apk", stderr="")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        if command == ["adb", "-s", "ABC123", "install", "-r", str(termux_apk)]:
            installed_packages.add("com.termux")
            return subprocess.CompletedProcess(command, 0, stdout="Success", stderr="")
        if command == ["adb", "-s", "ABC123", "install", "-r", str(termux_api_apk)]:
            installed_packages.add("com.termux.api")
            return subprocess.CompletedProcess(command, 0, stdout="Success", stderr="")
        if command[:5] == ["adb", "-s", "ABC123", "shell", "pm"] and command[-1] in {"com.termux", "com.termux.api"}:
            return subprocess.CompletedProcess(command, 0, stdout=f"package:/data/app/{command[-1]}/base.apk", stderr="")
        if command[:6] == ["adb", "-s", "ABC123", "shell", "test", "-d"]:
            return subprocess.CompletedProcess(command, 0, stdout="yes", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "dumpsys", "package", "com.termux"]:
            return subprocess.CompletedProcess(command, 0, stdout="versionName=0.118.1", stderr="")
        if command == ["curl", "--silent", "--show-error", "http://localhost:11434/api/tags"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"models":[{"name":"qwen2.5-coder:1.5b"},{"name":"qwen2.5-coder:0.5b"}]}',
                stderr="",
            )
        if command[:7] == ["curl", "--silent", "--show-error", "-X", "POST", "-H", "Content-Type: application/json"]:
            return subprocess.CompletedProcess(command, 0, stdout='{"response":"pro-ai-server-ready"}', stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli.app,
        [
            "setup",
            "--production",
            "--execute",
            "--yes",
            "--profile",
            "lightweight",
            "--no-continue",
            "--no-tunnel",
            "--termux-apk",
            str(termux_apk),
            "--termux-api-apk",
            str(termux_api_apk),
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert ["adb", "-s", "ABC123", "install", "-r", str(termux_apk)] in commands
    assert ["adb", "-s", "ABC123", "install", "-r", str(termux_api_apk)] in commands
    assert any(command[:4] == ["adb", "-s", "ABC123", "push"] and "bootstrap-phone-stack.sh" in command[4] for command in commands)
    assert any(any("RunCommandService" in part for part in command) for command in commands)
    assert "Requested" in result.output
    assert "Production endpoint verified" in result.output
    assert "Test prompt" in result.output


def test_setup_production_execute_can_use_pinned_apk_manifest(monkeypatch, tmp_path):
    runner = CliRunner()
    apk_bytes = b"apk"
    apk_hash = hashlib.sha256(apk_bytes).hexdigest()
    commands = []
    installed_packages = {"org.fdroid.fdroid"}

    manifest = ApkManifest(
        entries=(
            ApkManifestEntry(
                package_name="org.fdroid.fdroid",
                label="F-Droid",
                version="1",
                min_android=7,
                max_android=None,
                url="https://downloads.example/fdroid.apk",
                sha256=apk_hash,
                source="fdroid",
            ),
            ApkManifestEntry(
                package_name="com.termux",
                label="Termux",
                version="1",
                min_android=7,
                max_android=None,
                url="https://downloads.example/termux.apk",
                sha256=apk_hash,
                source="fdroid",
            ),
            ApkManifestEntry(
                package_name="com.termux.api",
                label="Termux:API",
                version="1",
                min_android=7,
                max_android=None,
                url="https://downloads.example/termux-api.apk",
                sha256=apk_hash,
                source="fdroid",
            ),
        )
    )

    def fake_urlretrieve(url, target):
        Path(target).write_bytes(apk_bytes)
        return target, None

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.release"]:
            return subprocess.CompletedProcess(command, 0, stdout="13\n", stderr="")
        if command[:5] == ["adb", "-s", "ABC123", "shell", "pm"]:
            package_name = command[-1]
            if package_name in installed_packages:
                return subprocess.CompletedProcess(command, 0, stdout=f"package:/data/app/{package_name}/base.apk", stderr="")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        if command[:4] == ["adb", "-s", "ABC123", "install"]:
            if "termux-api.apk" in command[-1]:
                installed_packages.add("com.termux.api")
            elif "termux.apk" in command[-1]:
                installed_packages.add("com.termux")
            elif "fdroid.apk" in command[-1]:
                installed_packages.add("org.fdroid.fdroid")
            return subprocess.CompletedProcess(command, 0, stdout="Success", stderr="")
        if command[:6] == ["adb", "-s", "ABC123", "shell", "test", "-d"]:
            return subprocess.CompletedProcess(command, 0, stdout="yes", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "dumpsys", "package", "com.termux"]:
            return subprocess.CompletedProcess(command, 0, stdout="versionName=0.118.3", stderr="")
        if command == ["curl", "--silent", "--show-error", "http://localhost:11434/api/tags"]:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"models":[{"name":"qwen2.5-coder:1.5b"},{"name":"qwen2.5-coder:0.5b"}]}',
                stderr="",
            )
        if command[:7] == ["curl", "--silent", "--show-error", "-X", "POST", "-H", "Content-Type: application/json"]:
            return subprocess.CompletedProcess(command, 0, stdout='{"response":"pro-ai-server-ready"}', stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "load_apk_manifest", lambda _: manifest)
    monkeypatch.setattr(cli, "urlretrieve", fake_urlretrieve)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli.app,
        [
            "setup",
            "--production",
            "--execute",
            "--yes",
            "--profile",
            "lightweight",
            "--no-continue",
            "--no-tunnel",
            "--use-pinned-apk-manifest",
            "--apk-cache-dir",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0
    assert "Using pinned APK manifest for Android 13" in result.output
    assert ["adb", "-s", "ABC123", "install", "-r", str(tmp_path / "termux.apk")] in commands
    assert ["adb", "-s", "ABC123", "install", "-r", str(tmp_path / "termux-api.apk")] in commands
    assert "Production endpoint verified" in result.output


def test_setup_production_execute_pauses_before_push_when_termux_is_not_ready(monkeypatch, tmp_path):
    runner = CliRunner()
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"]:
            return subprocess.CompletedProcess(command, 0, stdout="package:/data/app/org.fdroid.fdroid/base.apk", stderr="")
        if command in (
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux.api"],
        ):
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        if command[:6] == ["adb", "-s", "ABC123", "shell", "test", "-d"]:
            return subprocess.CompletedProcess(command, 0, stdout="no", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "monkey", "-p", "com.termux", "1"]:
            return subprocess.CompletedProcess(command, 1, stdout="monkey aborted", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli.app,
        [
            "setup",
            "--production",
            "--execute",
            "--yes",
            "--profile",
            "lightweight",
            "--no-continue",
            "--no-tunnel",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Production setup paused before script push" in result.output
    assert "Termux is not installed" in result.output
    assert not any(command[:4] == ["adb", "-s", "ABC123", "push"] for command in commands)


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


def test_android_compatibility_reports_green_device(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        outputs = {
            ("adb", "devices"): "List of devices attached\nABC123\tdevice\n",
            ("adb", "-s", "ABC123", "shell", "cat", "/proc/meminfo"): "MemTotal: 6291456 kB",
            ("adb", "-s", "ABC123", "shell", "df", "-k", "/data"): (
                "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-2 100 1 67108864 1% /data"
            ),
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.cpu.abi"): "arm64-v8a\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.release"): "13\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.manufacturer"): "Google\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.model"): "Pixel Test\n",
            ("adb", "-s", "ABC123", "shell", "dumpsys", "battery"): "level: 55",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux",
            ): "package:com.termux installer=org.fdroid.fdroid",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux.api",
            ): "package:com.termux.api installer=org.fdroid.fdroid",
        }
        return subprocess.CompletedProcess(command, 0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["android-compatibility"])

    assert result.exit_code == 0
    assert "Compatibility tier: green" in result.output
    assert "Model tier: professional" in result.output
    assert "Termux installer: org.fdroid.fdroid" in result.output


def test_android_compatibility_exits_nonzero_for_play_store_termux(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        outputs = {
            ("adb", "devices"): "List of devices attached\nABC123\tdevice\n",
            ("adb", "-s", "ABC123", "shell", "cat", "/proc/meminfo"): "MemTotal: 6291456 kB",
            ("adb", "-s", "ABC123", "shell", "df", "-k", "/data"): (
                "Filesystem 1K-blocks Used Available Use% Mounted on\n/dev/block/dm-2 100 1 67108864 1% /data"
            ),
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.cpu.abi"): "arm64-v8a\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.build.version.release"): "13\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.manufacturer"): "Google\n",
            ("adb", "-s", "ABC123", "shell", "getprop", "ro.product.model"): "Pixel Test\n",
            ("adb", "-s", "ABC123", "shell", "dumpsys", "battery"): "level: 55",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux",
            ): "package:com.termux installer=com.android.vending",
            (
                "adb",
                "-s",
                "ABC123",
                "shell",
                "cmd",
                "package",
                "list",
                "packages",
                "-i",
                "com.termux.api",
            ): "",
        }
        return subprocess.CompletedProcess(command, 0, stdout=outputs[tuple(command)], stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["android-compatibility"])

    assert result.exit_code == 1
    assert "Compatibility tier: red" in result.output
    assert "Play Store Termux" in result.output


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


def test_install_termux_apps_opens_fdroid_pages_when_missing(monkeypatch):
    runner = CliRunner()
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command in (
            ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux.api"],
        ):
            if command[-1] == "org.fdroid.fdroid":
                return subprocess.CompletedProcess(command, 0, stdout="package:/data/app/org.fdroid.fdroid/base.apk", stderr="")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["install-termux-apps"])

    assert result.exit_code == 0
    assert [
        "adb",
        "-s",
        "ABC123",
        "shell",
        "am",
        "start",
        "-a",
        "android.settings.MANAGE_UNKNOWN_APP_SOURCES",
        "-d",
        "package:org.fdroid.fdroid",
    ] in commands
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
        "https://f-droid.org/packages/com.termux/",
    ] in commands
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
        "https://f-droid.org/packages/com.termux.api/",
    ] in commands
    assert "Opened" in result.output
    assert "termux-check --serial ABC123" in result.output


def test_install_termux_apps_installs_local_apks_with_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    termux_apk = tmp_path / "termux.apk"
    termux_api_apk = tmp_path / "termux-api.apk"
    termux_apk.write_text("apk", encoding="utf-8")
    termux_api_apk.write_text("apk", encoding="utf-8")
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command in (
            ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux"],
            ["adb", "-s", "ABC123", "shell", "pm", "path", "com.termux.api"],
        ):
            if command[-1] == "org.fdroid.fdroid":
                return subprocess.CompletedProcess(command, 0, stdout="package:/data/app/org.fdroid.fdroid/base.apk", stderr="")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli.app,
        [
            "install-termux-apps",
            "--termux-apk",
            str(termux_apk),
            "--termux-api-apk",
            str(termux_api_apk),
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert ["adb", "-s", "ABC123", "install", "-r", str(termux_apk)] in commands
    assert ["adb", "-s", "ABC123", "install", "-r", str(termux_api_apk)] in commands
    assert "Installed" in result.output


def test_install_termux_apps_refuses_local_apk_without_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    termux_apk = tmp_path / "termux.apk"
    termux_apk.write_text("apk", encoding="utf-8")

    def fake_run(command, capture_output, text):
        import subprocess

        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["install-termux-apps", "--termux-apk", str(termux_apk)])

    assert result.exit_code == 1
    assert "F-Droid is not installed" in result.output


def test_install_termux_apps_installs_fdroid_local_apk_with_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    fdroid_apk = tmp_path / "fdroid.apk"
    fdroid_apk.write_text("apk", encoding="utf-8")
    commands = []

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        if command == ["adb", "-s", "ABC123", "install", "-r", str(fdroid_apk)]:
            return subprocess.CompletedProcess(command, 0, stdout="Success", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["install-termux-apps", "--fdroid-apk", str(fdroid_apk), "--yes"])

    assert result.exit_code == 0
    assert ["adb", "-s", "ABC123", "install", "-r", str(fdroid_apk)] in commands
    assert "Installed" in result.output


def test_install_termux_apps_refuses_fdroid_local_apk_without_yes(monkeypatch, tmp_path):
    runner = CliRunner()
    fdroid_apk = tmp_path / "fdroid.apk"
    fdroid_apk.write_text("apk", encoding="utf-8")

    def fake_run(command, capture_output, text):
        import subprocess

        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["install-termux-apps", "--fdroid-apk", str(fdroid_apk)])

    assert result.exit_code == 1
    assert "F-Droid APK without --yes" in result.output


def test_install_termux_apps_reports_missing_fdroid_before_termux_pages(monkeypatch):
    runner = CliRunner()

    def fake_run(command, capture_output, text):
        import subprocess

        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(cli.app, ["install-termux-apps"])

    assert result.exit_code == 1
    assert "F-Droid is not installed" in result.output
    assert "Provide --fdroid-apk" in result.output


def test_install_termux_apps_downloads_and_verifies_pinned_fdroid_apk(monkeypatch, tmp_path):
    runner = CliRunner()
    apk_bytes = b"fdroid apk"
    apk_hash = hashlib.sha256(apk_bytes).hexdigest()
    commands = []

    def fake_urlretrieve(url, target):
        Path(target).write_bytes(apk_bytes)
        return target, None

    def fake_run(command, capture_output, text):
        import subprocess

        commands.append(command)
        if command == ["adb", "devices"]:
            return subprocess.CompletedProcess(command, 0, stdout="List of devices attached\nABC123\tdevice\n", stderr="")
        if command == ["adb", "-s", "ABC123", "shell", "pm", "path", "org.fdroid.fdroid"]:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="package not found")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "urlretrieve", fake_urlretrieve)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    result = runner.invoke(
        cli.app,
        [
            "install-termux-apps",
            "--fdroid-url",
            "https://downloads.example/fdroid.apk",
            "--fdroid-sha256",
            apk_hash,
            "--apk-cache-dir",
            str(tmp_path),
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert "Verified" in result.output
    assert ["adb", "-s", "ABC123", "install", "-r", str(tmp_path / "fdroid.apk")] in commands


def test_install_termux_apps_refuses_download_without_sha256(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")

    result = runner.invoke(cli.app, ["install-termux-apps", "--fdroid-url", "https://downloads.example/fdroid.apk"])

    assert result.exit_code == 1
    assert "requires both URL and SHA-256" in result.output


def test_install_termux_apps_refuses_download_with_sha256_mismatch(monkeypatch, tmp_path):
    runner = CliRunner()

    def fake_urlretrieve(url, target):
        Path(target).write_bytes(b"wrong apk")
        return target, None

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "urlretrieve", fake_urlretrieve)

    result = runner.invoke(
        cli.app,
        [
            "install-termux-apps",
            "--fdroid-url",
            "https://downloads.example/fdroid.apk",
            "--fdroid-sha256",
            "0" * 64,
            "--apk-cache-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "SHA-256 mismatch" in result.output


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


def test_configure_devstack_writes_usb_launch_config_and_ready_ides(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(cli, "default_continue_dir", lambda: tmp_path / ".continue", raising=False)
    monkeypatch.setattr(
        cli,
        "write_continue_config",
        lambda plan, mode, devstack: ContinueConfigWriteResult(
            config_path=tmp_path / ".continue" / "config.yaml",
            backup_path=tmp_path / ".continue" / "config.yaml.pro-ai-server-backup-20260502-131415",
            api_base="http://localhost:11434",
        ),
    )
    monkeypatch.setattr(
        cli,
        "launch_ide_readiness_matrix",
        lambda: (
            IdeReadiness(
                ide=IdeCli(command="cursor", path="C:/bin/cursor.cmd"),
                launch_supported=True,
                follow_up=False,
                continue_installed=True,
                state="ready",
                next_action="Run configure-continue.",
            ),
        ),
    )

    result = runner.invoke(cli.app, ["configure-devstack", "--profile", "professional"])

    assert result.exit_code == 0
    assert "Wrote DevStack Continue config" in result.output
    assert "API base: http://localhost:11434" in result.output
    assert "Chat model: qwen2.5-coder:3b" in result.output
    assert "Autocomplete model: qwen2.5-coder:1.5b-base" in result.output
    assert "To restore, copy" in result.output
    assert "DevStack-ready launch IDEs: cursor" in result.output


def test_configure_devstack_warns_when_launch_ide_is_not_ready(monkeypatch, tmp_path):
    runner = CliRunner()

    monkeypatch.setattr(
        cli,
        "write_continue_config",
        lambda plan, mode, devstack: ContinueConfigWriteResult(
            config_path=tmp_path / ".continue" / "config.yaml",
            backup_path=None,
            api_base="http://localhost:11434",
        ),
    )
    monkeypatch.setattr(cli, "launch_ide_readiness_matrix", lambda: ())

    result = runner.invoke(cli.app, ["configure-devstack"])

    assert result.exit_code == 0
    assert "No launch IDE is ready yet" in result.output
    assert "devstack-ide-status" in result.output


def test_status_prints_concise_readiness_report(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "run_optional_command", lambda command: "output")
    monkeypatch.setattr(cli, "assess_ollama_server_status", lambda output: OllamaServerStatus(ok=True))
    monkeypatch.setattr(cli, "build_native_runtime_lifecycle_status", lambda: None)
    monkeypatch.setattr(cli, "detect_ide_clis", lambda: ())
    monkeypatch.setattr(
        cli,
        "build_status_report",
        lambda devices,
        reverse,
        ollama,
        ides,
        adb_path,
        api_base="http://localhost:11434",
        native_runtime_status=None: ProAiStatus(
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


def test_native_runtime_config_prints_resolved_chat_config():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-config",
            "--profile",
            "professional",
            "--prefer",
            "chat",
            "--models-root",
            "bundled-models",
        ],
    )

    assert result.exit_code == 0
    assert "Native runtime config" in result.output
    assert "Profile: professional" in result.output
    assert "Preference: chat" in result.output
    assert "Model contract: qwen2.5-coder:3b" in result.output
    assert "GGUF path: bundled-models\\qwen2.5-coder-3b-instruct-q4_k_m.gguf" in result.output
    assert "API base: http://127.0.0.1:11434" in result.output
    assert "Context length: 8192" in result.output
    assert "Threads: 6" in result.output
    assert "Startup command: llama-server --model" in result.output
    assert "bundled-models\\qwen2.5-coder-3b-instruct-q4_k_m.gguf" in result.output
    assert "--ctx-size 8192" in result.output


def test_native_runtime_config_can_select_profile_from_ram():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-config",
            "--ram-gb",
            "4.5",
            "--prefer",
            "autocomplete",
            "--models-root",
            "bundled-models",
        ],
    )

    assert result.exit_code == 0
    assert "Profile: lightweight" in result.output
    assert "Preference: autocomplete" in result.output
    assert "Model contract: qwen2.5-coder:0.5b" in result.output
    assert "GGUF path: bundled-models\\qwen2.5-coder-0.5b-instruct-q4_k_m.gguf" in result.output


def test_native_runtime_config_can_use_custom_manifest(tmp_path):
    runner = CliRunner()
    manifest_path = tmp_path / "native-runtime-manifest.json"
    manifest_path.write_text(
        """{
          "engine": "test-engine",
          "profiles": {
            "professional": {
              "chat_model_filename": "custom-chat.gguf",
              "autocomplete_model_filename": "custom-autocomplete.gguf",
              "context_length": 2048,
              "threads": 2,
              "gpu_layers": 1
            }
          }
        }""",
        encoding="utf-8",
    )

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-config",
            "--profile",
            "professional",
            "--manifest",
            str(manifest_path),
            "--models-root",
            "custom-models",
        ],
    )

    assert result.exit_code == 0
    assert "Engine: test-engine" in result.output
    assert "GGUF path: custom-models\\custom-chat.gguf" in result.output
    assert "Context length: 2048" in result.output
    assert "Threads: 2" in result.output
    assert "GPU layers: 1" in result.output
    assert "--n-gpu-layers 1" in result.output


def test_native_runtime_config_rejects_invalid_preference():
    runner = CliRunner()

    result = runner.invoke(cli.app, ["native-runtime-config", "--prefer", "summary"])

    assert result.exit_code == 1
    assert "prefer value must be 'chat' or 'autocomplete'" in result.output


def test_native_runtime_assets_reports_missing_inputs(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-assets",
            "--profile",
            "professional",
            "--models-root",
            str(tmp_path / "models"),
            "--llama-server",
            str(tmp_path / "llama-server"),
        ],
    )

    assert result.exit_code == 1
    assert "Native runtime asset readiness" in result.output
    assert "Ready: False" in result.output
    assert "Missing llama-server" in result.output
    assert "qwen2.5-coder-3b-instruct-q4_k_m.gguf" in result.output


def test_native_runtime_assets_passes_when_profile_assets_exist(tmp_path):
    runner = CliRunner()
    llama_server = tmp_path / "llama-server"
    models_root = tmp_path / "models"
    models_root.mkdir()
    llama_server.write_text("binary", encoding="utf-8")
    (models_root / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf").write_text("chat", encoding="utf-8")
    (models_root / "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf").write_text("autocomplete", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-assets",
            "--profile",
            "lightweight",
            "--models-root",
            str(models_root),
            "--llama-server",
            str(llama_server),
        ],
    )

    assert result.exit_code == 0
    assert "Ready: True" in result.output
    assert "OK llama-server" in result.output
    assert "OK model:qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" in result.output
    assert "OK model:qwen2.5-coder-0.5b-instruct-q4_k_m.gguf" in result.output


def test_native_runtime_plan_reports_missing_inputs():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-plan",
            "--profile",
            "professional",
            "--models-root",
            "bundled-models",
            "--llama-server",
            "missing-llama-server",
        ],
    )

    assert result.exit_code == 0
    assert "Engine: llama.cpp" in result.output
    assert "Native runtime launch plan" in result.output
    assert "Ready: False" in result.output
    assert "Model: qwen2.5-coder:3b" in result.output
    assert "Missing llama-server" in result.output
    assert "Missing model-file" in result.output


def test_native_runtime_plan_reports_ready_inputs(tmp_path):
    runner = CliRunner()
    executable = tmp_path / "llama-server"
    models_root = tmp_path / "models"
    model_file = models_root / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    models_root.mkdir()
    executable.write_text("binary", encoding="utf-8")
    model_file.write_text("model", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-plan",
            "--profile",
            "professional",
            "--models-root",
            str(models_root),
            "--llama-server",
            str(executable),
        ],
    )

    assert result.exit_code == 0
    assert "Ready: True" in result.output
    assert "OK llama-server" in result.output
    assert "OK model-file" in result.output


def test_native_runtime_start_refuses_unready_plan():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-start",
            "--profile",
            "professional",
            "--models-root",
            "bundled-models",
            "--llama-server",
            "missing-llama-server",
        ],
    )

    assert result.exit_code == 1
    assert "Refusing to start native runtime" in result.output
    assert "Missing llama-server" in result.output
    assert "Missing model-file" in result.output


def test_native_runtime_start_launches_and_waits_when_ready(monkeypatch, tmp_path):
    runner = CliRunner()
    executable = tmp_path / "llama-server"
    models_root = tmp_path / "models"
    model_file = models_root / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    models_root.mkdir()
    executable.write_text("binary", encoding="utf-8")
    model_file.write_text("model", encoding="utf-8")
    state_path = tmp_path / "native-runtime-state.json"
    started = []

    def fake_start(launch_plan, force=False):
        started.append((launch_plan, force))
        return NativeRuntimeProcess(pid=4321, command=launch_plan.command)

    monkeypatch.setattr(cli, "start_native_runtime_process", fake_start)
    monkeypatch.setattr(
        cli,
        "wait_for_native_runtime_readiness",
        lambda api_base, timeout_seconds, interval_seconds: NativeRuntimeReadiness(
            ok=True,
            attempts=2,
            detail="runtime responded on /api/tags",
        ),
    )

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-start",
            "--profile",
            "professional",
            "--models-root",
            str(models_root),
            "--llama-server",
            str(executable),
            "--state-path",
            str(state_path),
        ],
    )

    assert result.exit_code == 0
    assert started
    assert started[0][1] is False
    assert "Started native runtime process" in result.output
    assert "PID 4321" in result.output
    assert state_path.exists()
    assert "Ready:" in result.output


def test_native_runtime_start_exits_when_readiness_fails(monkeypatch, tmp_path):
    runner = CliRunner()
    executable = tmp_path / "llama-server"
    model_file = tmp_path / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    state_path = tmp_path / "native-runtime-state.json"
    executable.write_text("binary", encoding="utf-8")
    model_file.write_text("model", encoding="utf-8")

    def fake_start(launch_plan, force=False):
        return NativeRuntimeProcess(pid=4321, command=launch_plan.command)

    monkeypatch.setattr(cli, "start_native_runtime_process", fake_start)
    monkeypatch.setattr(
        cli,
        "wait_for_native_runtime_readiness",
        lambda api_base, timeout_seconds, interval_seconds: NativeRuntimeReadiness(
            ok=False,
            attempts=3,
            detail="runtime did not respond",
        ),
    )

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-start",
            "--profile",
            "professional",
            "--models-root",
            str(tmp_path),
            "--llama-server",
            str(executable),
            "--state-path",
            str(state_path),
        ],
    )

    assert result.exit_code == 1
    assert "Started native runtime process" in result.output
    assert "Not ready yet" in result.output


def test_native_runtime_status_reports_missing_state(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["native-runtime-status", "--state-path", str(tmp_path / "missing.json")])

    assert result.exit_code == 0
    assert "Native runtime status" in result.output
    assert "State: missing" in result.output


def test_native_runtime_status_reports_recorded_state(monkeypatch, tmp_path):
    runner = CliRunner()
    state_path = tmp_path / "native-runtime-state.json"
    state_path.write_text(
        """{
          "api_base": "http://127.0.0.1:11434",
          "command": ["llama-server"],
          "gguf_path": "model.gguf",
          "model": "qwen2.5-coder:3b",
          "pid": 4321,
          "started_at": "2026-05-07T00:00:00+00:00"
        }""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli,
        "build_native_runtime_lifecycle_status",
        lambda path: native_runtime.build_native_runtime_lifecycle_status(
            path,
            fetch_tags=lambda api_base: '{"models":[]}',
            process_exists=lambda pid: True,
        ),
    )

    result = runner.invoke(cli.app, ["native-runtime-status", "--state-path", str(state_path)])

    assert result.exit_code == 0
    assert "State: recorded" in result.output
    assert "PID: 4321" in result.output
    assert "Process running: True" in result.output
    assert "Runtime ready: True" in result.output


def test_native_runtime_stop_reports_missing_state(tmp_path):
    runner = CliRunner()

    result = runner.invoke(cli.app, ["native-runtime-stop", "--state-path", str(tmp_path / "missing.json")])

    assert result.exit_code == 0
    assert "No native runtime state file found" in result.output


def test_native_runtime_stop_terminates_recorded_state(monkeypatch, tmp_path):
    runner = CliRunner()
    state_path = tmp_path / "native-runtime-state.json"
    state_path.write_text(
        """{
          "api_base": "http://127.0.0.1:11434",
          "command": ["llama-server"],
          "gguf_path": "model.gguf",
          "model": "qwen2.5-coder:3b",
          "pid": 4321,
          "started_at": "2026-05-07T00:00:00+00:00"
        }""",
        encoding="utf-8",
    )
    stopped = []

    monkeypatch.setattr(native_runtime, "_terminate_process", lambda pid: stopped.append(pid))

    result = runner.invoke(cli.app, ["native-runtime-stop", "--state-path", str(state_path)])

    assert result.exit_code == 0
    assert stopped == [4321]
    assert "Stopped native runtime process" in result.output
    assert "Removed state" in result.output


def test_native_runtime_doctor_reports_preflight(tmp_path):
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-doctor",
            "--profile",
            "professional",
            "--models-root",
            str(tmp_path / "models"),
            "--llama-server",
            str(tmp_path / "llama-server"),
            "--state-path",
            str(tmp_path / "native-runtime-state.json"),
        ],
    )

    assert result.exit_code == 0
    assert "Native runtime doctor" in result.output
    assert "Engine: llama.cpp" in result.output
    assert "Profile ready: False" in result.output
    assert "Lifecycle ready: False" in result.output
    assert "Missing llama-server" in result.output
    assert "State: missing" in result.output


def test_native_runtime_android_plan_prints_adb_asset_plan():
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-plan",
            "--profile",
            "professional",
            "--models-root",
            "models",
            "--llama-server",
            "llama-server",
            "--remote-root",
            "/data/local/tmp/pro-ai",
            "--serial",
            "ABC123",
        ],
    )

    assert result.exit_code == 0
    assert "Native Android runtime install plan" in result.output
    assert "/data/local/tmp/pro-ai/bin/llama-server" in result.output
    assert "adb -s ABC123 push llama-server" in result.output
    assert "adb -s ABC123 forward tcp:11434 tcp:11434" in result.output


def test_native_runtime_android_install_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-install",
            "--profile",
            "professional",
            "--models-root",
            "models",
            "--llama-server",
            "llama-server",
        ],
    )

    assert result.exit_code == 0
    assert "Native Android runtime install plan" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_install_refuses_execute_without_yes(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-install",
            "--profile",
            "professional",
            "--models-root",
            "models",
            "--llama-server",
            "llama-server",
            "--execute",
        ],
    )

    assert result.exit_code == 1
    assert "without --yes" in result.output


def test_native_runtime_android_install_executes_adb_commands(monkeypatch):
    runner = CliRunner()
    commands = []

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", lambda command: commands.append(command) or "")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-install",
            "--profile",
            "professional",
            "--models-root",
            "models",
            "--llama-server",
            "llama-server",
            "--execute",
            "--yes",
        ],
    )

    assert result.exit_code == 0
    assert commands
    assert any(command[:4] == ["adb", "-s", "ABC123", "push"] for command in commands)
    assert any(command == ["adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434"] for command in commands)
    assert "Installed native runtime assets" in result.output


def test_native_runtime_android_start_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-start",
            "--profile",
            "professional",
            "--remote-root",
            "/data/local/tmp/pro-ai",
        ],
    )

    assert result.exit_code == 0
    assert "Native Android runtime start plan" in result.output
    assert "/data/local/tmp/pro-ai/bin/llama-server" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_start_refuses_execute_without_yes(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-start", "--execute"])

    assert result.exit_code == 1
    assert "without --yes" in result.output


def test_native_runtime_android_start_executes_adb_commands(monkeypatch):
    runner = CliRunner()
    commands = []

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", lambda command: commands.append(command) or "")

    result = runner.invoke(cli.app, ["native-runtime-android-start", "--execute", "--yes"])

    assert result.exit_code == 0
    assert commands
    assert any(command[:4] == ["adb", "-s", "ABC123", "shell"] for command in commands)
    assert any(command == ["adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434"] for command in commands)
    assert "Requested native Android runtime start" in result.output
    assert "Remote PID file" in result.output


def test_native_runtime_android_status_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-status"])

    assert result.exit_code == 0
    assert "Native Android runtime status plan" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_status_executes_adb_commands(monkeypatch):
    runner = CliRunner()
    commands = []

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", lambda command: commands.append(command) or "running:1234")

    result = runner.invoke(cli.app, ["native-runtime-android-status", "--execute"])

    assert result.exit_code == 0
    assert any(command[:4] == ["adb", "-s", "ABC123", "shell"] for command in commands)
    assert any(command == ["adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434"] for command in commands)
    assert "running:1234" in result.output


def test_native_runtime_android_smoke_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-smoke"])

    assert result.exit_code == 0
    assert "Native Android runtime smoke plan" in result.output
    assert "/api/tags" in result.output
    assert "/api/generate" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_smoke_executes_forward_and_prompt(monkeypatch):
    runner = CliRunner()
    commands = []

    def fake_run_command(command):
        commands.append(command)
        return ""

    def fake_run_optional(command):
        commands.append(command)
        if command[-1].endswith("/api/tags"):
            return '{"models":[{"name":"qwen2.5-coder:3b"}]}'
        return '{"response":"pro-ai-server-ready"}'

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", fake_run_command)
    monkeypatch.setattr(cli, "run_optional_command", fake_run_optional)

    result = runner.invoke(cli.app, ["native-runtime-android-smoke", "--execute"])

    assert result.exit_code == 0
    assert ["adb", "-s", "ABC123", "forward", "tcp:11434", "tcp:11434"] in commands
    assert any(command[-1].endswith("/api/tags") for command in commands)
    assert any(command[-1].endswith("/api/generate") for command in commands)
    assert "Native Android runtime smoke succeeded" in result.output
    assert "pro-ai-server-ready" in result.output


def test_native_runtime_android_smoke_fails_when_tags_are_not_ready(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", lambda command: "")
    monkeypatch.setattr(cli, "run_optional_command", lambda command: "connection refused")

    result = runner.invoke(cli.app, ["native-runtime-android-smoke", "--execute"])

    assert result.exit_code == 1
    assert "Ollama tags request failed" in result.output


def test_native_runtime_android_smoke_path_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(
        cli.app,
        [
            "native-runtime-android-smoke-path",
            "--profile",
            "professional",
            "--models-root",
            "models",
            "--llama-server",
            "llama-server",
        ],
    )

    assert result.exit_code == 0
    assert "Native Android runtime smoke path" in result.output
    assert "Native Android runtime install plan" in result.output
    assert "Native Android runtime start plan" in result.output
    assert "Native Android runtime smoke plan" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_smoke_path_refuses_execute_without_yes(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-smoke-path", "--execute"])

    assert result.exit_code == 1
    assert "without --yes" in result.output


def test_native_runtime_android_smoke_path_executes_install_start_and_smoke(monkeypatch):
    runner = CliRunner()
    commands = []

    def fake_run_command(command):
        commands.append(command)
        return ""

    def fake_run_optional(command):
        commands.append(command)
        if command[-1].endswith("/api/tags"):
            return '{"models":[{"name":"qwen2.5-coder:3b"}]}'
        return '{"response":"pro-ai-server-ready"}'

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", fake_run_command)
    monkeypatch.setattr(cli, "run_optional_command", fake_run_optional)

    result = runner.invoke(cli.app, ["native-runtime-android-smoke-path", "--execute", "--yes"])

    assert result.exit_code == 0
    assert any(command[:4] == ["adb", "-s", "ABC123", "push"] for command in commands)
    assert any(command[:4] == ["adb", "-s", "ABC123", "shell"] for command in commands)
    assert any(command[-1].endswith("/api/tags") for command in commands)
    assert any(command[-1].endswith("/api/generate") for command in commands)
    assert "Installed and started native Android runtime" in result.output
    assert "Native Android runtime smoke succeeded" in result.output


def test_native_runtime_android_stop_prints_plan_without_execute(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-stop"])

    assert result.exit_code == 0
    assert "Native Android runtime stop plan" in result.output
    assert "Plan only" in result.output


def test_native_runtime_android_stop_refuses_execute_without_yes(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")

    result = runner.invoke(cli.app, ["native-runtime-android-stop", "--execute"])

    assert result.exit_code == 1
    assert "without --yes" in result.output


def test_native_runtime_android_stop_executes_adb_commands(monkeypatch):
    runner = CliRunner()
    commands = []

    monkeypatch.setattr(cli, "resolve_adb", lambda: "adb")
    monkeypatch.setattr(cli, "select_device_serial", lambda adb, serial: "ABC123")
    monkeypatch.setattr(cli, "run_command", lambda command: commands.append(command) or "stopped:1234")

    result = runner.invoke(cli.app, ["native-runtime-android-stop", "--execute", "--yes"])

    assert result.exit_code == 0
    assert any(command[:4] == ["adb", "-s", "ABC123", "shell"] for command in commands)
    assert any(command == ["adb", "-s", "ABC123", "forward", "--remove", "tcp:11434"] for command in commands)
    assert "stopped:1234" in result.output
    assert "Requested native Android runtime stop" in result.output


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
