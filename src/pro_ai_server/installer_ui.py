from __future__ import annotations

from dataclasses import dataclass

from pro_ai_server.setup_receipt import SetupReceipt, render_setup_receipt
from pro_ai_server.setup_workflow import ProductionInstallerPlan, ProductionInstallerStep


@dataclass(frozen=True)
class InstallerUIScreen:
    key: str
    title: str
    current_step_key: str | None
    step_keys: tuple[str, ...]
    body: tuple[str, ...]
    recovery: tuple[str, ...] = ()
    debug_details: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstallerUIFlow:
    mode: str
    screens: tuple[InstallerUIScreen, ...]
    advanced_modes_visible: bool = False

    @property
    def failed(self) -> bool:
        return any(screen.key == "recoverable-error" for screen in self.screens)


SCREEN_STEP_MAP: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "welcome",
        "Welcome and USB debugging checklist",
        ("host-checks",),
    ),
    (
        "device-detection",
        "Device detection",
        ("android-phone-detection", "adb-verification"),
    ),
    (
        "hardware-scan",
        "Hardware scan and model recommendation",
        ("hardware-scan", "model-profile-selection"),
    ),
    (
        "install-progress",
        "Install progress",
        ("termux-readiness", "script-generation", "script-push", "server-start", "usb-tunnel", "model-inventory-check"),
    ),
    (
        "test-prompt",
        "Test prompt result",
        ("test-prompt",),
    ),
    (
        "ide-configuration",
        "IDE configuration prompt",
        ("final-receipt",),
    ),
)


def build_installer_ui_flow(
    plan: ProductionInstallerPlan,
    *,
    receipt: SetupReceipt | None = None,
) -> InstallerUIFlow:
    steps_by_key = {step.key: step for step in plan.steps}
    screens = [_screen_from_steps(key, title, step_keys, steps_by_key) for key, title, step_keys in SCREEN_STEP_MAP]

    failed_steps = tuple(step for step in plan.steps if step.status == "failure")
    if failed_steps:
        screens.append(_recoverable_error_screen(failed_steps))
    else:
        screens.append(_success_receipt_screen(receipt))

    return InstallerUIFlow(
        mode=plan.mode,
        screens=tuple(screens),
        advanced_modes_visible=False,
    )


def render_installer_ui_flow(flow: InstallerUIFlow) -> str:
    lines = ["Pro AI Server Installer", f"Mode: {flow.mode}", f"Advanced network modes visible: {_yes_no(flow.advanced_modes_visible)}"]
    for screen in flow.screens:
        lines.extend(["", f"## {screen.title}", f"Screen: {screen.key}"])
        if screen.current_step_key:
            lines.append(f"Current step: {screen.current_step_key}")
        if screen.step_keys:
            lines.append("Steps: " + ", ".join(screen.step_keys))
        lines.extend(screen.body)
        for recovery in screen.recovery:
            lines.append(f"Recovery: {recovery}")
        for detail in screen.debug_details:
            lines.append(f"Debug: {detail}")
    return "\n".join(lines) + "\n"


def _screen_from_steps(
    key: str,
    title: str,
    step_keys: tuple[str, ...],
    steps_by_key: dict[str, ProductionInstallerStep],
) -> InstallerUIScreen:
    steps = tuple(steps_by_key[step_key] for step_key in step_keys)
    current = next((step for step in steps if step.status != "success"), steps[-1])
    body = tuple(f"- {step.status}: {step.title} - {step.detail}" for step in steps)
    recovery = tuple(step.recovery for step in steps if step.status == "failure" and step.recovery)
    debug_details = tuple(step.debug_detail for step in steps if step.status == "failure" and step.debug_detail)
    return InstallerUIScreen(
        key=key,
        title=title,
        current_step_key=current.key,
        step_keys=step_keys,
        body=body,
        recovery=recovery,
        debug_details=debug_details,
    )


def _recoverable_error_screen(failed_steps: tuple[ProductionInstallerStep, ...]) -> InstallerUIScreen:
    return InstallerUIScreen(
        key="recoverable-error",
        title="Recoverable error",
        current_step_key=failed_steps[0].key,
        step_keys=tuple(step.key for step in failed_steps),
        body=tuple(f"- {step.title}: {step.detail}" for step in failed_steps),
        recovery=tuple(step.recovery for step in failed_steps if step.recovery),
        debug_details=tuple(step.debug_detail for step in failed_steps if step.debug_detail),
    )


def _success_receipt_screen(receipt: SetupReceipt | None) -> InstallerUIScreen:
    if receipt is None:
        body = ("- Setup receipt will appear here after installation actions run.",)
    else:
        body = tuple(render_setup_receipt(receipt).splitlines())
    return InstallerUIScreen(
        key="success-receipt",
        title="Success receipt",
        current_step_key="final-receipt",
        step_keys=("final-receipt",),
        body=body,
    )


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"

