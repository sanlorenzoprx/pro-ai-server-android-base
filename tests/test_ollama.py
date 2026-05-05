from pro_ai_server.models import ModelPlan, model_plan_for_profile
from pro_ai_server.ollama import (
    DEFAULT_TEST_PROMPT,
    assess_model_inventory,
    assess_ollama_server_status,
    assess_ollama_test_prompt_response,
    build_ollama_generate_command,
    build_ollama_tags_command,
    build_ollama_tags_commands,
    parse_ollama_tags_model_names,
)


def test_responding_server_with_models():
    tags = (
        '{"models":['
        '{"name":"qwen2.5-coder:3b"},'
        '{"name":"qwen2.5-coder:1.5b-base"}'
        "]}"
    )

    server = assess_ollama_server_status(tags)
    inventory = assess_model_inventory(model_plan_for_profile("professional"), tags)

    assert server.ok is True
    assert server.model_names == ("qwen2.5-coder:3b", "qwen2.5-coder:1.5b-base")
    assert inventory.ok is True
    assert inventory.missing_models == ()
    assert inventory.warnings == ()
    assert inventory.instructions == ()


def test_empty_inventory_is_parsed_and_reports_required_models_missing():
    inventory = assess_model_inventory(model_plan_for_profile("lightweight"), '{"models":[]}')

    assert inventory.ok is False
    assert inventory.model_names == ()
    assert inventory.missing_models == ("qwen2.5-coder:1.5b", "qwen2.5-coder:0.5b")
    assert "missing required model" in inventory.warnings[0]
    assert inventory.instructions == (
        "Run in Termux: ollama pull qwen2.5-coder:1.5b",
        "Run in Termux: ollama pull qwen2.5-coder:0.5b",
    )


def test_missing_one_required_model_reports_only_missing_model():
    tags = '{"models":[{"name":"qwen2.5-coder:3b"}]}'

    inventory = assess_model_inventory(model_plan_for_profile("professional"), tags)

    assert inventory.ok is False
    assert inventory.model_names == ("qwen2.5-coder:3b",)
    assert inventory.missing_models == ("qwen2.5-coder:1.5b-base",)
    assert inventory.instructions == ("Run in Termux: ollama pull qwen2.5-coder:1.5b-base",)


def test_duplicate_required_models_are_not_reported_twice():
    plan = ModelPlan(
        profile="test",
        status="test",
        chat_model="qwen2.5-coder:1.5b",
        autocomplete_model="qwen2.5-coder:1.5b",
    )

    inventory = assess_model_inventory(plan, '{"models":[]}')

    assert inventory.missing_models == ("qwen2.5-coder:1.5b",)
    assert inventory.instructions == ("Run in Termux: ollama pull qwen2.5-coder:1.5b",)


def test_invalid_json_returns_not_ready_instruction():
    server = assess_ollama_server_status("not json")
    inventory = assess_model_inventory(model_plan_for_profile("professional"), "not json")

    assert parse_ollama_tags_model_names("not json") == ()
    assert server.ok is False
    assert "invalid JSON" in server.warnings[0]
    assert "Start Ollama in Termux" in server.instructions[0]
    assert inventory.ok is False
    assert inventory.instructions == server.instructions


def test_server_error_string_returns_not_ready_instruction():
    server = assess_ollama_server_status("ERROR: Connection refused")

    assert server.ok is False
    assert "Connection refused" in server.warnings[0]
    assert "verify the selected connection mode and tunnel" in server.instructions[0]


def test_json_error_string_returns_not_ready_instruction():
    server = assess_ollama_server_status('{"error":"model service unavailable"}')

    assert server.ok is False
    assert "model service unavailable" in server.warnings[0]
    assert "Start Ollama in Termux" in server.instructions[0]


def test_api_base_url_command_building():
    command = build_ollama_tags_command("http://phone.local:11434/")

    assert command == (
        "curl",
        "--silent",
        "--show-error",
        "http://phone.local:11434/api/tags",
    )
    assert build_ollama_tags_commands("http://phone.local:11434/") == (command,)


def test_generate_command_uses_small_non_streaming_payload():
    command = build_ollama_generate_command("qwen2.5-coder:3b", api_base_url="http://phone.local:11434/")

    assert command == (
        "curl",
        "--silent",
        "--show-error",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "-d",
        '{"model":"qwen2.5-coder:3b","prompt":"Reply with exactly: pro-ai-server-ready","stream":false}',
        "http://phone.local:11434/api/generate",
    )
    assert DEFAULT_TEST_PROMPT in command[-2]


def test_test_prompt_accepts_non_empty_generate_response():
    status = assess_ollama_test_prompt_response(
        "qwen2.5-coder:3b",
        '{"model":"qwen2.5-coder:3b","response":"pro-ai-server-ready","done":true}',
    )

    assert status.ok is True
    assert status.model == "qwen2.5-coder:3b"
    assert status.response == "pro-ai-server-ready"
    assert status.warnings == ()


def test_test_prompt_reports_connection_failure():
    status = assess_ollama_test_prompt_response("qwen2.5-coder:3b", "Failed to connect to localhost")

    assert status.ok is False
    assert "Failed to connect" in status.warnings[0]
    assert "Start Ollama in Termux" in status.instructions[0]


def test_test_prompt_reports_invalid_json():
    status = assess_ollama_test_prompt_response("qwen2.5-coder:3b", "not json")

    assert status.ok is False
    assert "invalid JSON" in status.warnings[0]


def test_test_prompt_reports_missing_model_with_pull_instruction():
    status = assess_ollama_test_prompt_response(
        "qwen2.5-coder:3b",
        '{"error":"model qwen2.5-coder:3b not found, try pulling it first"}',
    )

    assert status.ok is False
    assert "could not run model qwen2.5-coder:3b" in status.warnings[0]
    assert status.instructions == ("Run in Termux: ollama pull qwen2.5-coder:3b",)


def test_test_prompt_reports_empty_generated_text():
    status = assess_ollama_test_prompt_response("qwen2.5-coder:3b", '{"response":"   "}')

    assert status.ok is False
    assert "generated text" in status.warnings[0]
