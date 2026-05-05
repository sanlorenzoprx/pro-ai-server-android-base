from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pro_ai_server.continue_config import api_base_for_mode, exposure_warnings
from pro_ai_server.models import ModelPlan, model_plan_for_profile, model_plan_for_ram
from pro_ai_server.script_delivery import Command, build_script_delivery_plan
from pro_ai_server.termux_scripts import DEFAULT_SCRIPT_DIR, generate_termux_scripts


VALID_SETUP_MODES = {"usb", "lan", "tailscale"}
ADVANCED_EXPOSURE_MODES = {"lan", "tailscale"}


@dataclass(frozen=True)
class SetupStep:
    key: str
    title: str
    detail: str
    notes: tuple[str, ...] = ()
    commands: tuple[Command, ...] = ()


@dataclass(frozen=True)
class SetupWorkflowPlan:
    mode: str
    host: str | None
    steps: tuple[SetupStep, ...]
    warnings: tuple[str, ...]
    model_plan: ModelPlan
    requires_confirmation: bool
    summary: str


@dataclass(frozen=True)
class ProductionInstallerStep:
    key: str
    title: str
    detail: str
    status: str = "pending"
    recovery: str | None = None
    debug_detail: str | None = None
    setup_step_key: str | None = None


@dataclass(frozen=True)
class ProductionInstallerPlan:
    mode: str
    host: str | None
    model_plan: ModelPlan
    steps: tuple[ProductionInstallerStep, ...]
    warnings: tuple[str, ...]
    requires_confirmation: bool
    setup_plan: SetupWorkflowPlan
    summary: str

    @property
    def failed(self) -> bool:
        return any(step.status == "failure" for step in self.steps)


def plan_setup_workflow(
    mode: str = "usb",
    host: str | None = None,
    ram_gb: float | None = None,
    profile: str | None = None,
    configure_continue: bool = True,
    create_usb_tunnel: bool | None = None,
    push_scripts: bool = False,
    generated_termux_dir: Path = DEFAULT_SCRIPT_DIR,
    remote_termux_home: str = "/data/data/com.termux/files/home",
    serial: str | None = None,
) -> SetupWorkflowPlan:
    normalized_mode = _normalize_mode(mode)
    normalized_host = _normalize_host(host)
    selected_model_plan = _select_model_plan(ram_gb=ram_gb, profile=profile)
    include_tunnel = _include_tunnel(normalized_mode, create_usb_tunnel)
    warnings = tuple(exposure_warnings(normalized_mode))
    requires_confirmation = normalized_mode in {"lan", "tailscale"}

    termux_bundle = generate_termux_scripts(
        selected_model_plan.chat_model,
        selected_model_plan.autocomplete_model,
        mode=normalized_mode,
        script_dir=generated_termux_dir,
    )

    steps: list[SetupStep] = [
        SetupStep(
            key="select-models",
            title="Select model profile",
            detail=(
                f"Use the {selected_model_plan.profile} profile "
                f"({selected_model_plan.chat_model} chat, "
                f"{selected_model_plan.autocomplete_model} autocomplete)."
            ),
            notes=(f"Profile status: {selected_model_plan.status}.",),
        ),
        SetupStep(
            key="generate-termux-scripts",
            title="Plan Termux scripts",
            detail=(
                f"Generate {len(termux_bundle.files)} inspectable Termux files for "
                f"{normalized_mode} mode with OLLAMA_HOST={termux_bundle.ollama_host}."
            ),
            notes=(
                "This is a planning step only; no script files are written.",
                "Generated scripts include bootstrap, start, model install, widget, and Android optimization guidance.",
            ),
        ),
    ]

    if configure_continue:
        api_base = api_base_for_mode(normalized_mode, normalized_host)
        steps.append(
            SetupStep(
                key="configure-continue",
                title="Configure Continue",
                detail=f"Plan Continue config.yaml for API base {api_base}.",
                notes=(
                    "This step writes user Continue config when executed.",
                    "Existing config.yaml should be backed up before replacement.",
                ),
            )
        )

    if include_tunnel:
        steps.append(
            SetupStep(
                key="create-usb-tunnel",
                title="Create USB tunnel",
                detail="Plan adb reverse from host localhost:11434 to phone tcp:11434.",
                commands=(("adb", "reverse", "tcp:11434", "tcp:11434"),),
                notes=("USB tunnel keeps Ollama reachable on localhost without network exposure.",),
            )
        )

    if push_scripts:
        delivery_plan = build_script_delivery_plan(generated_termux_dir, remote_termux_home, serial)
        steps.append(
            SetupStep(
                key="push-scripts",
                title="Push Termux scripts",
                detail=f"Plan {len(delivery_plan.commands)} adb commands to deliver generated Termux files.",
                commands=delivery_plan.commands,
                notes=(
                    "Scripts are inspectable before delivery.",
                    "Delivery uses adb push plus chmod for executable scripts.",
                    *delivery_plan.instructions,
                ),
            )
        )

    return SetupWorkflowPlan(
        mode=normalized_mode,
        host=normalized_host,
        steps=tuple(steps),
        warnings=warnings,
        model_plan=selected_model_plan,
        requires_confirmation=requires_confirmation,
        summary=_summary(
            normalized_mode,
            normalized_host,
            selected_model_plan,
            configure_continue,
            include_tunnel,
            push_scripts,
            requires_confirmation,
        ),
    )


