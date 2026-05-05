from pro_ai_server.packaging import (
    PACKAGED_WINDOWS_PLATFORM_TOOLS,
    REQUIRED_WINDOWS_PLATFORM_TOOL_FILES,
    SOURCE_TREE_WINDOWS_PLATFORM_TOOLS,
    WINDOWS_EXE_BUILD_SCRIPT,
    WINDOWS_EXE_DIST_PATH,
    build_windows_executable_packaging_plan,
    validate_windows_executable_packaging,
    validate_windows_platform_tools_dir,
    validate_windows_platform_tools_layouts,
)


def touch_files(directory, file_names):
    directory.mkdir(parents=True, exist_ok=True)
    for file_name in file_names:
        (directory / file_name).write_text("", encoding="utf-8")


def test_windows_platform_tools_validation_accepts_required_files(tmp_path):
    touch_files(tmp_path, REQUIRED_WINDOWS_PLATFORM_TOOL_FILES)

    result = validate_windows_platform_tools_dir(tmp_path)

    assert result.ok is True
    assert result.present_files == REQUIRED_WINDOWS_PLATFORM_TOOL_FILES
    assert result.missing_files == ()
    assert "ADB runtime is ready" in result.message
    assert "adb.exe" in result.message
    assert "AdbWinApi.dll" in result.message
    assert "AdbWinUsbApi.dll" in result.message


def test_windows_platform_tools_validation_reports_missing_files(tmp_path):
    touch_files(tmp_path, ("adb.exe",))

    result = validate_windows_platform_tools_dir(tmp_path)

    assert result.ok is False
    assert result.present_files == ("adb.exe",)
    assert result.missing_files == ("AdbWinApi.dll", "AdbWinUsbApi.dll")
    assert "ADB runtime is incomplete" in result.message
    assert "missing AdbWinApi.dll and AdbWinUsbApi.dll" in result.message


def test_windows_platform_tools_validation_does_not_require_fastboot(tmp_path):
    touch_files(tmp_path, REQUIRED_WINDOWS_PLATFORM_TOOL_FILES + ("fastboot.exe",))

    result = validate_windows_platform_tools_dir(tmp_path)

    assert result.ok is True
    assert "fastboot" not in result.present_files
    assert "fastboot" not in result.missing_files
    assert "fastboot" not in result.message.lower()


def test_windows_platform_tools_layout_validation_checks_source_and_packaged_layouts(tmp_path):
    touch_files(tmp_path / SOURCE_TREE_WINDOWS_PLATFORM_TOOLS, REQUIRED_WINDOWS_PLATFORM_TOOL_FILES)
    touch_files(tmp_path / PACKAGED_WINDOWS_PLATFORM_TOOLS, ("adb.exe",))

    result = validate_windows_platform_tools_layouts(tmp_path)

    assert result.ok is False
    assert result.source_tree.ok is True
    assert result.packaged.ok is False
    assert result.packaged.missing_files == ("AdbWinApi.dll", "AdbWinUsbApi.dll")
    assert "one or more layouts" in result.message


def test_windows_platform_tools_layout_validation_message_when_both_layouts_are_valid(tmp_path):
    touch_files(tmp_path / SOURCE_TREE_WINDOWS_PLATFORM_TOOLS, REQUIRED_WINDOWS_PLATFORM_TOOL_FILES)
    touch_files(tmp_path / PACKAGED_WINDOWS_PLATFORM_TOOLS, REQUIRED_WINDOWS_PLATFORM_TOOL_FILES)

    result = validate_windows_platform_tools_layouts(tmp_path)

    assert result.ok is True
    assert "both layouts" in result.message


def test_windows_executable_packaging_plan_defines_build_and_smoke_commands():
    plan = build_windows_executable_packaging_plan()

    assert plan.build_script == WINDOWS_EXE_BUILD_SCRIPT
    assert plan.exe_path == WINDOWS_EXE_DIST_PATH
    assert "pyinstaller" in plan.pyinstaller_command
    assert "--collect-data" in plan.pyinstaller_command
    assert "pro_ai_server" in plan.pyinstaller_command
    assert "--exclude-module" in plan.pyinstaller_command
    assert "build/pyinstaller/pro_ai_server_entry.py" in plan.pyinstaller_command
    assert "-m" not in plan.pyinstaller_command
    assert (WINDOWS_EXE_DIST_PATH.as_posix(), "setup", "--production", "--profile", "lightweight") in plan.smoke_commands
    assert (WINDOWS_EXE_DIST_PATH.as_posix(), "validate-platform-tools") in plan.smoke_commands


def test_windows_executable_packaging_validation_checks_script_and_dependency(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / WINDOWS_EXE_BUILD_SCRIPT).write_text("build", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        """
[project.optional-dependencies]
dev = ["pytest", "pyinstaller"]
""".strip(),
        encoding="utf-8",
    )

    result = validate_windows_executable_packaging(tmp_path)

    assert result.ok is True
    assert result.missing == ()


def test_windows_executable_packaging_validation_reports_missing_inputs(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        """
[project.optional-dependencies]
dev = ["pytest"]
""".strip(),
        encoding="utf-8",
    )

    result = validate_windows_executable_packaging(tmp_path)

    assert result.ok is False
    assert str(WINDOWS_EXE_BUILD_SCRIPT) in result.missing
    assert "pyinstaller dev dependency" in result.missing
