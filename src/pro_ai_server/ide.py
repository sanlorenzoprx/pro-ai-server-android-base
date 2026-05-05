from dataclasses import dataclass
import subprocess
import shutil
from typing import Callable


IDE_CLIS: tuple[str, ...] = ("code", "cursor", "codium", "windsurf")
LAUNCH_IDE_CLIS: tuple[str, ...] = ("code", "cursor")
FOLLOW_UP_IDE_CLIS: tuple[str, ...] = ("windsurf", "jetbrains")
CONTINUE_EXTENSION_ID = "Continue.continue"


@dataclass(frozen=True)
class IdeCli:
    command: str
    path: str | None

    @property
    def installed(self) -> bool:
        return self.path is not None


@dataclass(frozen=True)
class IdeExtensionStatus:
    ide: IdeCli
    extension_id: str
    installed: bool | None
    error: str | None = None


@dataclass(frozen=True)
class IdeReadiness:
    ide: IdeCli
    launch_supported: bool
    follow_up: bool
    continue_installed: bool | None
    state: str
    next_action: str

    @property
    def ready(self) -> bool:
        return self.state == "ready"


def detect_ide_clis(
    commands: tuple[str, ...] = IDE_CLIS,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[IdeCli, ...]:
    detected: list[IdeCli] = []
    for command in commands:
        try:
            path = which(command)
        except OSError:
            path = None
        detected.append(IdeCli(command=command, path=path))
    return tuple(detected)


def installed_ide_clis(
    commands: tuple[str, ...] = IDE_CLIS,
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[IdeCli, ...]:
    return tuple(cli for cli in detect_ide_clis(commands, which) if cli.installed)


def launch_ide_readiness_matrix(
    *,
    which: Callable[[str], str | None] = shutil.which,
    run: Callable[[list[str]], subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[IdeReadiness, ...]:
    detected = {ide.command: ide for ide in detect_ide_clis(LAUNCH_IDE_CLIS + FOLLOW_UP_IDE_CLIS, which)}
    readiness: list[IdeReadiness] = []
    for command in LAUNCH_IDE_CLIS:
        ide = detected[command]
        status = detect_continue_extension_status(ide, run=run)
        readiness.append(_readiness_for_launch_ide(status))
    for command in FOLLOW_UP_IDE_CLIS:
        ide = detected[command]
        readiness.append(
            IdeReadiness(
                ide=ide,
                launch_supported=False,
                follow_up=True,
                continue_installed=None,
                state="follow-up",
                next_action=f"{_display_name(command)} support is planned after the DevStack launch.",
            )
        )
    return tuple(readiness)


def list_installed_extensions(
    ide: IdeCli,
    *,
    run: Callable[[list[str]], subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[str, ...]:
    if not ide.path:
        raise ValueError(f"{ide.command} is not installed.")

    result = run([ide.path, "--list-extensions"], capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "extension listing failed"
        raise OSError(message)

    return tuple(line.strip() for line in result.stdout.splitlines() if line.strip())


def detect_continue_extension_status(
    ide: IdeCli,
    *,
    run: Callable[[list[str]], subprocess.CompletedProcess[str]] = subprocess.run,
) -> IdeExtensionStatus:
    if not ide.installed:
        return IdeExtensionStatus(ide=ide, extension_id=CONTINUE_EXTENSION_ID, installed=None)

    try:
        extensions = list_installed_extensions(ide, run=run)
    except OSError as exc:
        return IdeExtensionStatus(
            ide=ide,
            extension_id=CONTINUE_EXTENSION_ID,
            installed=None,
            error=str(exc),
        )

    installed = any(extension.lower() == CONTINUE_EXTENSION_ID.lower() for extension in extensions)
    return IdeExtensionStatus(ide=ide, extension_id=CONTINUE_EXTENSION_ID, installed=installed)


def install_continue_extension(
    ide: IdeCli,
    *,
    run: Callable[[list[str]], subprocess.CompletedProcess[str]] = subprocess.run,
) -> IdeExtensionStatus:
    if not ide.path:
        raise ValueError(f"{ide.command} is not installed.")

    result = run(
        [ide.path, "--install-extension", CONTINUE_EXTENSION_ID],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "extension installation failed"
        raise OSError(message)

    return detect_continue_extension_status(ide, run=run)


def _readiness_for_launch_ide(status: IdeExtensionStatus) -> IdeReadiness:
    ide = status.ide
    if not ide.installed:
        return IdeReadiness(
            ide=ide,
            launch_supported=True,
            follow_up=False,
            continue_installed=None,
            state="missing-cli",
            next_action=f"Install {_display_name(ide.command)} and make sure `{ide.command}` is on PATH.",
        )
    if status.installed is True:
        return IdeReadiness(
            ide=ide,
            launch_supported=True,
            follow_up=False,
            continue_installed=True,
            state="ready",
            next_action=f"Run `pro-ai-server configure-continue --mode usb` for {_display_name(ide.command)}.",
        )
    if status.installed is False:
        return IdeReadiness(
            ide=ide,
            launch_supported=True,
            follow_up=False,
            continue_installed=False,
            state="missing-continue",
            next_action=f"Run `pro-ai-server install-continue-extension --ide {ide.command}`.",
        )
    return IdeReadiness(
        ide=ide,
        launch_supported=True,
        follow_up=False,
        continue_installed=None,
        state="unknown",
        next_action=status.error or "Rerun doctor after confirming the IDE CLI can list extensions.",
    )


def _display_name(command: str) -> str:
    names = {
        "code": "VS Code",
        "cursor": "Cursor",
        "codium": "VSCodium",
        "windsurf": "Windsurf",
        "jetbrains": "JetBrains",
    }
    return names.get(command, command)