def plan_production_installer(
    mode: str = "usb",
    host: str | None = None,
    ram_gb: float | None = None,
    profile: str | None = None,
    configure_continue: bool = True,
    create_usb_tunnel: bool | None = None,
    push_scripts: bool = True,
    generated_termux_dir: Path = DEFAULT_SCRIPT_DIR,
    remote_termux_home: str = "/data/data/com.termux/files/home",
    serial: str | None = None,
    allow_advanced_exposure: bool = False,
) -> ProductionInstallerPlan:
    """Build the stable production installer state machine.

    The production plan is intentionally pure: it describes the steps that the
    CLI, packaged executable, and future UI should execute while reusing the
    existing setup workflow for model, script, Continue, tunnel, and push
    planning.
    """

    normalized_mode = _normalize_mode(mode)
    _ensure_production_exposure_allowed(normalized_mode, allow_advanced_exposure)
    setup_plan = plan_setup_workflow(
        mode=normalized_mode,
        host=host,
        ram_gb=ram_gb,
        profile=profile,
        configure_continue=configure_continue,
        create_usb_tunnel=create_usb_tunnel,
        push_scripts=push_scripts,
        generated_termux_dir=generated_termux_dir,
        remote_termux_home=remote_termux_home,
        serial=serial,
    )
    setup_steps = {step.key: step for step in setup_plan.steps}
    steps = (
        ProductionInstallerStep(
            key="host-checks",
            title="Host checks",
            detail="Verify Windows prerequisites, bundled ADB availability, and supported IDE discovery.",
            recovery="Install the packaged Pro AI Server build or run doctor for host diagnostics.",
        ),
        ProductionInstallerStep(
            key="android-phone-detection",
            title="Android phone detection",
            detail="Detect exactly one authorized Android phone over USB, or use the requested serial.",
            recovery="Connect the phone by USB, enable USB debugging, and approve the Android prompt.",
        ),
        ProductionInstallerStep(
            key="adb-verification",
            title="ADB verification",
            detail="Confirm ADB can run shell commands against the selected phone.",
            recovery="Reconnect the phone, restart ADB, or install bundled platform-tools.",
        ),
        ProductionInstallerStep(
            key="hardware-scan",
            title="Hardware scan",
            detail="Read Android version, ABI, RAM, storage, battery, and device model over ADB.",
            recovery="Keep the phone unlocked and rerun scan after ADB authorization succeeds.",
        ),
        ProductionInstallerStep(
            key="model-profile-selection",
            title="Model profile selection",
            detail=(
                f"Use the {setup_plan.model_plan.profile} profile "
                f"({setup_plan.model_plan.chat_model} chat, "
                f"{setup_plan.model_plan.autocomplete_model} autocomplete)."
            ),
            setup_step_key="select-models",
        ),
        ProductionInstallerStep(
            key="termux-readiness",
            title="Termux readiness",
            detail="Verify Termux, Termux:API, and initialized Termux home on the phone.",
            recovery="Install Termux and Termux:API from the same trusted source, then open Termux once.",
        ),
        ProductionInstallerStep(
            key="script-generation",
            title="Script generation",
            detail=setup_steps["generate-termux-scripts"].detail,
            setup_step_key="generate-termux-scripts",
        ),
        ProductionInstallerStep(
            key="script-push",
            title="Script push",
            detail=_production_script_push_detail(setup_steps),
            recovery="Rerun with the phone connected and enough Termux storage available.",
            setup_step_key="push-scripts",
        ),
        ProductionInstallerStep(
            key="server-start",
            title="Server start",
            detail="Guide the operator to run bootstrap, install models, and start Pro AI Server inside Termux.",
            recovery="Open Termux and run the generated commands shown in the setup receipt.",
        ),
        ProductionInstallerStep(
            key="usb-tunnel",
            title="USB tunnel",
            detail=_production_tunnel_detail(setup_steps),
            recovery="Keep the phone connected by USB and rerun the tunnel step.",
            setup_step_key="create-usb-tunnel",
        ),
        ProductionInstallerStep(
            key="model-inventory-check",
            title="Model inventory check",
            detail="Check Ollama model inventory for the selected chat and autocomplete models.",
            recovery="Run the generated install-models.sh script inside Termux, then retry.",
        ),
        ProductionInstallerStep(
            key="test-prompt",
            title="Test prompt",
            detail="Placeholder for TKT-P20-003: send a small prompt through the local Ollama endpoint.",
            recovery="Verify the server is running, the USB tunnel is active, and the selected model is installed.",
        ),
        ProductionInstallerStep(
            key="final-receipt",
            title="Final receipt",
            detail="Render setup artifacts, selected device, mode, model profile, tunnel state, and next steps.",
            setup_step_key="setup-receipt",
        ),
    )
    return ProductionInstallerPlan(
        mode=setup_plan.mode,
        host=setup_plan.host,
        model_plan=setup_plan.model_plan,
        steps=steps,
        warnings=setup_plan.warnings,
        requires_confirmation=setup_plan.requires_confirmation,
        setup_plan=setup_plan,
        summary=(
            "Production installer state machine for "
            f"{setup_plan.mode} setup with {setup_plan.model_plan.profile} profile "
            f"and {len(steps)} stable steps."
        ),
    )


