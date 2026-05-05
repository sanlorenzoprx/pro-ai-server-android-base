from datetime import datetime

import yaml

from pro_ai_server.continue_config import (
    api_base_for_mode,
    devstack_restore_instructions,
    exposure_warnings,
    render_devstack_continue_config_yaml,
    render_continue_config_yaml,
    write_continue_config,
)
from pro_ai_server.models import model_plan_for_profile


def test_render_continue_config_yaml_uses_pyyaml_shape():
    plan = model_plan_for_profile("professional")

    rendered = render_continue_config_yaml(plan)
    parsed = yaml.safe_load(rendered)

    assert parsed["name"] == "Pro AI Server Local"
    assert parsed["schema"] == "v1"
    assert parsed["models"][0]["name"] == "Pro AI Chat"
    assert parsed["models"][0]["model"] == "qwen2.5-coder:3b"
    assert parsed["models"][0]["apiBase"] == "http://localhost:11434"
    assert parsed["models"][0]["roles"] == ["chat", "edit", "apply"]
    assert parsed["models"][1]["name"] == "Pro AI Autocomplete"
    assert parsed["models"][1]["model"] == "qwen2.5-coder:1.5b-base"
    assert parsed["models"][1]["roles"] == ["autocomplete"]
    assert rendered.startswith("name: Pro AI Server Local\n")


def test_write_continue_config_creates_directory(tmp_path):
    continue_dir = tmp_path / ".continue"
    plan = model_plan_for_profile("lightweight")

    result = write_continue_config(plan, continue_dir=continue_dir)

    assert result.config_path == continue_dir / "config.yaml"
    assert result.backup_path is None
    assert result.config_path.exists()
    assert continue_dir.exists()


def test_write_continue_config_backs_up_existing_config(tmp_path):
    continue_dir = tmp_path / ".continue"
    continue_dir.mkdir()
    config_path = continue_dir / "config.yaml"
    config_path.write_text("existing: true\n", encoding="utf-8")
    plan = model_plan_for_profile("professional")
    now = datetime(2026, 5, 2, 13, 14, 15)

    result = write_continue_config(plan, continue_dir=continue_dir, now=now)

    assert result.backup_path == continue_dir / "config.yaml.pro-ai-server-backup-20260502-131415"
    assert result.backup_path.read_text(encoding="utf-8") == "existing: true\n"
    assert "qwen2.5-coder:3b" in config_path.read_text(encoding="utf-8")


def test_api_base_for_usb_defaults_to_localhost():
    assert api_base_for_mode("usb") == "http://localhost:11434"


def test_continue_config_usb_uses_localhost_for_all_model_roles():
    plan = model_plan_for_profile("professional")

    parsed = yaml.safe_load(render_continue_config_yaml(plan, mode="usb"))

    assert {model["apiBase"] for model in parsed["models"]} == {"http://localhost:11434"}


def test_devstack_continue_config_adds_launch_metadata_and_uses_profile_models():
    plan = model_plan_for_profile("lightweight")

    parsed = yaml.safe_load(render_devstack_continue_config_yaml(plan))

    assert parsed["name"] == "Pro Agentic Coding Server"
    assert parsed["metadata"]["product"] == "DevStack"
    assert parsed["metadata"]["launch_ides"] == ["VS Code", "Cursor"]
    assert parsed["metadata"]["connection_mode"] == "usb"
    assert parsed["metadata"]["api_base"] == "http://localhost:11434"
    assert parsed["metadata"]["chat_model"] == plan.chat_model
    assert parsed["metadata"]["autocomplete_model"] == plan.autocomplete_model
    assert parsed["models"][0]["model"] == plan.chat_model
    assert parsed["models"][1]["model"] == plan.autocomplete_model


def test_write_devstack_continue_config_uses_backup_and_restore_instructions(tmp_path):
    continue_dir = tmp_path / ".continue"
    continue_dir.mkdir()
    config_path = continue_dir / "config.yaml"
    config_path.write_text("existing: true\n", encoding="utf-8")
    now = datetime(2026, 5, 2, 13, 14, 15)

    result = write_continue_config(
        model_plan_for_profile("professional"),
        continue_dir=continue_dir,
        now=now,
        devstack=True,
    )
    rendered = config_path.read_text(encoding="utf-8")

    assert result.backup_path == continue_dir / "config.yaml.pro-ai-server-backup-20260502-131415"
    assert "name: Pro Agentic Coding Server" in rendered
    assert "product: DevStack" in rendered
    assert devstack_restore_instructions(result) == (
        f"Backup saved at {result.backup_path}.",
        f"To restore, copy {result.backup_path} back to {result.config_path}.",
    )


def test_lan_warning_is_pure_helper():
    assert exposure_warnings("lan") == ["LAN mode exposes Ollama to devices on the local network."]
    assert exposure_warnings("usb") == []
