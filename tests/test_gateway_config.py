from pathlib import Path

from pro_ai_server.gateway.config import (
    default_project_config_path,
    default_user_config_path,
    load_gateway_config,
)


def test_default_config_paths():
    assert default_project_config_path(Path("repo")) == Path("repo") / ".pro-ai-server" / "config.yaml"
    assert default_user_config_path(Path("home")) == Path("home") / ".pro-ai-server" / "config.yaml"


def test_load_gateway_config_reads_project_yaml(tmp_path):
    config = tmp_path / ".pro-ai-server" / "config.yaml"
    config.parent.mkdir()
    config.write_text(
        """
gateway:
  host: "127.0.0.2"
  port: 9000
  chat_model: "custom-chat:latest"
routing:
  routes:
    refactor:
      profile: "deep"
      model: "custom-refactor:latest"
      fallback_model: "custom-chat:latest"
""",
        encoding="utf-8",
    )

    loaded = load_gateway_config(project_root=tmp_path, home=tmp_path / "home")

    assert loaded.settings.host == "127.0.0.2"
    assert loaded.settings.port == 9000
    assert loaded.settings.chat_model == "custom-chat:latest"
    assert loaded.settings.route_overrides["refactor"]["model"] == "custom-refactor:latest"


def test_project_config_overrides_user_config(tmp_path):
    home = tmp_path / "home"
    user_config = home / ".pro-ai-server" / "config.yaml"
    project_config = tmp_path / ".pro-ai-server" / "config.yaml"
    user_config.parent.mkdir(parents=True)
    project_config.parent.mkdir(parents=True)
    user_config.write_text("gateway:\n  host: 127.0.0.2\n  port: 9000\n", encoding="utf-8")
    project_config.write_text("gateway:\n  port: 9001\n", encoding="utf-8")

    loaded = load_gateway_config(project_root=tmp_path, home=home)

    assert loaded.settings.host == "127.0.0.2"
    assert loaded.settings.port == 9001