def mark_production_step_failed(
    plan: ProductionInstallerPlan,
    key: str,
    *,
    message: str,
    debug_detail: str,
    recovery: str | None = None,
) -> ProductionInstallerPlan:
    """Return a copy of a production plan with one step marked as failed."""

    updated_steps = []
    found = False
    for step in plan.steps:
        if step.key != key:
            updated_steps.append(step)
            continue
        found = True
        updated_steps.append(
            ProductionInstallerStep(
                key=step.key,
                title=step.title,
                detail=message,
                status="failure",
                recovery=recovery or step.recovery,
                debug_detail=debug_detail,
                setup_step_key=step.setup_step_key,
            )
        )
    if not found:
        raise ValueError(f"Unknown production installer step '{key}'.")
    return ProductionInstallerPlan(
        mode=plan.mode,
        host=plan.host,
        model_plan=plan.model_plan,
        steps=tuple(updated_steps),
        warnings=plan.warnings,
        requires_confirmation=plan.requires_confirmation,
        setup_plan=plan.setup_plan,
        summary=plan.summary,
    )


def _normalize_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in VALID_SETUP_MODES:
        modes = ", ".join(sorted(VALID_SETUP_MODES))
        raise ValueError(f"Unknown setup mode '{mode}'. Expected one of: {modes}.")
    return normalized


def _ensure_production_exposure_allowed(mode: str, allow_advanced_exposure: bool) -> None:
    if mode in ADVANCED_EXPOSURE_MODES and not allow_advanced_exposure:
        raise ValueError(
            "Production installer defaults to USB mode. "
            f"{mode} mode is an advanced exposure mode; re-run with --advanced-exposure after confirming this is intended."
        )


def _normalize_host(host: str | None) -> str | None:
    normalized = (host or "").strip()
    return normalized or None


def _select_model_plan(ram_gb: float | None, profile: str | None) -> ModelPlan:
    if profile:
        return model_plan_for_profile(profile)
    if ram_gb is not None:
        return model_plan_for_ram(ram_gb)
    return model_plan_for_profile("professional")


def _include_tunnel(mode: str, requested: bool | None) -> bool:
    if requested is not None:
        return requested
    return mode == "usb"


def _summary(
    mode: str,
    host: str | None,
    model_plan: ModelPlan,
    configure_continue: bool,
    include_tunnel: bool,
    push_scripts: bool,
    requires_confirmation: bool,
) -> str:
    target = mode if host is None else f"{mode} via {host}"
    options = [
        "Continue config" if configure_continue else "no Continue config",
        "USB tunnel" if include_tunnel else "no USB tunnel",
        "adb script push" if push_scripts else "no adb script push",
    ]
    confirmation = "requires explicit confirmation" if requires_confirmation else "does not require exposure confirmation"
    return f"Plan {target} setup with {model_plan.profile} profile, {', '.join(options)}; {confirmation}."


def _production_script_push_detail(setup_steps: dict[str, SetupStep]) -> str:
    step = setup_steps.get("push-scripts")
    if step is None:
        return "Skip script push in this plan; scripts can be pushed later with push-scripts."
    return step.detail


def _production_tunnel_detail(setup_steps: dict[str, SetupStep]) -> str:
    step = setup_steps.get("create-usb-tunnel")
    if step is None:
        return "Skip USB tunnel in this plan because the selected mode does not require it."
    return step.detail
