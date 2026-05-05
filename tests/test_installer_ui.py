from pro_ai_server.installer_ui import build_installer_ui_flow, render_installer_ui_flow
from pro_ai_server.setup_receipt import build_setup_receipt
from pro_ai_server.setup_workflow import mark_production_step_failed, plan_production_installer


def screen_keys(flow):
    return tuple(screen.key for screen in flow.screens)


def test_installer_ui_flow_has_required_customer_screens_without_advanced_modes():
    plan = plan_production_installer()

    flow = build_installer_ui_flow(plan)

    assert flow.mode == "usb"
    assert flow.advanced_modes_visible is False
    assert screen_keys(flow) == (
        "welcome",
        "device-detection",
        "hardware-scan",
        "install-progress",
        "test-prompt",
        "ide-configuration",
        "success-receipt",
    )
    assert flow.screens[0].title == "Welcome and USB debugging checklist"
    assert "android-phone-detection" in flow.screens[1].step_keys
    assert "model-profile-selection" in flow.screens[2].step_keys
    assert "test-prompt" in flow.screens[4].step_keys


def test_installer_ui_success_screen_can_render_receipt():
    plan = plan_production_installer()
    receipt = build_setup_receipt(workflow_plan=plan.setup_plan, production_plan=plan)

    flow = build_installer_ui_flow(plan, receipt=receipt)
    rendered = render_installer_ui_flow(flow)

    assert "## Success receipt" in rendered
    assert "Pro AI Server setup receipt" in rendered
    assert "Advanced network modes visible: no" in rendered


def test_installer_ui_flow_can_show_mocked_recoverable_error():
    plan = mark_production_step_failed(
        plan_production_installer(),
        "termux-readiness",
        message="Termux is not ready.",
        debug_detail="pm path com.termux.api returned package not found",
    )

    flow = build_installer_ui_flow(plan)
    rendered = render_installer_ui_flow(flow)

    assert flow.failed is True
    assert screen_keys(flow)[-1] == "recoverable-error"
    assert "Termux is not ready." in rendered
    assert "Install Termux and Termux:API" in rendered
    assert "pm path com.termux.api returned package not found" in rendered

