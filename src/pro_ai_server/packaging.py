from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_WINDOWS_PLATFORM_TOOL_FILES: tuple[str, ...] = (
    "adb.exe",
    "AdbWinApi.dll",
    "AdbWinUsbApi.dll",
)

SOURCE_TREE_WINDOWS_PLATFORM_TOOLS = Path("embedded-tools") / "windows" / "platform-tools"
PACKAGED_WINDOWS_PLATFORM_TOOLS = (
    Path("src") / "pro_ai_server" / "embedded-tools" / "windows" / "platform-tools"
)
WINDOWS_EXE_NAME = "pro-ai-server.exe"
WINDOWS_EXE_BUILD_SCRIPT = Path("scripts") / "build-windows-exe.ps1"
WINDOWS_DIST_DIR = Path("dist") / "pro-ai-server"
WINDOWS_EXE_DIST_PATH = WINDOWS_DIST_DIR / WINDOWS_EXE_NAME
PYINSTALLER_EXCLUDES: tuple[str, ...] = (
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    ".git",
    ".env",
    "build",
    "dist",
)
REQUIRED_CLI_SMOKE_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("doctor",),
    ("setup", "--production", "--profile", "lightweight"),
    ("status",),
    ("diagnose", "--output", "diagnostics.txt"),
    ("validate-platform-tools",),
)


@dataclass(frozen=True)
class PlatformToolsValidationResult:
    platform_tools_dir: Path
    present_files: tuple[str, ...]
    missing_files: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.missing_files

    @property
    def message(self) -> str:
        if self.ok:
            return (
                "Windows Platform Tools ADB runtime is ready at "
                f"{self.platform_tools_dir}; found {format_file_list(self.present_files)}."
            )
        return (
            "Windows Platform Tools ADB runtime is incomplete at "
            f"{self.platform_tools_dir}; missing {format_file_list(self.missing_files)}."
        )


@dataclass(frozen=True)
class PlatformToolsLayoutValidation:
    source_tree: PlatformToolsValidationResult
    packaged: PlatformToolsValidationResult

    @property
    def ok(self) -> bool:
        return self.source_tree.ok and self.packaged.ok

    @property
    def message(self) -> str:
        if self.ok:
            return "Bundled Windows Platform Tools ADB runtime files are present in both layouts."
        return "Bundled Windows Platform Tools ADB runtime files are missing from one or more layouts."


@dataclass(frozen=True)
class WindowsExecutablePackagingPlan:
    build_script: Path = WINDOWS_EXE_BUILD_SCRIPT
    dist_dir: Path = WINDOWS_DIST_DIR
    exe_path: Path = WINDOWS_EXE_DIST_PATH
    required_cli_smoke_commands: tuple[tuple[str, ...], ...] = REQUIRED_CLI_SMOKE_COMMANDS
    excludes: tuple[str, ...] = PYINSTALLER_EXCLUDES

    @property
    def pyinstaller_command(self) -> tuple[str, ...]:
        return (
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--name",
            "pro-ai-server",
            "--distpath",
            self.dist_dir.parent.as_posix(),
            "--workpath",
            "build/pyinstaller",
            "--specpath",
            "build/pyinstaller",
            "--collect-data",
            "pro_ai_server",
            "--add-data",
            "embedded-tools/windows/platform-tools;embedded-tools/windows/platform-tools",
            "--exclude-module",
            "pytest",
            "--exclude-module",
            "ruff",
            "build/pyinstaller/pro_ai_server_entry.py",
        )

    @property
    def smoke_commands(self) -> tuple[tuple[str, ...], ...]:
        return tuple((self.exe_path.as_posix(), *command) for command in self.required_cli_smoke_commands)


@dataclass(frozen=True)
class WindowsExecutablePackagingValidation:
    plan: WindowsExecutablePackagingPlan
    build_script_exists: bool
    pyproject_has_pyinstaller: bool

    @property
    def ok(self) -> bool:
        return self.build_script_exists and self.pyproject_has_pyinstaller

    @property
    def missing(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.build_script_exists:
            missing.append(str(self.plan.build_script))
        if not self.pyproject_has_pyinstaller:
            missing.append("pyinstaller dev dependency")
        return tuple(missing)


def validate_windows_platform_tools_dir(platform_tools_dir: str | Path) -> PlatformToolsValidationResult:
    directory = Path(platform_tools_dir)
    present_files = tuple(
        file_name for file_name in REQUIRED_WINDOWS_PLATFORM_TOOL_FILES if (directory / file_name).is_file()
    )
    missing_files = tuple(
        file_name for file_name in REQUIRED_WINDOWS_PLATFORM_TOOL_FILES if file_name not in present_files
    )
    return PlatformToolsValidationResult(
        platform_tools_dir=directory,
        present_files=present_files,
        missing_files=missing_files,
    )


def validate_windows_platform_tools_layouts(base_path: str | Path) -> PlatformToolsLayoutValidation:
    base = Path(base_path)
    return PlatformToolsLayoutValidation(
        source_tree=validate_windows_platform_tools_dir(base / SOURCE_TREE_WINDOWS_PLATFORM_TOOLS),
        packaged=validate_windows_platform_tools_dir(base / PACKAGED_WINDOWS_PLATFORM_TOOLS),
    )


def build_windows_executable_packaging_plan() -> WindowsExecutablePackagingPlan:
    return WindowsExecutablePackagingPlan()


def validate_windows_executable_packaging(base_path: str | Path) -> WindowsExecutablePackagingValidation:
    base = Path(base_path)
    pyproject_path = base / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8") if pyproject_path.is_file() else ""
    return WindowsExecutablePackagingValidation(
        plan=build_windows_executable_packaging_plan(),
        build_script_exists=(base / WINDOWS_EXE_BUILD_SCRIPT).is_file(),
        pyproject_has_pyinstaller="pyinstaller" in pyproject_text.lower(),
    )


def format_file_list(file_names: tuple[str, ...]) -> str:
    if not file_names:
        return "no files"
    if len(file_names) == 1:
        return file_names[0]
    if len(file_names) == 2:
        return f"{file_names[0]} and {file_names[1]}"
    return ", ".join(file_names[:-1]) + f", and {file_names[-1]}"
