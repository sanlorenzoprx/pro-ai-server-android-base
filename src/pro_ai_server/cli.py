from pathlib import Path
import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import urlretrieve

import typer
from rich.console import Console

from pro_ai_server.adb import select_adb_device_from_output
from pro_ai_server.agent.context import build_agent_context
from pro_ai_server.agent.autopilot import render_autopilot_result, run_autopilot_once
from pro_ai_server.agent.execution import (
    build_execution_packet,
    render_execution_packet,
    render_next_action,
    select_next_action,
    write_execution_packet,
)
from pro_ai_server.agent.handoff import build_handoff_view, render_handoff_view
from pro_ai_server.agent.improver import (
    build_self_improvement_review,
    render_self_improvement_review,
    write_self_improvement_review,
)
from pro_ai_server.agent.planner import build_plan_draft, write_plan
from pro_ai_server.agent.prime import build_prime_report, write_prime_report
from pro_ai_server.agent.queue import (
    build_decision_queue,
    default_decision_ledger_path,
    load_decision_events,
    record_decision,
    render_decision_history,
    render_decision_queue,
)
from pro_ai_server.agent.reporter import (
    build_implementation_report,
    build_ticket_status,
    discover_tickets,
    render_ticket_status,
    write_implementation_report,
)
from pro_ai_server.agent.reconciliation import (
    build_session_report_reconciliation,
    render_session_report_reconciliation,
)
from pro_ai_server.agent.session_archive import (
    apply_session_archive_plan,
    build_session_archive_plan,
    render_session_archive_plan,
)
from pro_ai_server.agent.sessions import (
    build_work_sessions,
    default_session_ledger_path,
    load_session_events,
    record_session_event,
    render_session_history,
    render_work_sessions,
)
from pro_ai_server.agent.ticketizer import (
    build_ticket_drafts,
    extract_recommendations,
    next_ticket_number,
    render_ticketize_preview,
    select_accepted_recommendations,
    write_ticket_drafts,
)
from pro_ai_server.android_compatibility import (
    ApkManifest,
    assess_android_compatibility,
    load_apk_manifest,
    parse_android_major,
    render_android_compatibility,
    render_android_validation_lanes,
    render_apk_manifest,
)
from pro_ai_server.android_compatibility import AndroidCompatibilityResult
from pro_ai_server.continue_config import (
    api_base_for_mode,
    devstack_restore_instructions,
    exposure_warnings,
    write_continue_config,
)
from pro_ai_server.device_scan import (
    DeviceScanOutputs,
    build_device_profile_from_scan_outputs,
    build_device_scan_commands,
    build_device_scan_summary_lines,
)
from pro_ai_server.diagnostics import build_diagnostics_report, write_diagnostics_report
from pro_ai_server.gateway.app import build_route_test_response
from pro_ai_server.gateway.config import load_gateway_config
from pro_ai_server.gateway.inventory import assess_gateway_model_inventory
from pro_ai_server.gateway.ollama_client import OllamaProxyError, proxy_ollama_json
from pro_ai_server.gateway.router import build_default_route_catalog, select_route
from pro_ai_server.gateway.server import GatewayStatusError, fetch_gateway_health, serve_gateway
from pro_ai_server.gateway.settings import GatewaySettings
from pro_ai_server.ide import detect_ide_clis
from pro_ai_server.ide import detect_continue_extension_status
from pro_ai_server.ide import install_continue_extension
from pro_ai_server.ide import installed_ide_clis
from pro_ai_server.ide import launch_ide_readiness_matrix
from pro_ai_server.installer_ui import build_installer_ui_flow, render_installer_ui_flow
from pro_ai_server.models import model_plan_for_profile, model_plan_for_ram
from pro_ai_server.native_runtime import (
    build_llama_server_command,
    build_native_runtime_config_for_model_plan,
    load_native_runtime_manifest,
)
from pro_ai_server.ollama import (
    DEFAULT_TEST_PROMPT,
    assess_model_inventory,
    assess_ollama_server_status,
    assess_ollama_test_prompt_response,
    build_ollama_generate_command,
    build_ollama_tags_command,
)
from pro_ai_server.packaging import validate_windows_platform_tools_layouts
from pro_ai_server.rag.context import build_context
from pro_ai_server.rag.indexer import DEFAULT_INDEX_PATH, index_project
from pro_ai_server.rag.search import search_index
from pro_ai_server.rag.store import IndexStore
from pro_ai_server.release_validation import validate_release_layout
from pro_ai_server.script_delivery import build_script_delivery_plan
from pro_ai_server.setup_receipt import build_setup_receipt, render_setup_receipt
from pro_ai_server.setup_workflow import mark_production_step_failed, plan_production_installer, plan_setup_workflow
from pro_ai_server.status import build_status_report, render_status_report
from pro_ai_server.termux_readiness import (
    TERMUX_API_PACKAGE,
    TERMUX_PACKAGE,
    TermuxReadinessResult,
    assess_termux_readiness,
    build_package_installer_command,
    build_termux_package_info_command,
    build_termux_readiness_commands,
    parse_package_installer,
    parse_pm_path_installed,
)
from pro_ai_server.termux_scripts import PHONE_STACK_BOOTSTRAP_SCRIPT, generate_termux_scripts, write_termux_scripts
from pro_ai_server.tailscale import build_tailscale_install_plan
from pro_ai_server.tailscale import tailscale_android_installed
from pro_ai_server.tailscale import tailscale_host_installed

app = typer.Typer(help="Pro AI Server: Android phone local AI server manager.")
agent_app = typer.Typer(help="Agentic CodeFlow workflow commands.")
app.add_typer(agent_app, name="agent")
console = Console()

TERMUX_FDROID_URL = "https://f-droid.org/packages/com.termux/"
TERMUX_API_FDROID_URL = "https://f-droid.org/packages/com.termux.api/"
FDROID_PACKAGE = "org.fdroid.fdroid"


@dataclass
class ModelProfile:
    name: str
    chat_model: str
    autocomplete_model: str
    note: str


