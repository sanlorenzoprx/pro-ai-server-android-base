import subprocess

from pro_ai_server.ide import CONTINUE_EXTENSION_ID, IDE_CLIS, IdeCli, detect_continue_extension_status, detect_ide_clis
from pro_ai_server.ide import install_continue_extension, installed_ide_clis, list_installed_extensions
from pro_ai_server.ide import launch_ide_readiness_matrix


def test_detects_known_ide_clis_without_crashing_when_missing():
    found = {"code": "C:/bin/code.cmd", "windsurf": "C:/bin/windsurf.cmd"}

    detected = detect_ide_clis(which=lambda command: found.get(command))

    assert tuple(cli.command for cli in detected) == IDE_CLIS
    assert {cli.command: cli.path for cli in detected} == {
        "code": "C:/bin/code.cmd",
        "cursor": None,
        "codium": None,
        "windsurf": "C:/bin/windsurf.cmd",
    }


def test_missing_cli_lookup_errors_do_not_crash():
    def broken_which(command):
        if command == "cursor":
            raise OSError("lookup failed")
        return None

    detected = detect_ide_clis(which=broken_which)

    assert len(detected) == 4
    assert all(cli.path is None for cli in detected)


def test_installed_ide_clis_filters_missing_entries():
    found = {"codium": "C:/bin/codium.cmd"}

    detected = installed_ide_clis(which=lambda command: found.get(command))

    assert tuple(cli.command for cli in detected) == ("codium",)


def test_list_installed_extensions_reads_cli_output():
    ide = IdeCli(command="cursor", path="C:/bin/cursor.cmd")

    def fake_run(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, stdout="Continue.continue\nms-python.python\n", stderr="")

    detected = list_installed_extensions(ide, run=fake_run)

    assert detected == ("Continue.continue", "ms-python.python")


def test_detect_continue_extension_status_reports_installed():
    ide = IdeCli(command="cursor", path="C:/bin/cursor.cmd")

    def fake_run(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, stdout="Continue.continue\n", stderr="")

    status = detect_continue_extension_status(ide, run=fake_run)

    assert status.extension_id == CONTINUE_EXTENSION_ID
    assert status.installed is True
    assert status.error is None


def test_detect_continue_extension_status_reports_missing():
    ide = IdeCli(command="cursor", path="C:/bin/cursor.cmd")

    def fake_run(command, capture_output, text):
        return subprocess.CompletedProcess(command, 0, stdout="ms-python.python\n", stderr="")

    status = detect_continue_extension_status(ide, run=fake_run)

    assert status.installed is False


def test_install_continue_extension_installs_and_verifies():
    ide = IdeCli(command="cursor", path="C:/bin/cursor.cmd")
    calls = []

    def fake_run(command, capture_output, text):
        calls.append(command)
        if "--install-extension" in command:
            return subprocess.CompletedProcess(command, 0, stdout="installed", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="Continue.continue\n", stderr="")

    status = install_continue_extension(ide, run=fake_run)

    assert calls[0] == ["C:/bin/cursor.cmd", "--install-extension", CONTINUE_EXTENSION_ID]
    assert calls[1] == ["C:/bin/cursor.cmd", "--list-extensions"]
    assert status.installed is True


def test_launch_ide_readiness_matrix_marks_ready_missing_and_follow_up_states():
    found = {
        "code": "C:/bin/code.cmd",
        "cursor": "C:/bin/cursor.cmd",
        "windsurf": "C:/bin/windsurf.cmd",
    }

    def fake_run(command, capture_output, text):
        if command[0] == "C:/bin/code.cmd":
            return subprocess.CompletedProcess(command, 0, stdout="Continue.continue\n", stderr="")
        if command[0] == "C:/bin/cursor.cmd":
            return subprocess.CompletedProcess(command, 0, stdout="ms-python.python\n", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    matrix = launch_ide_readiness_matrix(which=lambda command: found.get(command), run=fake_run)
    by_command = {item.ide.command: item for item in matrix}

    assert tuple(by_command) == ("code", "cursor", "windsurf", "jetbrains")
    assert by_command["code"].state == "ready"
    assert by_command["code"].ready is True
    assert by_command["cursor"].state == "missing-continue"
    assert "install-continue-extension --ide cursor" in by_command["cursor"].next_action
    assert by_command["windsurf"].state == "follow-up"
    assert by_command["windsurf"].follow_up is True
    assert by_command["jetbrains"].state == "follow-up"


def test_launch_ide_readiness_matrix_reports_missing_launch_cli():
    matrix = launch_ide_readiness_matrix(which=lambda command: None)
    by_command = {item.ide.command: item for item in matrix}

    assert by_command["code"].state == "missing-cli"
    assert "Install VS Code" in by_command["code"].next_action
    assert by_command["cursor"].state == "missing-cli"
    assert "Install Cursor" in by_command["cursor"].next_action