class CommandError(RuntimeError):
    def __init__(self, command: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.command = command
        self.returncode = returncode
        self.stdout = stdout.strip()
        self.stderr = stderr.strip()
        message = self.stderr or self.stdout or f"Command failed with exit code {returncode}."
        super().__init__(message)


def package_root() -> Path:
    return Path(__file__).resolve().parent


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def bundled_adb_candidates() -> tuple[Path, ...]:
    relative_path = Path("embedded-tools") / "windows" / "platform-tools" / "adb.exe"
    return (
        package_root() / relative_path,
        project_root() / relative_path,
    )


def bundled_adb_path() -> Path:
    return bundled_adb_candidates()[0]


def resolve_adb() -> str | None:
    for bundled in bundled_adb_candidates():
        if bundled.exists():
            return str(bundled)

    system_adb = shutil.which("adb")
    if system_adb:
        return system_adb

    return None


def run_command(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise CommandError(command, result.returncode, result.stdout, result.stderr)
    return result.stdout.strip()


def run_optional_command(command: list[str]) -> str:
    try:
        return run_command(command)
    except CommandError as exc:
        return exc.stdout or exc.stderr


def adb_command(adb: str, args: list[str], serial: str | None = None) -> list[str]:
    if serial:
        return [adb, "-s", serial, *args]
    return [adb, *args]


def select_device_serial(adb: str, requested_serial: str | None = None) -> str:
    devices = run_command([adb, "devices"])
    selection = select_adb_device_from_output(devices, serial=requested_serial)
    if selection.ok and selection.selected:
        return selection.selected.serial

    raise ValueError(selection.error or "Unable to select an ADB device.")


def select_model_profile(ram_gb: float) -> ModelProfile:
    if ram_gb < 5:
        return ModelProfile(
            name="lightweight",
            chat_model="qwen2.5-coder:1.5b",
            autocomplete_model="qwen2.5-coder:0.5b",
            note="Experimental profile for low-memory phones.",
        )
    if ram_gb < 9:
        return ModelProfile(
            name="professional",
            chat_model="qwen2.5-coder:3b",
            autocomplete_model="qwen2.5-coder:1.5b-base",
            note="Recommended profile for 6GB-8GB Android phones.",
        )
    return ModelProfile(
        name="max",
        chat_model="qwen2.5-coder:7b",
        autocomplete_model="qwen2.5-coder:1.5b-base",
        note="High-memory profile for 10GB+ Android phones.",
    )


@app.command()
def doctor() -> None:
    """Check host computer requirements."""
    console.print("[bold]Pro AI Server Doctor[/bold]")

    adb_path = resolve_adb()
    if adb_path:
        if "embedded-tools" in adb_path:
            console.print(f"[green]OK[/green] bundled adb found: {adb_path}")
        else:
            console.print(f"[green]OK[/green] system adb found: {adb_path}")
    else:
        console.print("[yellow]Missing[/yellow] adb not found. App should bundle platform-tools for release builds.")

    python_path = shutil.which("python")
    if python_path:
        console.print(f"[green]OK[/green] python found: {python_path}")

    for ide in detect_ide_clis():
        if ide.installed:
            console.print(f"[green]OK[/green] IDE CLI found: {ide.command} -> {ide.path}")
            extension_status = detect_continue_extension_status(ide)
            if extension_status.installed is True:
                console.print(f"  [green]OK[/green] Continue extension installed: {extension_status.extension_id}")
            elif extension_status.installed is False:
                console.print(
                    "  [yellow]Missing[/yellow] Continue extension not installed. "
                    f"Run `pro-ai-server install-continue-extension --ide {ide.command}`."
                )
            elif extension_status.error:
                console.print(f"  [yellow]Unknown[/yellow] Continue extension status: {extension_status.error}")

    console.print("DevStack launch IDEs: VS Code and Cursor. Follow-up: Windsurf and JetBrains.")


@app.command("devstack-ide-status")
def devstack_ide_status() -> None:
    """Show DevStack launch IDE readiness for VS Code and Cursor."""
    console.print("[bold]DevStack IDE readiness[/bold]")
    for readiness in launch_ide_readiness_matrix():
        support = "launch" if readiness.launch_supported else "follow-up"
        installed = "installed" if readiness.ide.installed else "missing"
        console.print(f"{readiness.ide.command}: {readiness.state} ({support}, CLI {installed})")
        console.print(f"  Next: {readiness.next_action}")


@app.command("install-continue-extension")
def install_continue(
    ide_name: str | None = typer.Option(
        None,
        "--ide",
        help="IDE CLI to target: code, cursor, codium, or windsurf. Defaults to all installed IDE CLIs.",
    ),
) -> None:
    """Install the Continue extension into one or more supported IDEs and verify it."""
    detected = {ide.command: ide for ide in installed_ide_clis()}

    if ide_name:
        targets = [detected.get(ide_name)]
        if targets[0] is None:
            console.print(f"[red]IDE CLI not found or not installed: {ide_name}[/red]")
            raise typer.Exit(code=1)
    else:
        targets = list(detected.values())
        if not targets:
            console.print("[red]No supported IDE CLIs found. Install Cursor, VS Code, VSCodium, or Windsurf first.[/red]")
            raise typer.Exit(code=1)

    failed = False
    for ide in targets:
        assert ide is not None
        try:
            status = detect_continue_extension_status(ide)
            if status.installed is True:
                console.print(f"[green]OK[/green] Continue extension already installed in {ide.command}.")
                continue

            console.print(f"Installing Continue extension in {ide.command}...")
            status = install_continue_extension(ide)
            if status.installed is True:
                console.print(f"[green]Installed[/green] Continue extension in {ide.command}.")
            else:
                console.print(f"[yellow]Unknown[/yellow] Could not verify Continue extension in {ide.command}.")
                failed = True
        except (OSError, ValueError) as exc:
            console.print(f"[red]Failed to install Continue extension in {ide.command}.[/red]")
            console.print(str(exc))
            failed = True

    if failed:
        raise typer.Exit(code=1)


@app.command()
def scan(serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected.")) -> None:
    """Scan connected Android phone over ADB."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    try:
        selected_serial = select_device_serial(adb, serial)
        commands = build_device_scan_commands(adb, selected_serial)
        profile = build_device_profile_from_scan_outputs(
            selected_serial,
            DeviceScanOutputs(
                meminfo=run_command(list(commands.meminfo)),
                storage=run_command(list(commands.storage)),
                abi=run_command(list(commands.abi)),
                android_version=run_command(list(commands.android_version)),
                manufacturer=run_command(list(commands.manufacturer)),
                model=run_command(list(commands.model)),
                battery=run_command(list(commands.battery)),
            ),
        )
    except CommandError as exc:
        console.print("[red]ADB scan failed.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print("[red]Unable to parse device scan output.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    for line in build_device_scan_summary_lines(profile):
        if line.startswith("Warning: "):
            console.print(f"[yellow]{line}[/yellow]")
        else:
            console.print(line)


@app.command("android-compatibility")
def android_compatibility(
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
) -> None:
    """Classify Android compatibility before bootstrap or model install."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    try:
        selected_serial, profile, result, termux_installer, termux_api_installer = _scan_android_compatibility(
            adb,
            serial,
        )
    except CommandError as exc:
        console.print("[red]Android compatibility check failed while running ADB.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"Device: {profile.manufacturer} {profile.model} ({selected_serial})")
    console.print(f"Android: {profile.android_version}")
    console.print(f"ABI: {profile.abi}")
    console.print(f"RAM: {profile.ram_gb:.2f} GB")
    if termux_installer:
        console.print(f"Termux installer: {termux_installer}")
    if termux_api_installer:
        console.print(f"Termux:API installer: {termux_api_installer}")

    for line in render_android_compatibility(result):
        console.print(line)
    if not result.supported:
        raise typer.Exit(code=1)


def _scan_android_compatibility_for_setup(serial: str | None) -> AndroidCompatibilityResult:
    adb = resolve_adb()
    if not adb:
        raise ValueError("adb not found. Release builds should include bundled platform-tools.")
    _selected_serial, _profile, result, _termux_installer, _termux_api_installer = _scan_android_compatibility(adb, serial)
    if not result.supported:
        blockers = "; ".join(result.blockers) or result.summary
        raise ValueError(f"Android device is not production supported: {blockers}")
    return result


def _scan_android_compatibility(
    adb: str,
    serial: str | None,
) -> tuple[str, object, AndroidCompatibilityResult, str | None, str | None]:
    selected_serial = select_device_serial(adb, serial)
    commands = build_device_scan_commands(adb, selected_serial)
    profile = build_device_profile_from_scan_outputs(
        selected_serial,
        DeviceScanOutputs(
            meminfo=run_command(list(commands.meminfo)),
            storage=run_command(list(commands.storage)),
            abi=run_command(list(commands.abi)),
            android_version=run_command(list(commands.android_version)),
            manufacturer=run_command(list(commands.manufacturer)),
            model=run_command(list(commands.model)),
            battery=run_command(list(commands.battery)),
        ),
    )
    termux_installer = parse_package_installer(
        run_optional_command(list(build_package_installer_command(TERMUX_PACKAGE, selected_serial, adb=adb))),
        TERMUX_PACKAGE,
    )
    termux_api_installer = parse_package_installer(
        run_optional_command(list(build_package_installer_command(TERMUX_API_PACKAGE, selected_serial, adb=adb))),
        TERMUX_API_PACKAGE,
    )
    result = assess_android_compatibility(
        profile,
        termux_installer=termux_installer,
        termux_api_installer=termux_api_installer,
    )
    return selected_serial, profile, result, termux_installer, termux_api_installer


def _production_profile_from_compatibility(result: AndroidCompatibilityResult) -> str | None:
    if result.model_tier in {"lightweight", "professional", "max"}:
        return result.model_tier
    return None


@app.command("apk-manifest")
def apk_manifest(
    android_version: str | None = typer.Option(
        None,
        "--android-version",
        help="Optional Android version used to select manifest entries and setup flags.",
    ),
    manifest_path: Path | None = typer.Option(None, "--manifest", help="Optional APK manifest JSON path."),
) -> None:
    """Show pinned APK manifest values for the production install lane."""
    try:
        manifest = load_apk_manifest(manifest_path)
        android_major = parse_android_major(android_version) if android_version else None
        if android_version is not None and android_major is None:
            raise ValueError(f"Unable to parse Android version: {android_version}")
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    for line in render_apk_manifest(manifest, android_major):
        console.print(line)


@app.command("android-validation-matrix")
def android_validation_matrix() -> None:
    """Show production hardware validation lanes for Android version bands."""
    for line in render_android_validation_lanes():
        console.print(line)


@app.command()
def profile(ram_gb: float = typer.Argument(..., help="Detected phone RAM in GB.")) -> None:
    """Show recommended model profile for a RAM amount."""
    selected = select_model_profile(ram_gb)
    plan = model_plan_for_ram(ram_gb)
    console.print(f"Profile: [bold]{selected.name}[/bold]")
    console.print(f"Chat model: {selected.chat_model}")
    console.print(f"Autocomplete model: {selected.autocomplete_model}")
    console.print(f"Status: {plan.status}")
    console.print(selected.note)


@app.command()
def generate_scripts(
    mode: str = typer.Option("usb", help="Connection mode: usb, lan, or tailscale."),
    profile_name: str = typer.Option("professional", "--profile", help="Model profile to use."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
    output_dir: Path = typer.Option(Path("."), help="Directory where generated/termux will be written."),
) -> None:
    """Generate inspectable Termux setup/start/model scripts."""
    try:
        plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
        bundle = generate_termux_scripts(plan.chat_model, plan.autocomplete_model, mode=mode)
        written = write_termux_scripts(bundle, root=output_dir)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Generated Termux scripts for {bundle.mode} mode.[/green]")
    console.print(f"Ollama host binding: {bundle.ollama_host}")
    for path in written:
        console.print(str(path))


@app.command()
def configure_continue(
    mode: str = typer.Option("usb", help="Connection mode: usb, lan, or tailscale."),
    host: str | None = typer.Option(None, help="Host or IP for lan/tailscale modes."),
    profile_name: str = typer.Option("professional", "--profile", help="Model profile to use."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
) -> None:
    """Generate Continue config.yaml with backup protection."""
    try:
        plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
        result = write_continue_config(plan, mode=mode, host=host)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Wrote Continue config:[/green] {result.config_path}")
    console.print(f"API base: {result.api_base}")
    if result.backup_path:
        console.print(f"Backup: {result.backup_path}")

    ready_ides = [
        status.ide.command
        for status in (detect_continue_extension_status(ide) for ide in installed_ide_clis())
        if status.installed is True
    ]
    if ready_ides:
        console.print(f"Continue-ready IDEs: {', '.join(ready_ides)}")
    else:
        console.print(
            "[yellow]Warning:[/yellow] No supported IDE with the Continue extension was detected. "
            "Install it with `pro-ai-server install-continue-extension --ide cursor` "
            "or the equivalent IDE CLI before using this config."
        )

    for warning in exposure_warnings(mode):
        console.print(f"[yellow]Warning:[/yellow] {warning}")


@app.command("configure-devstack")
def configure_devstack(
    profile_name: str = typer.Option("professional", "--profile", help="Model profile to use."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
) -> None:
    """Generate the DevStack launch Continue config for VS Code and Cursor."""
    plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
    result = write_continue_config(plan, mode="usb", devstack=True)

    console.print(f"[green]Wrote DevStack Continue config:[/green] {result.config_path}")
    console.print(f"API base: {result.api_base}")
    console.print(f"Chat model: {plan.chat_model}")
    console.print(f"Autocomplete model: {plan.autocomplete_model}")
    for instruction in devstack_restore_instructions(result):
        console.print(instruction)

    ready_ides = [
        readiness.ide.command
        for readiness in launch_ide_readiness_matrix()
        if readiness.ready
    ]
    if ready_ides:
        console.print(f"DevStack-ready launch IDEs: {', '.join(ready_ides)}")
    else:
        console.print(
            "[yellow]Warning:[/yellow] No launch IDE is ready yet. "
            "Run `pro-ai-server devstack-ide-status`, then install Continue for VS Code or Cursor."
        )


@app.command()
def termux_check(
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
) -> None:
    """Check Termux, Termux:API, and Termux home readiness on the phone."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    try:
        selected_serial = select_device_serial(adb, serial)
        readiness_outputs = [
            run_optional_command([adb, *list(command[1:])])
            for command in build_termux_readiness_commands(selected_serial)
        ]
        package_info = run_optional_command([adb, *list(build_termux_package_info_command(selected_serial)[1:])])
    except CommandError as exc:
        console.print("[red]ADB Termux readiness check failed.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    result = assess_termux_readiness(*readiness_outputs, package_info_output=package_info)
    console.print(f"Device: {selected_serial}")
    if result.version_hint:
        console.print(f"Termux version: {result.version_hint}")
    for check in result.checks:
        status = "[green]OK[/green]" if check.ok else "[yellow]Needs attention[/yellow]"
        console.print(f"{status} {check.name}")
        if check.warning:
            console.print(f"  Warning: {check.warning}")
        if check.instruction:
            console.print(f"  Next: {check.instruction}")
    if not result.ok:
        raise typer.Exit(code=1)


@app.command("install-termux-apps")
def install_termux_apps(
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
    fdroid_apk: Path | None = typer.Option(None, "--fdroid-apk", help="Optional local F-Droid APK to install."),
    fdroid_url: str | None = typer.Option(None, "--fdroid-url", help="Optional pinned F-Droid APK URL to download."),
    fdroid_sha256: str | None = typer.Option(None, "--fdroid-sha256", help="Expected SHA-256 for --fdroid-url."),
    termux_apk: Path | None = typer.Option(None, "--termux-apk", help="Optional local Termux APK to install."),
    termux_url: str | None = typer.Option(None, "--termux-url", help="Optional pinned Termux APK URL to download."),
    termux_sha256: str | None = typer.Option(None, "--termux-sha256", help="Expected SHA-256 for --termux-url."),
    termux_api_apk: Path | None = typer.Option(
        None,
        "--termux-api-apk",
        help="Optional local Termux:API APK to install.",
    ),
    termux_api_url: str | None = typer.Option(
        None,
        "--termux-api-url",
        help="Optional pinned Termux:API APK URL to download.",
    ),
    termux_api_sha256: str | None = typer.Option(
        None,
        "--termux-api-sha256",
        help="Expected SHA-256 for --termux-api-url.",
    ),
    apk_cache_dir: Path = typer.Option(
        Path(".cache") / "pro-ai-server" / "apks",
        "--apk-cache-dir",
        help="Directory for downloaded APK files.",
    ),
    yes: bool = typer.Option(False, "--yes", help="Confirm local APK installation actions."),
) -> None:
    """Install or open trusted install pages for Termux and Termux:API."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    for label, apk in (("F-Droid", fdroid_apk), ("Termux", termux_apk), ("Termux:API", termux_api_apk)):
        if apk is not None and not apk.exists():
            console.print(f"[red]{label} APK not found:[/red] {apk}")
            raise typer.Exit(code=1)

    fdroid_apk = _resolve_downloaded_apk(
        label="F-Droid",
        local_apk=fdroid_apk,
        url=fdroid_url,
        sha256=fdroid_sha256,
        cache_dir=apk_cache_dir,
    )
    termux_apk = _resolve_downloaded_apk(
        label="Termux",
        local_apk=termux_apk,
        url=termux_url,
        sha256=termux_sha256,
        cache_dir=apk_cache_dir,
    )
    termux_api_apk = _resolve_downloaded_apk(
        label="Termux:API",
        local_apk=termux_api_apk,
        url=termux_api_url,
        sha256=termux_api_sha256,
        cache_dir=apk_cache_dir,
    )

    try:
        selected_serial = select_device_serial(adb, serial)
        console.print(f"Device: {selected_serial}")
        _install_fdroid_app(adb=adb, serial=selected_serial, apk=fdroid_apk, yes=yes)
        _open_fdroid_unknown_app_permission(adb, selected_serial)

        _install_or_open_termux_app(
            adb=adb,
            serial=selected_serial,
            label="Termux",
            package_name=TERMUX_PACKAGE,
            apk=termux_apk,
            fdroid_url=TERMUX_FDROID_URL,
            yes=yes,
        )
        _install_or_open_termux_app(
            adb=adb,
            serial=selected_serial,
            label="Termux:API",
            package_name=TERMUX_API_PACKAGE,
            apk=termux_api_apk,
            fdroid_url=TERMUX_API_FDROID_URL,
            yes=yes,
        )
    except CommandError as exc:
        console.print("[red]Termux app install automation failed while running an external command.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print("After installing, open Termux once so its home directory initializes.")
    console.print(f"Then run: pro-ai-server termux-check --serial {selected_serial}")


def _resolve_downloaded_apk(
    *,
    label: str,
    local_apk: Path | None,
    url: str | None,
    sha256: str | None,
    cache_dir: Path,
) -> Path | None:
    if url is None and sha256 is None:
        return local_apk
    if url is None or sha256 is None:
        console.print(f"[red]{label} download requires both URL and SHA-256.[/red]")
        raise typer.Exit(code=1)
    if local_apk is not None:
        console.print(f"[red]Use either local {label} APK or download URL, not both.[/red]")
        raise typer.Exit(code=1)

    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / _download_filename(url, label)
    console.print(f"Downloading {label} APK: {url}")
    urlretrieve(url, target)
    actual = _sha256_file(target)
    expected = sha256.lower()
    if actual.lower() != expected:
        target.unlink(missing_ok=True)
        console.print(f"[red]{label} APK SHA-256 mismatch.[/red]")
        console.print(f"Expected: {expected}")
        console.print(f"Actual:   {actual}")
        raise typer.Exit(code=1)
    console.print(f"[green]Verified[/green] {label} APK SHA-256.")
    return target


def _download_filename(url: str, label: str) -> str:
    path = Path(urlparse(url).path)
    if path.name:
        return path.name
    return f"{label.lower().replace(':', '-').replace(' ', '-')}.apk"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _install_fdroid_app(*, adb: str, serial: str, apk: Path | None, yes: bool) -> None:
    fdroid_output = run_optional_command(adb_command(adb, ["shell", "pm", "path", FDROID_PACKAGE], serial))
    if parse_pm_path_installed(fdroid_output):
        console.print("[green]OK[/green] F-Droid is installed.")
        return

    if apk is None:
        console.print(
            "[yellow]Missing[/yellow] F-Droid is not installed. "
            "Provide --fdroid-apk with --yes for automated install, then rerun this command."
        )
        return

    if not yes:
        console.print("[red]Refusing to install F-Droid APK without --yes.[/red]")
        raise typer.Exit(code=1)
    run_command(adb_command(adb, ["install", "-r", str(apk)], serial))
    console.print(f"[green]Installed[/green] F-Droid APK on Android device {serial}.")


def _open_fdroid_unknown_app_permission(adb: str, serial: str) -> None:
    fdroid_output = run_optional_command(adb_command(adb, ["shell", "pm", "path", FDROID_PACKAGE], serial))
    if not parse_pm_path_installed(fdroid_output):
        console.print("[yellow]F-Droid is not installed; skipping F-Droid unknown-app permission screen.[/yellow]")
        return

    run_command(
        adb_command(
            adb,
            [
                "shell",
                "am",
                "start",
                "-a",
                "android.settings.MANAGE_UNKNOWN_APP_SOURCES",
                "-d",
                f"package:{FDROID_PACKAGE}",
            ],
            serial,
        )
    )
    console.print("[yellow]Opened[/yellow] F-Droid Install unknown apps permission screen.")


def _install_or_open_termux_app(
    *,
    adb: str,
    serial: str,
    label: str,
    package_name: str,
    apk: Path | None,
    fdroid_url: str,
    yes: bool,
) -> None:
    installed_output = run_optional_command(adb_command(adb, ["shell", "pm", "path", package_name], serial))
    if parse_pm_path_installed(installed_output):
        console.print(f"[green]OK[/green] {label} is installed.")
        return

    if apk is not None:
        if not yes:
            console.print(f"[red]Refusing to install {label} APK without --yes.[/red]")
            raise typer.Exit(code=1)
        run_command(adb_command(adb, ["install", "-r", str(apk)], serial))
        console.print(f"[green]Installed[/green] {label} APK on Android device {serial}.")
        return

    run_command(
        adb_command(
            adb,
            ["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", fdroid_url],
            serial,
        )
    )
    console.print(f"[yellow]Opened[/yellow] {label} F-Droid page on Android device {serial}.")


def _validate_local_apks(
    *,
    fdroid_apk: Path | None,
    termux_apk: Path | None,
    termux_api_apk: Path | None,
) -> None:
    for label, apk in (("F-Droid", fdroid_apk), ("Termux", termux_apk), ("Termux:API", termux_api_apk)):
        if apk is not None and not apk.exists():
            console.print(f"[red]{label} APK not found:[/red] {apk}")
            raise typer.Exit(code=1)


def _resolve_setup_apks(
    *,
    fdroid_apk: Path | None,
    fdroid_url: str | None,
    fdroid_sha256: str | None,
    termux_apk: Path | None,
    termux_url: str | None,
    termux_sha256: str | None,
    termux_api_apk: Path | None,
    termux_api_url: str | None,
    termux_api_sha256: str | None,
    apk_cache_dir: Path,
) -> tuple[Path | None, Path | None, Path | None]:
    return (
        _resolve_downloaded_apk(
            label="F-Droid",
            local_apk=fdroid_apk,
            url=fdroid_url,
            sha256=fdroid_sha256,
            cache_dir=apk_cache_dir,
        ),
        _resolve_downloaded_apk(
            label="Termux",
            local_apk=termux_apk,
            url=termux_url,
            sha256=termux_sha256,
            cache_dir=apk_cache_dir,
        ),
        _resolve_downloaded_apk(
            label="Termux:API",
            local_apk=termux_api_apk,
            url=termux_api_url,
            sha256=termux_api_sha256,
            cache_dir=apk_cache_dir,
        ),
    )


def _manifest_inputs_for_setup(
    *,
    manifest: ApkManifest,
    android_version: str,
    fdroid_url: str | None,
    fdroid_sha256: str | None,
    termux_url: str | None,
    termux_sha256: str | None,
    termux_api_url: str | None,
    termux_api_sha256: str | None,
) -> tuple[str | None, str | None, str | None, str | None, str | None, str | None]:
    android_major = parse_android_major(android_version)
    if android_major is None:
        raise ValueError(f"Unable to parse Android version for APK manifest selection: {android_version}")

    for package_name in ("org.fdroid.fdroid", "com.termux", "com.termux.api"):
        if manifest.for_package(package_name, android_major) is None:
            raise ValueError(
                f"No pinned APK manifest entry for {package_name} on Android {android_major}. "
                "This device is not in the production APK install lane."
            )

    fdroid = manifest.for_package("org.fdroid.fdroid", android_major)
    termux = manifest.for_package("com.termux", android_major)
    termux_api = manifest.for_package("com.termux.api", android_major)
    assert fdroid is not None
    assert termux is not None
    assert termux_api is not None
    return (
        fdroid_url or fdroid.url,
        fdroid_sha256 or fdroid.sha256,
        termux_url or termux.url,
        termux_sha256 or termux.sha256,
        termux_api_url or termux_api.url,
        termux_api_sha256 or termux_api.sha256,
    )


def _install_termux_apps_for_setup(
    *,
    adb: str,
    serial: str,
    fdroid_apk: Path | None,
    termux_apk: Path | None,
    termux_api_apk: Path | None,
    yes: bool,
) -> None:
    _install_fdroid_app(adb=adb, serial=serial, apk=fdroid_apk, yes=yes)
    _open_fdroid_unknown_app_permission(adb, serial)
    _install_or_open_termux_app(
        adb=adb,
        serial=serial,
        label="Termux",
        package_name=TERMUX_PACKAGE,
        apk=termux_apk,
        fdroid_url=TERMUX_FDROID_URL,
        yes=yes,
    )
    _install_or_open_termux_app(
        adb=adb,
        serial=serial,
        label="Termux:API",
        package_name=TERMUX_API_PACKAGE,
        apk=termux_api_apk,
        fdroid_url=TERMUX_API_FDROID_URL,
        yes=yes,
    )


def _open_termux_once(adb: str, serial: str) -> None:
    output = run_optional_command(adb_command(adb, ["shell", "monkey", "-p", TERMUX_PACKAGE, "1"], serial))
    if "monkey aborted" in output.lower() or "no activities found" in output.lower():
        console.print("[yellow]Termux could not be opened yet; approve/install it on the phone first.[/yellow]")
        return
    console.print("[yellow]Opened[/yellow] Termux once to request home initialization.")


def _assess_termux_readiness_for_setup(adb: str, serial: str) -> TermuxReadinessResult:
    readiness_outputs = [
        run_optional_command([adb, *list(command[1:])])
        for command in build_termux_readiness_commands(serial)
    ]
    package_info = run_optional_command([adb, *list(build_termux_package_info_command(serial)[1:])])
    return assess_termux_readiness(*readiness_outputs, package_info_output=package_info)


def _print_termux_readiness_result(result: TermuxReadinessResult) -> None:
    if result.version_hint:
        console.print(f"Termux version: {result.version_hint}")
    for check in result.checks:
        status = "[green]OK[/green]" if check.ok else "[yellow]Needs attention[/yellow]"
        console.print(f"{status} {check.name}")
        if check.warning:
            console.print(f"  Warning: {check.warning}")
        if check.instruction:
            console.print(f"  Next: {check.instruction}")


def _request_termux_phone_stack(adb: str, serial: str, remote_home: str) -> str:
    home = remote_home.rstrip("/")
    command = adb_command(
        adb,
        [
            "shell",
            "am",
            "startservice",
            "--user",
            "0",
            "-n",
            "com.termux/com.termux.app.RunCommandService",
            "-a",
            "com.termux.RUN_COMMAND",
            "--es",
            "com.termux.RUN_COMMAND_PATH",
            f"~/{PHONE_STACK_BOOTSTRAP_SCRIPT}",
            "--es",
            "com.termux.RUN_COMMAND_WORKDIR",
            home,
            "--ez",
            "com.termux.RUN_COMMAND_BACKGROUND",
            "true",
        ],
        serial,
    )
    output = run_command(command)
    console.print(f"[green]Requested[/green] Termux phone stack bootstrap on device {serial}.")
    console.print(f"Bootstrap log: {home}/pro-ai-server-bootstrap.log")
    console.print(f"Server log: {home}/pro-ai-server.log")
    return output


@app.command()
def server_check(
    api_base: str = typer.Option("http://localhost:11434", help="Ollama API base URL."),
    profile_name: str = typer.Option("professional", "--profile", help="Model profile to verify."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
) -> None:
    """Check Ollama /api/tags and required model inventory."""
    plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
    command = build_ollama_tags_command(api_base)
    tags_output = run_optional_command(list(command))
    inventory = assess_model_inventory(plan, tags_output)

    console.print(f"Ollama API: {api_base.rstrip('/')}")
    console.print(f"Profile: {plan.profile}")
    if inventory.model_names:
        console.print("Models:")
        for model in inventory.model_names:
            console.print(f"  {model}")
    else:
        console.print("Models: none detected")

    for warning in inventory.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")
    for instruction in inventory.instructions:
        console.print(f"Next: {instruction}")
    if not inventory.ok:
        raise typer.Exit(code=1)


@app.command("test-prompt")
def test_prompt(
    api_base: str = typer.Option("http://localhost:11434", help="Ollama API base URL."),
    profile_name: str = typer.Option("professional", "--profile", help="Model profile whose chat model should be tested."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
    model: str | None = typer.Option(None, help="Optional explicit model to test instead of the profile chat model."),
    prompt: str = typer.Option(DEFAULT_TEST_PROMPT, help="Small prompt to send to /api/generate."),
) -> None:
    """Send a small Ollama /api/generate prompt through the configured endpoint."""
    plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
    selected_model = model or plan.chat_model
    command = build_ollama_generate_command(selected_model, prompt=prompt, api_base_url=api_base)
    generate_output = run_optional_command(list(command))
    status = assess_ollama_test_prompt_response(selected_model, generate_output)

    console.print(f"Ollama API: {api_base.rstrip('/')}")
    console.print(f"Test model: {selected_model}")
    if status.ok:
        console.print("[green]Test prompt succeeded.[/green]")
        console.print(f"Response: {status.response}")
        return

    for warning in status.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")
    for instruction in status.instructions:
        console.print(f"Next: {instruction}")
    raise typer.Exit(code=1)


@app.command("gateway-start")
def gateway_start(
    host: str = typer.Option("127.0.0.1", help="Gateway bind host. Defaults to loopback."),
    port: int = typer.Option(8765, help="Gateway bind port."),
    ollama_api_base: str = typer.Option("http://localhost:11434", help="Ollama API base URL."),
    timeout_seconds: float = typer.Option(30.0, help="Gateway upstream/status timeout in seconds."),
    model_profile: str = typer.Option("professional", "--model-profile", help="Default model profile."),
    chat_model: str | None = typer.Option(None, help="Optional chat model override."),
    autocomplete_model: str | None = typer.Option(None, help="Optional autocomplete model override."),
) -> None:
    """Start the local Pro CodeFlow gateway."""
    try:
        settings = GatewaySettings(
            host=host,
            port=port,
            ollama_api_base=ollama_api_base,
            timeout_seconds=timeout_seconds,
            model_profile=model_profile,
            chat_model=chat_model,
            autocomplete_model=autocomplete_model,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Starting Pro CodeFlow gateway:[/green] {settings.bind_url}")
    console.print(f"Ollama API base: {settings.ollama_api_base}")
    console.print(f"Model profile: {settings.model_profile}")
    try:
        serve_gateway(settings)
    except KeyboardInterrupt:
        console.print("Gateway stopped.")
    except OSError as exc:
        console.print(f"[red]Gateway failed to start:[/red] {exc}")
        raise typer.Exit(code=1) from exc


@app.command("gateway-status")
def gateway_status(
    host: str = typer.Option("127.0.0.1", help="Gateway host."),
    port: int = typer.Option(8765, help="Gateway port."),
    timeout_seconds: float = typer.Option(5.0, help="Gateway status timeout in seconds."),
) -> None:
    """Check the local Pro CodeFlow gateway health endpoint."""
    try:
        settings = GatewaySettings(host=host, port=port, timeout_seconds=timeout_seconds)
        health = fetch_gateway_health(settings)
    except (GatewayStatusError, ValueError) as exc:
        console.print("[red]Gateway is not ready.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    status = health.get("status", "unknown")
    if status == "ok":
        console.print(f"[green]OK[/green] Gateway ready at {settings.bind_url}")
    else:
        console.print(f"[yellow]Gateway status:[/yellow] {status}")
    console.print(f"Service: {health.get('service', 'unknown')}")
    console.print(f"Version: {health.get('version', 'unknown')}")


@app.command("gateway-route-test")
def gateway_route_test(
    task: str = typer.Option("chat", help="Task type to route: chat, autocomplete, refactor, test_generation."),
    prompt: str | None = typer.Option(None, help="Optional prompt sample for route testing."),
    config: Path | None = typer.Option(None, help="Optional gateway config YAML path."),
    model_profile: str | None = typer.Option(None, "--model-profile", help="Override default model profile."),
    chat_model: str | None = typer.Option(None, help="Optional chat model override."),
    autocomplete_model: str | None = typer.Option(None, help="Optional autocomplete model override."),
) -> None:
    """Show which model route the gateway would choose for a task."""
    try:
        settings = _gateway_settings_from_cli_options(
            config=config,
            model_profile=model_profile,
            chat_model=chat_model,
            autocomplete_model=autocomplete_model,
        )
        response = build_route_test_response(task, prompt=prompt, settings=settings)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    fallback_note = " (fallback)" if response.used_fallback else ""
    console.print(f"Task: {response.requested_task}{fallback_note}")
    console.print(f"Route: {response.route.task}")
    console.print(f"Profile: {response.route.profile}")
    console.print(f"Model: {response.route.model}")
    if response.route.fallback_model:
        console.print(f"Fallback model: {response.route.fallback_model}")
    console.print(f"Prompt received: {'yes' if response.prompt_received else 'no'}")


@app.command("gateway-proxy-test")
def gateway_proxy_test(
    task: str = typer.Option("chat", help="Task type to check."),
    all_routes: bool = typer.Option(False, "--all", help="Check all configured routes."),
    config: Path | None = typer.Option(None, help="Optional gateway config YAML path."),
    ollama_api_base: str | None = typer.Option(None, help="Override Ollama API base URL."),
    model_profile: str | None = typer.Option(None, "--model-profile", help="Override model profile."),
    chat_model: str | None = typer.Option(None, help="Optional chat model override."),
    autocomplete_model: str | None = typer.Option(None, help="Optional autocomplete model override."),
) -> None:
    """Check configured gateway route models against Ollama /api/tags."""
    try:
        settings = _gateway_settings_from_cli_options(
            config=config,
            ollama_api_base=ollama_api_base,
            model_profile=model_profile,
            chat_model=chat_model,
            autocomplete_model=autocomplete_model,
        )
        tags = proxy_ollama_json("GET", "/api/tags", settings=settings).payload
    except (ValueError, OllamaProxyError) as exc:
        console.print("[red]Gateway proxy test failed.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc

    routes = build_default_route_catalog(settings)
    selected_routes = routes if all_routes else {select_route(task, settings=settings).route.task: select_route(task, settings=settings).route}
    inventory = assess_gateway_model_inventory(selected_routes, tags)

    console.print(f"Ollama API: {settings.ollama_api_base}")
    for route in selected_routes.values():
        console.print(f"Route {route.task}: {route.model}")
        if route.fallback_model:
            console.print(f"  Fallback: {route.fallback_model}")
    if inventory.ok:
        console.print("[green]OK[/green] All checked route models are available.")
        return

    console.print("[yellow]Missing models:[/yellow]")
    for model in inventory.missing_models:
        console.print(f"  {model}")
        console.print(f"  Next: ollama pull {model}")
    raise typer.Exit(code=1)


@app.command("index")
def index_codebase(
    root: Path = typer.Argument(Path("."), help="Project root to index."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
) -> None:
    """Index a codebase for local keyword search."""
    result = index_project(root, db_path=db)
    console.print(f"Index DB: {result.db_path}")
    console.print(f"Indexed files: {result.file_count}")
    console.print(f"Indexed chunks: {result.chunk_count}")


@app.command("index-status")
def index_status(db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path.")) -> None:
    """Show local code index status."""
    store = IndexStore(db)
    try:
        status = store.status()
    except Exception as exc:  # noqa: BLE001 - CLI should show a friendly status failure.
        console.print("[red]Index is not ready.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    console.print(f"Index DB: {db}")
    console.print(f"Indexed files: {status.file_count}")
    console.print(f"Indexed chunks: {status.chunk_count}")


@app.command("search")
def search_codebase(
    query: str = typer.Argument(..., help="Search query."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
    limit: int = typer.Option(5, help="Maximum results."),
) -> None:
    """Search the local code index."""
    for result in search_index(query, db_path=db, limit=limit):
        console.print(f"{result.path.as_posix()}#{result.chunk_index} score={result.score}")
        console.print(result.text)


@app.command("context")
def context_codebase(
    query: str = typer.Argument(..., help="Context query."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
    limit: int = typer.Option(5, help="Maximum chunks."),
    max_chars: int = typer.Option(12000, help="Maximum context characters."),
) -> None:
    """Build deterministic prompt context from the local code index."""
    console.print(build_context(query, db_path=db, limit=limit, max_chars=max_chars))


@agent_app.command("prime")
def agent_prime(
    root: Path = typer.Option(Path("."), help="Repository root."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
) -> None:
    """Write an agent prime report with git and index status."""
    store = IndexStore(db)
    try:
        status = store.status()
        file_count = status.file_count
        chunk_count = status.chunk_count
    except Exception:  # noqa: BLE001 - prime should still work before indexing.
        file_count = None
        chunk_count = None
    report = build_prime_report(index_file_count=file_count, index_chunk_count=chunk_count)
    path = write_prime_report(report, root=root)
    console.print(f"Wrote agent prime: {path}")


@agent_app.command("context")
def agent_context(
    query: str = typer.Argument(..., help="Context query."),
    root: Path = typer.Option(Path("."), help="Repository root."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
    limit: int = typer.Option(5, help="Maximum chunks."),
    max_chars: int = typer.Option(12000, help="Maximum context characters."),
) -> None:
    """Build agent-ready context using project memory and the local index."""
    console.print(build_agent_context(query, root=root, db_path=db, limit=limit, max_chars=max_chars))


@agent_app.command("plan")
def agent_plan(
    feature: str = typer.Argument(..., help="Feature or change request to plan."),
    root: Path = typer.Option(Path("."), help="Repository root."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path."),
    limit: int = typer.Option(5, help="Maximum context chunks."),
    max_chars: int = typer.Option(12000, help="Maximum indexed context characters."),
    slug: str | None = typer.Option(None, help="Optional filename-safe plan slug."),
) -> None:
    """Create a draft implementation plan from memory, prime, and indexed context."""
    project_memory = _read_optional_text(root / ".agents" / "memory" / "project-memory.md")
    prime_report = _read_optional_text(root / ".agents" / "memory" / "last-prime.md")
    indexed_context = build_agent_context(feature, root=root, db_path=db, limit=limit, max_chars=max_chars)
    plan = build_plan_draft(
        feature,
        project_memory=project_memory,
        prime_report=prime_report,
        indexed_context=indexed_context,
    )
    try:
        path = write_plan(plan, feature, root=root, slug=slug)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"Wrote agent plan: {path}")


@agent_app.command("report")
def agent_report(
    ticket_id: str = typer.Argument(..., help="Ticket ID to report, for example TKT-P8-001."),
    summary: str = typer.Option(..., "--summary", help="Implementation summary."),
    root: Path = typer.Option(Path("."), help="Repository root."),
    slug: str | None = typer.Option(None, help="Optional filename-safe report slug."),
    file_created: list[str] | None = typer.Option(None, "--file-created", help="Created file path. Repeatable."),
    file_updated: list[str] | None = typer.Option(None, "--file-updated", help="Updated file path. Repeatable."),
    validation: list[str] | None = typer.Option(None, "--validation", help="Validation evidence. Repeatable."),
    deviation: list[str] | None = typer.Option(None, "--deviation", help="Deviation note. Repeatable."),
    follow_up: list[str] | None = typer.Option(None, "--follow-up", help="Follow-up note. Repeatable."),
) -> None:
    """Write a deterministic ticket implementation report."""
    ticket_path = next((ticket.path for ticket in discover_tickets(root) if ticket.ticket_id == ticket_id.upper()), None)
    report = build_implementation_report(
        ticket_id,
        summary=summary,
        ticket_path=ticket_path,
        files_created=tuple(file_created or ()),
        files_updated=tuple(file_updated or ()),
        validation=tuple(validation or ()),
        deviations=tuple(deviation or ()),
        follow_up=tuple(follow_up or ()),
    )
    try:
        path = write_implementation_report(ticket_id, report, root=root, slug=slug)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"Wrote implementation report: {path}")


@agent_app.command("status")
def agent_status(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-8."),
) -> None:
    """Show ticket status derived from build tickets and reports."""
    console.print(render_ticket_status(build_ticket_status(root, phase=phase)))


@agent_app.command("improve")
def agent_improve(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-9."),
    write: bool = typer.Option(False, "--write", help="Write the review under .agents/reports."),
    output: Path | None = typer.Option(None, "--output", help="Optional output path used with --write."),
) -> None:
    """Review tickets, reports, validation, and mistakes for process improvements."""
    review = build_self_improvement_review(root, phase=phase)
    rendered = render_self_improvement_review(review)
    if write:
        path = write_self_improvement_review(review, root=root, output=output)
        console.print(f"Wrote self-improvement review: {path}")
        return
    console.print(rendered)


@agent_app.command("ticketize")
def agent_ticketize(
    root: Path = typer.Option(Path("."), help="Repository root."),
    review: Path | None = typer.Option(None, "--review", help="Self-improvement review path."),
    accept: list[str] | None = typer.Option(None, "--accept", help="Accepted recommendation text. Repeatable."),
    all_recommendations: bool = typer.Option(False, "--all", help="Ticketize all recommendations from the review."),
    phase: str = typer.Option("phase-10", "--phase", help="Target build-ticket phase directory."),
    ticket_prefix: str = typer.Option("TKT-P10", "--ticket-prefix", help="Ticket ID prefix, for example TKT-P10."),
    start: int = typer.Option(0, "--start", help="Starting ticket number. Defaults to next available in phase."),
    write: bool = typer.Option(False, "--write", help="Write ticket drafts. Defaults to preview only."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing ticket files when used with --write."),
) -> None:
    """Turn accepted self-improvement recommendations into build-ticket drafts."""
    review_path = review or root / ".agents" / "reports" / "self-improvement-review.md"
    if not review_path.exists():
        console.print(f"[red]Self-improvement review not found:[/red] {review_path}")
        raise typer.Exit(code=1)
    recommendations = extract_recommendations(review_path.read_text(encoding="utf-8"))
    selected = select_accepted_recommendations(
        recommendations,
        accepted=tuple(accept or ()),
        include_all=all_recommendations,
    )
    start_number = start if start > 0 else next_ticket_number(root, phase=phase, ticket_prefix=ticket_prefix)
    drafts = build_ticket_drafts(selected, root=root, phase=phase, ticket_prefix=ticket_prefix, start=start_number)
    if write:
        try:
            paths = write_ticket_drafts(drafts, force=force)
        except FileExistsError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1) from exc
        console.print(f"Wrote {len(paths)} ticket draft(s).")
        for path in paths:
            console.print(str(path))
        return
    console.print(render_ticketize_preview(drafts))


@agent_app.command("decide")
def agent_decide(
    ticket_id: str = typer.Argument(..., help="Ticket ID to decide, for example TKT-P10-006."),
    decision: str = typer.Option(..., "--decision", help="Decision: accepted, deferred, or rejected."),
    reason: str = typer.Option(..., "--reason", help="Reason for the decision."),
    root: Path = typer.Option(Path("."), help="Repository root."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
    ledger: Path | None = typer.Option(None, "--ledger", help="Optional append-only decision ledger JSONL path."),
) -> None:
    """Record a local accepted/deferred/rejected ticket decision."""
    try:
        record = record_decision(ticket_id, decision=decision, reason=reason, root=root, path=queue, ledger_path=ledger)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"Recorded {record.decision} decision for {record.ticket_id}.")


@agent_app.command("queue")
def agent_queue(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-11."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
) -> None:
    """Show local accepted/deferred/rejected ticket decisions."""
    console.print(render_decision_queue(build_decision_queue(root, phase=phase, path=queue)))


@agent_app.command("history")
def agent_history(
    root: Path = typer.Option(Path("."), help="Repository root."),
    ledger: Path | None = typer.Option(None, "--ledger", help="Optional append-only decision ledger JSONL path."),
) -> None:
    """Show append-only ticket decision history."""
    ledger_path = ledger or default_decision_ledger_path(root)
    console.print(render_decision_history(load_decision_events(ledger_path)))


@agent_app.command("handoff")
def agent_handoff(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-13."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    include_reported: bool = typer.Option(False, "--include-reported", help="Include accepted tickets that already have reports."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
) -> None:
    """Show accepted tickets ready for implementation handoff."""
    view = build_handoff_view(
        root,
        phase=phase,
        ticket_id=ticket_id,
        include_reported=include_reported,
        queue_path=queue,
    )
    console.print(render_handoff_view(view))


@agent_app.command("next-action")
def agent_next_action(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-14."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    session_policy: str = typer.Option("available", "--session-policy", help="Session policy: available, resume, or all."),
) -> None:
    """Select the next accepted unreported ticket ready for execution."""
    try:
        selection = select_next_action(
            root,
            phase=phase,
            ticket_id=ticket_id,
            queue_path=queue,
            session_path=session_file,
            session_policy=session_policy,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(render_next_action(selection))


@agent_app.command("packet")
def agent_packet(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-14."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    session_policy: str = typer.Option("available", "--session-policy", help="Session policy: available, resume, or all."),
    include_context: bool = typer.Option(False, "--context", help="Include indexed agent context for the selected ticket."),
    db: Path = typer.Option(DEFAULT_INDEX_PATH, help="SQLite index path used with --context."),
    limit: int = typer.Option(5, help="Maximum context chunks used with --context."),
    max_chars: int = typer.Option(12000, help="Maximum indexed context characters used with --context."),
    write: bool = typer.Option(False, "--write", help="Write the execution packet under .agents/execution."),
    output: Path | None = typer.Option(None, "--output", help="Optional output path used with --write."),
) -> None:
    """Render or write a focused execution packet for the next ready ticket."""
    try:
        selection = select_next_action(
            root,
            phase=phase,
            ticket_id=ticket_id,
            queue_path=queue,
            session_path=session_file,
            session_policy=session_policy,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    indexed_context = ""
    if selection.item and include_context:
        indexed_context = build_agent_context(
            f"{selection.item.ticket_id} {selection.item.title}",
            root=root,
            db_path=db,
            limit=limit,
            max_chars=max_chars,
        )
    packet = build_execution_packet(
        root,
        phase=phase,
        ticket_id=ticket_id,
        queue_path=queue,
        session_path=session_file,
        session_policy=session_policy,
        indexed_context=indexed_context,
    )
    rendered = render_execution_packet(packet)
    if write:
        if packet is None:
            console.print(rendered)
            raise typer.Exit(code=1)
        path = write_execution_packet(packet, root=root, output=output)
        console.print(f"Wrote execution packet: {path}")
        return
    console.print(rendered)


@agent_app.command("session")
def agent_session(
    ticket_id: str = typer.Argument(..., help="Ticket ID to mark, for example TKT-P15-001."),
    event: str = typer.Option(..., "--event", help="Event: picked-up, started, or finished."),
    note: str = typer.Option("", "--note", help="Optional session note."),
    root: Path = typer.Option(Path("."), help="Repository root."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    ledger: Path | None = typer.Option(None, "--ledger", help="Optional append-only session ledger JSONL path."),
    packet: Path | None = typer.Option(None, "--packet", help="Optional execution packet path."),
) -> None:
    """Record a work-session event for an execution packet."""
    try:
        session = record_session_event(
            ticket_id,
            event=event,
            note=note,
            root=root,
            path=session_file,
            ledger_path=ledger,
            packet_path=packet,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(f"Recorded {session.status} session event for {session.ticket_id}.")


@agent_app.command("sessions")
def agent_sessions(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-15."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
) -> None:
    """Show current work-session status for execution packets."""
    sessions = build_work_sessions(root, phase=phase, ticket_id=ticket_id, path=session_file)
    console.print(render_work_sessions(sessions))


@agent_app.command("session-history")
def agent_session_history(
    root: Path = typer.Option(Path("."), help="Repository root."),
    ledger: Path | None = typer.Option(None, "--ledger", help="Optional append-only session ledger JSONL path."),
) -> None:
    """Show append-only work-session event history."""
    ledger_path = ledger or default_session_ledger_path(root)
    console.print(render_session_history(load_session_events(ledger_path)))


@agent_app.command("reconcile")
def agent_reconcile(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-17."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    fail_on_warning: bool = typer.Option(False, "--fail-on-warning", help="Exit nonzero when reconciliation warnings exist."),
) -> None:
    """Show session/report reconciliation warnings."""
    reconciliation = build_session_report_reconciliation(
        root,
        phase=phase,
        ticket_id=ticket_id,
        session_path=session_file,
    )
    console.print(render_session_report_reconciliation(reconciliation))
    if fail_on_warning and reconciliation.warning_count:
        raise typer.Exit(code=1)


@agent_app.command("session-archive")
def agent_session_archive(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-19."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    archive: Path | None = typer.Option(None, "--archive", help="Optional archive JSONL path."),
    write: bool = typer.Option(False, "--write", help="Archive candidates. Defaults to preview only."),
    fail_on_empty: bool = typer.Option(False, "--fail-on-empty", help="Exit nonzero when there are no archive candidates."),
) -> None:
    """Archive finished reported sessions out of current autopilot state."""
    plan = build_session_archive_plan(
        root,
        phase=phase,
        ticket_id=ticket_id,
        session_path=session_file,
        archive_path=archive,
        write=write,
    )
    result = apply_session_archive_plan(plan) if write else plan
    console.print(render_session_archive_plan(result))
    if fail_on_empty and result.archive_count == 0:
        raise typer.Exit(code=1)


@agent_app.command("autopilot")
def agent_autopilot(
    root: Path = typer.Option(Path("."), help="Repository root."),
    phase: str | None = typer.Option(None, "--phase", help="Optional phase directory filter, for example phase-18."),
    ticket_id: str | None = typer.Option(None, "--ticket", help="Optional ticket ID filter."),
    queue: Path | None = typer.Option(None, "--queue", help="Optional decision queue JSON path."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional current-state session JSON path."),
    ledger: Path | None = typer.Option(None, "--ledger", help="Optional append-only session ledger JSONL path."),
    session_policy: str = typer.Option("available", "--session-policy", help="Session policy: available, resume, or all."),
    max_tickets: int = typer.Option(1, "--max-tickets", help="Maximum tickets for this controlled autopilot tick."),
    execute: bool = typer.Option(False, "--execute", help="Write packet and optional session events. Defaults to preview."),
    start_session: bool = typer.Option(False, "--start-session", help="With --execute, record picked-up and started session events."),
    fail_on_stop: bool = typer.Option(False, "--fail-on-stop", help="Exit nonzero when autopilot stops before selecting a ticket."),
) -> None:
    """Run one controlled autopilot preflight and packet/session tick."""
    try:
        result = run_autopilot_once(
            root,
            phase=phase,
            ticket_id=ticket_id,
            queue_path=queue,
            session_path=session_file,
            session_ledger_path=ledger,
            session_policy=session_policy,
            max_tickets=max_tickets,
            execute=execute,
            start_session=start_session,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    console.print(render_autopilot_result(result))
    if fail_on_stop and result.status == "stopped" and result.ticket_id is None:
        raise typer.Exit(code=1)


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _gateway_settings_from_cli_options(
    *,
    config: Path | None = None,
    ollama_api_base: str | None = None,
    model_profile: str | None = None,
    chat_model: str | None = None,
    autocomplete_model: str | None = None,
) -> GatewaySettings:
    base = load_gateway_config(explicit_path=config).settings if config else GatewaySettings()
    return GatewaySettings(
        host=base.host,
        port=base.port,
        ollama_api_base=ollama_api_base or base.ollama_api_base,
        timeout_seconds=base.timeout_seconds,
        model_profile=model_profile or base.model_profile,
        chat_model=chat_model or base.chat_model,
        autocomplete_model=autocomplete_model or base.autocomplete_model,
        route_overrides=base.route_overrides,
    )


@app.command("setup-tailscale")
def setup_tailscale(
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
    android_apk: Path | None = typer.Option(
        None,
        "--android-apk",
        help="Optional local Tailscale Android APK to install with adb install.",
    ),
    install_host: bool = typer.Option(False, "--install-host", help="Install Tailscale on Windows with winget."),
    yes: bool = typer.Option(False, "--yes", help="Confirm host or phone app installation actions."),
) -> None:
    """Install/check Tailscale on Windows and Android for private remote access mode."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    if android_apk is not None and not android_apk.exists():
        console.print(f"[red]Tailscale Android APK not found:[/red] {android_apk}")
        raise typer.Exit(code=1)

    try:
        selected_serial = select_device_serial(adb, serial)
        plan = build_tailscale_install_plan(adb, serial=selected_serial, android_apk=android_apk)
        try:
            host_output = run_command(list(plan.host_check_command))
            host_ready = tailscale_host_installed(host_output)
        except CommandError:
            host_ready = False

        if host_ready:
            console.print("[green]OK[/green] Tailscale is available on this Windows host.")
        elif install_host:
            if not yes:
                console.print("[red]Refusing to install host Tailscale without --yes.[/red]")
                raise typer.Exit(code=1)
            run_command(list(plan.host_install_command))
            console.print("[green]Installed[/green] Tailscale on this Windows host with winget.")
        else:
            console.print(
                "[yellow]Missing[/yellow] Tailscale was not found on this Windows host. "
                "Re-run with --install-host --yes to install with winget."
            )

        android_output = run_optional_command(list(plan.android_check_command))
        if tailscale_android_installed(android_output):
            console.print(f"[green]OK[/green] Tailscale is installed on Android device {selected_serial}.")
        elif android_apk is not None:
            if not yes:
                console.print("[red]Refusing to install Android Tailscale APK without --yes.[/red]")
                raise typer.Exit(code=1)
            assert plan.android_install_command is not None
            run_command(list(plan.android_install_command))
            console.print(f"[green]Installed[/green] Tailscale APK on Android device {selected_serial}.")
        else:
            run_command(list(plan.android_open_store_command))
            console.print(
                f"[yellow]Opened[/yellow] Tailscale Play Store page on Android device {selected_serial}. "
                "Install it there, sign in, then use `configure-continue --mode tailscale --host <tailscale-host>`."
            )
    except CommandError as exc:
        console.print("[red]Tailscale setup failed while running an external command.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc


@app.command()
def setup(
    mode: str = typer.Option("usb", help="Connection mode: usb, lan, or tailscale."),
    host: str | None = typer.Option(None, help="Host or IP for lan/tailscale modes."),
    profile_name: str | None = typer.Option(None, "--profile", help="Model profile to use."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
    configure_continue_config: bool = typer.Option(True, "--continue/--no-continue", help="Plan/write Continue config."),
    create_usb_tunnel: bool | None = typer.Option(None, "--tunnel/--no-tunnel", help="Plan/create USB tunnel."),
    push: bool = typer.Option(False, "--push-scripts", help="Plan/push generated scripts to the phone."),
    execute: bool = typer.Option(False, help="Execute the planned local/device actions."),
    production: bool = typer.Option(False, "--production", help="Use the production installer state-machine plan."),
    advanced_exposure: bool = typer.Option(
        False,
        "--advanced-exposure",
        help="Allow LAN/Tailscale in production mode after explicitly accepting network exposure.",
    ),
    yes: bool = typer.Option(False, "--yes", help="Confirm setup actions that write config or expose network mode."),
    output_dir: Path = typer.Option(Path("."), help="Directory where generated/termux will be written."),
    remote_home: str = typer.Option("/data/data/com.termux/files/home", help="Remote Termux home directory."),
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
    auto_install_termux: bool = typer.Option(
        True,
        "--auto-install-termux/--no-auto-install-termux",
        help="In production execute mode, install/open F-Droid, Termux, and Termux:API before script push.",
    ),
    start_phone_stack: bool = typer.Option(
        True,
        "--start-phone-stack/--no-start-phone-stack",
        help="In production execute mode, request the Termux one-command phone stack bootstrap runner.",
    ),
    fdroid_apk: Path | None = typer.Option(None, "--fdroid-apk", help="Optional local F-Droid APK to install."),
    fdroid_url: str | None = typer.Option(None, "--fdroid-url", help="Optional pinned F-Droid APK URL to download."),
    fdroid_sha256: str | None = typer.Option(None, "--fdroid-sha256", help="Expected SHA-256 for --fdroid-url."),
    termux_apk: Path | None = typer.Option(None, "--termux-apk", help="Optional local Termux APK to install."),
    termux_url: str | None = typer.Option(None, "--termux-url", help="Optional pinned Termux APK URL to download."),
    termux_sha256: str | None = typer.Option(None, "--termux-sha256", help="Expected SHA-256 for --termux-url."),
    termux_api_apk: Path | None = typer.Option(
        None,
        "--termux-api-apk",
        help="Optional local Termux:API APK to install.",
    ),
    termux_api_url: str | None = typer.Option(
        None,
        "--termux-api-url",
        help="Optional pinned Termux:API APK URL to download.",
    ),
    termux_api_sha256: str | None = typer.Option(
        None,
        "--termux-api-sha256",
        help="Expected SHA-256 for --termux-api-url.",
    ),
    apk_cache_dir: Path = typer.Option(
        Path(".cache") / "pro-ai-server" / "apks",
        "--apk-cache-dir",
        help="Directory for downloaded APK files.",
    ),
    use_pinned_apk_manifest: bool = typer.Option(
        False,
        "--use-pinned-apk-manifest",
        help="Use the bundled reviewed APK manifest for missing F-Droid, Termux, and Termux:API URL/SHA-256 inputs.",
    ),
    apk_manifest_path: Path | None = typer.Option(
        None,
        "--apk-manifest",
        help="Optional APK manifest JSON path used with --use-pinned-apk-manifest.",
    ),
) -> None:
    """Plan or execute the guided MVP setup workflow."""
    try:
        production_plan = None
        compatibility_result = None
        compatibility_profile = None
        if production and mode.strip().lower() == "usb" and profile_name is None and ram_gb is None:
            compatibility_result = _scan_android_compatibility_for_setup(serial)
            compatibility_profile = _production_profile_from_compatibility(compatibility_result)
        effective_push = push or production
        plan = plan_setup_workflow(
            mode=mode,
            host=host,
            ram_gb=ram_gb,
            profile=compatibility_profile or profile_name,
            configure_continue=configure_continue_config,
            create_usb_tunnel=create_usb_tunnel,
            push_scripts=effective_push,
            generated_termux_dir=output_dir / "generated" / "termux",
            remote_termux_home=remote_home,
            serial=serial,
        )
        if production:
            production_plan = plan_production_installer(
                mode=mode,
                host=host,
                ram_gb=ram_gb,
                profile=compatibility_profile or profile_name,
                configure_continue=configure_continue_config,
                create_usb_tunnel=create_usb_tunnel,
                push_scripts=effective_push,
                generated_termux_dir=output_dir / "generated" / "termux",
                remote_termux_home=remote_home,
                serial=serial,
                allow_advanced_exposure=advanced_exposure,
            )
            plan = production_plan.setup_plan
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    if production_plan is not None:
        console.print(f"[bold]Production installer plan[/bold]: {production_plan.summary}")
        if compatibility_result is not None:
            console.print(f"Production compatibility tier: {compatibility_result.tier}")
            console.print(f"Production model profile: {compatibility_result.model_tier}")
            if compatibility_result.model_tier == "lightweight":
                console.print(
                    "[yellow]Warning:[/yellow] Using lightweight profile for customer-safe production setup."
                )
        for warning in production_plan.warnings:
            console.print(f"[yellow]Warning:[/yellow] {warning}")
        for index, step in enumerate(production_plan.steps, start=1):
            console.print(f"{index}. [bold]{step.title}[/bold] ({step.key}) - {step.detail}")
            if step.recovery:
                console.print(f"   Recovery: {step.recovery}")
    else:
        console.print(f"[bold]Setup plan[/bold]: {plan.summary}")
    for warning in plan.warnings:
        if production_plan is None:
            console.print(f"[yellow]Warning:[/yellow] {warning}")
    for index, step in enumerate(plan.steps, start=1):
        if production_plan is not None:
            break
        console.print(f"{index}. [bold]{step.title}[/bold] - {step.detail}")
        for note in step.notes:
            console.print(f"   Note: {note}")

    if not execute:
        console.print("Plan only. Re-run with --execute --yes to perform write/device actions.")
        return

    if (plan.requires_confirmation or configure_continue_config) and not yes:
        console.print("[red]Refusing to execute without --yes because setup writes config or changes exposure mode.[/red]")
        raise typer.Exit(code=1)

    try:
        continue_result = None
        selected_serial = None
        delivery_plan = None
        tunnel_requested = False
        ollama_status = None
        model_inventory_status = None
        test_prompt_status = None
        resolved_fdroid_apk = fdroid_apk
        resolved_termux_apk = termux_apk
        resolved_termux_api_apk = termux_api_apk

        bundle = generate_termux_scripts(
            plan.model_plan.chat_model,
            plan.model_plan.autocomplete_model,
            mode=plan.mode,
        )
        written = write_termux_scripts(bundle, root=output_dir)
        console.print(f"[green]Generated {len(written)} Termux files.[/green]")

        if configure_continue_config:
            continue_result = write_continue_config(plan.model_plan, mode=plan.mode, host=plan.host)
            console.print(f"[green]Wrote Continue config:[/green] {continue_result.config_path}")
            if continue_result.backup_path:
                console.print(f"Backup: {continue_result.backup_path}")

        if production and auto_install_termux:
            _validate_local_apks(
                fdroid_apk=fdroid_apk,
                termux_apk=termux_apk,
                termux_api_apk=termux_api_apk,
            )
            if not use_pinned_apk_manifest:
                resolved_fdroid_apk, resolved_termux_apk, resolved_termux_api_apk = _resolve_setup_apks(
                    fdroid_apk=fdroid_apk,
                    fdroid_url=fdroid_url,
                    fdroid_sha256=fdroid_sha256,
                    termux_apk=termux_apk,
                    termux_url=termux_url,
                    termux_sha256=termux_sha256,
                    termux_api_apk=termux_api_apk,
                    termux_api_url=termux_api_url,
                    termux_api_sha256=termux_api_sha256,
                    apk_cache_dir=apk_cache_dir,
                )

        if effective_push or (create_usb_tunnel is not False and plan.mode == "usb"):
            adb = resolve_adb()
            if not adb:
                console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
                raise typer.Exit(code=1)
            selected_serial = select_device_serial(adb, serial)

            if production and auto_install_termux:
                if use_pinned_apk_manifest:
                    manifest = load_apk_manifest(apk_manifest_path)
                    android_version = run_command(
                        adb_command(adb, ["shell", "getprop", "ro.build.version.release"], selected_serial)
                    )
                    (
                        fdroid_url,
                        fdroid_sha256,
                        termux_url,
                        termux_sha256,
                        termux_api_url,
                        termux_api_sha256,
                    ) = _manifest_inputs_for_setup(
                        manifest=manifest,
                        android_version=android_version,
                        fdroid_url=fdroid_url,
                        fdroid_sha256=fdroid_sha256,
                        termux_url=termux_url,
                        termux_sha256=termux_sha256,
                        termux_api_url=termux_api_url,
                        termux_api_sha256=termux_api_sha256,
                    )
                    console.print(f"[green]Using pinned APK manifest for Android {android_version.strip()}.[/green]")
                    resolved_fdroid_apk, resolved_termux_apk, resolved_termux_api_apk = _resolve_setup_apks(
                        fdroid_apk=fdroid_apk,
                        fdroid_url=fdroid_url,
                        fdroid_sha256=fdroid_sha256,
                        termux_apk=termux_apk,
                        termux_url=termux_url,
                        termux_sha256=termux_sha256,
                        termux_api_apk=termux_api_apk,
                        termux_api_url=termux_api_url,
                        termux_api_sha256=termux_api_sha256,
                        apk_cache_dir=apk_cache_dir,
                    )
                _install_termux_apps_for_setup(
                    adb=adb,
                    serial=selected_serial,
                    fdroid_apk=resolved_fdroid_apk,
                    termux_apk=resolved_termux_apk,
                    termux_api_apk=resolved_termux_api_apk,
                    yes=yes,
                )
                _open_termux_once(adb, selected_serial)
                termux_readiness = _assess_termux_readiness_for_setup(adb, selected_serial)
                _print_termux_readiness_result(termux_readiness)
                if not termux_readiness.ok:
                    console.print(
                        "[red]Production setup paused before script push because Termux is not ready.[/red]"
                    )
                    console.print(
                        "Approve any Android install prompts, open Termux once, then rerun setup --production --execute --yes."
                    )
                    raise typer.Exit(code=1)

            if effective_push:
                delivery_plan = build_script_delivery_plan(output_dir / "generated" / "termux", remote_home, selected_serial)
                run_command(
                    adb_command(adb, ["shell", "mkdir", "-p", f"{remote_home.rstrip('/')}/.shortcuts"], selected_serial)
                )
                run_command(
                    adb_command(adb, ["shell", "mkdir", "-p", f"{remote_home.rstrip('/')}/.termux"], selected_serial)
                )
                for command in delivery_plan.commands:
                    run_command([adb, *list(command[1:])])
                console.print(f"[green]Pushed Termux scripts to device {selected_serial}.[/green]")
                console.print("Run these inside Termux:")
                for command in delivery_plan.post_push_termux_commands:
                    console.print(f"  {command}")

            if production and start_phone_stack and delivery_plan is not None:
                try:
                    _request_termux_phone_stack(adb, selected_serial, remote_home)
                except CommandError as exc:
                    console.print("[yellow]Android blocked Termux RUN_COMMAND automation.[/yellow]")
                    console.print(str(exc))
                    console.print(f"Open Termux and run: ~/{PHONE_STACK_BOOTSTRAP_SCRIPT}")

            if create_usb_tunnel is not False and plan.mode == "usb":
                run_command(adb_command(adb, ["forward", "tcp:11434", "tcp:11434"], selected_serial))
                tunnel_requested = True
                console.print(f"[green]ADB forward tunnel requested for device {selected_serial}.[/green]")

        if production:
            api_base = api_base_for_mode(plan.mode, plan.host)
            tags_output = run_optional_command(list(build_ollama_tags_command(api_base)))
            ollama_status = assess_ollama_server_status(tags_output)
            model_inventory_status = assess_model_inventory(plan.model_plan, tags_output)
            generate_output = run_optional_command(
                list(build_ollama_generate_command(plan.model_plan.chat_model, api_base_url=api_base))
            )
            test_prompt_status = assess_ollama_test_prompt_response(plan.model_plan.chat_model, generate_output)
            if ollama_status.ok and model_inventory_status.ok and test_prompt_status.ok:
                console.print("[green]Production endpoint verified.[/green]")
            else:
                console.print("[yellow]Production endpoint is not verified yet.[/yellow]")
                for status in (ollama_status, model_inventory_status, test_prompt_status):
                    for warning in status.warnings:
                        console.print(f"[yellow]Warning:[/yellow] {warning}")
                    for instruction in status.instructions:
                        console.print(f"Next: {instruction}")
        receipt = build_setup_receipt(
            workflow_plan=plan,
            continue_result=continue_result,
            termux_bundle=bundle,
            written_termux_paths=written,
            delivery_plan=delivery_plan,
            selected_device_serial=selected_serial,
            pushed_scripts=effective_push,
            tunnel_requested=tunnel_requested,
            production_plan=production_plan,
            ollama_status=ollama_status,
            model_inventory_status=model_inventory_status,
            test_prompt_status=test_prompt_status,
        )
        console.print(render_setup_receipt(receipt))
    except CommandError as exc:
        console.print("[red]Setup failed while running an external command.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc


@app.command("installer-ui")
def installer_ui(
    profile_name: str | None = typer.Option(None, "--profile", help="Model profile to preview."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
    mock_failure: str | None = typer.Option(None, help="Optional production step key to show as a recoverable error."),
) -> None:
    """Preview the simple installer UI flow without mutating a phone."""
    try:
        plan = plan_production_installer(
            mode="usb",
            ram_gb=ram_gb,
            profile=profile_name,
            configure_continue=True,
            create_usb_tunnel=True,
            push_scripts=True,
        )
        if mock_failure:
            plan = mark_production_step_failed(
                plan,
                mock_failure,
                message=f"Mock failure at {mock_failure}.",
                debug_detail=f"mocked step failure: {mock_failure}",
            )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(render_installer_ui_flow(build_installer_ui_flow(plan)))


@app.command()
def push_scripts(
    generated_termux_dir: Path = typer.Option(
        Path("generated") / "termux",
        help="Local generated Termux script directory to push.",
    ),
    remote_home: str = typer.Option(
        "/data/data/com.termux/files/home",
        help="Remote Termux home directory.",
    ),
    serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected."),
) -> None:
    """Push generated Termux scripts to the selected phone with adb push."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    try:
        selected_serial = select_device_serial(adb, serial)
        plan = build_script_delivery_plan(generated_termux_dir, remote_home, selected_serial)
        run_command(adb_command(adb, ["shell", "mkdir", "-p", f"{remote_home.rstrip('/')}/.shortcuts"], selected_serial))
        for command in plan.commands:
            run_command([adb, *list(command[1:])])
    except CommandError as exc:
        console.print("[red]ADB script push failed.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Pushed Termux scripts to device {selected_serial}.[/green]")
    console.print("Run these inside Termux:")
    for command in plan.post_push_termux_commands:
        console.print(f"  {command}")
    for instruction in plan.instructions:
        console.print(f"[yellow]Note:[/yellow] {instruction}")


@app.command()
def tunnel(serial: str | None = typer.Option(None, help="ADB device serial to use when multiple phones are connected.")) -> None:
    """Create USB tunnel from host localhost:11434 to phone Ollama port."""
    adb = resolve_adb()
    if not adb:
        console.print("[red]adb not found. Release builds should include bundled platform-tools.[/red]")
        raise typer.Exit(code=1)

    try:
        selected_serial = select_device_serial(adb, serial)
        output = run_command(adb_command(adb, ["forward", "tcp:11434", "tcp:11434"], selected_serial))
    except CommandError as exc:
        console.print("[red]ADB forward tunnel failed.[/red]")
        console.print(str(exc))
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]ADB forward tunnel requested for device {selected_serial} on port 11434.[/green]")
    if output:
        console.print(output)


@app.command()
def diagnose(output: Path | None = typer.Option(None, help="Optional file path for the diagnostics report.")) -> None:
    """Print host, phone, and local Ollama diagnostics."""
    report = build_diagnostics_report(resolve_adb())
    console.print(report.text)
    if output:
        written = write_diagnostics_report(report, output)
        console.print(f"[green]Wrote diagnostics report:[/green] {written}")


@app.command("native-runtime-config")
def native_runtime_config(
    profile_name: str = typer.Option("professional", "--profile", help="Model profile to resolve."),
    ram_gb: float | None = typer.Option(None, help="Optional RAM value used to select a profile."),
    prefer: str = typer.Option("chat", help="Resolve the chat or autocomplete runtime lane."),
    models_root: Path = typer.Option(Path("models"), help="Root directory containing GGUF model files."),
    manifest_path: Path | None = typer.Option(None, "--manifest", help="Optional native runtime manifest JSON path."),
    llama_server: Path = typer.Option(Path("llama-server"), help="llama.cpp server executable path."),
    host: str = typer.Option("127.0.0.1", help="Native runtime bind host."),
    port: int = typer.Option(11434, help="Native runtime bind port."),
) -> None:
    """Render the resolved native runtime config without starting the engine."""
    try:
        plan = model_plan_for_ram(ram_gb) if ram_gb is not None else model_plan_for_profile(profile_name)
        manifest = load_native_runtime_manifest(manifest_path)
        config = build_native_runtime_config_for_model_plan(
            plan,
            models_root=models_root,
            prefer=prefer,
            host=host,
            port=port,
            manifest=manifest,
        )
        command = build_llama_server_command(config, executable=llama_server)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    console.print("[bold]Native runtime config[/bold]")
    console.print(f"Engine: {manifest.engine}")
    console.print(f"Profile: {plan.profile}")
    console.print(f"Preference: {prefer.strip().lower()}")
    console.print(f"Model contract: {config.model.contract_name}")
    console.print(f"GGUF path: {config.model.gguf_path}")
    console.print(f"API base: {config.api_base}")
    console.print(f"Context length: {config.context_length}")
    console.print(f"Threads: {config.threads}")
    console.print(f"GPU layers: {config.gpu_layers}")
    console.print(f"Startup command: {command.render()}")


@app.command()
def status(api_base: str = typer.Option("http://localhost:11434", help="Ollama API base URL to check.")) -> None:
    """Show concise phone, tunnel, Ollama, and IDE readiness."""
    adb = resolve_adb()
    adb_devices_output = run_optional_command([adb, "devices"]) if adb else None
    adb_forward_output = run_optional_command([adb, "forward", "--list"]) if adb else None
    tags_output = run_optional_command(list(build_ollama_tags_command(api_base)))
    ollama_status = assess_ollama_server_status(tags_output)
    ide_statuses = tuple(detect_continue_extension_status(ide) for ide in detect_ide_clis())

    report = build_status_report(
        adb_devices_output,
        adb_forward_output,
        ollama_status,
        ide_statuses,
        adb_path=adb,
        api_base=api_base,
    )
    for line in render_status_report(report):
        if line.startswith("OK "):
            console.print(f"[green]{line}[/green]")
        elif line.startswith("Needs attention "):
            console.print(f"[yellow]{line}[/yellow]")
        else:
            console.print(line)


@app.command()
def validate_platform_tools(root: Path = typer.Option(Path("."), help="Repository root to validate.")) -> None:
    """Validate bundled Windows Platform Tools ADB runtime files."""
    result = validate_windows_platform_tools_layouts(root)
    console.print(result.message)
    console.print(f"Source tree: {result.source_tree.message}")
    console.print(f"Packaged: {result.packaged.message}")
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def validate_release(root: Path = typer.Option(Path("."), help="Repository root to validate.")) -> None:
    """Validate release readiness: ADB files, package data, and CI gates."""
    result = validate_release_layout(root)
    console.print(result.summary)
    for issue in result.issues:
        path = f" ({issue.path})" if issue.path else ""
        console.print(f"[red]{issue.code}[/red]: {issue.message}{path}")
    if not result.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
