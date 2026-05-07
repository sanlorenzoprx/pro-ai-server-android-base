from pathlib import Path

import pytest

from pro_ai_server.native_runtime import (
    DEFAULT_NATIVE_RUNTIME_HOST,
    DEFAULT_NATIVE_RUNTIME_PORT,
    NativeRuntimeConfig,
    NativeRuntimeError,
    NativeRuntimeManifest,
    NativeRuntimeModel,
    NativeRuntimeProfileDefaults,
    build_native_runtime_config_for_model_plan,
    build_native_runtime_model,
    build_native_runtime_chat_response,
    build_native_runtime_generate_response,
    build_native_runtime_health_response,
    build_native_runtime_tags_response,
    load_native_runtime_manifest,
    native_runtime_defaults_for_profile,
    validate_native_runtime_config,
)
from pro_ai_server.models import model_plan_for_profile


def make_model() -> NativeRuntimeModel:
    return NativeRuntimeModel(
        contract_name="qwen2.5-coder:1.5b",
        gguf_path=Path("models") / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
    )


def test_native_runtime_model_inventory_entry_uses_contract_name():
    model = make_model()

    assert model.to_inventory_entry() == {"name": "qwen2.5-coder:1.5b"}


def test_native_runtime_config_defaults_match_host_contract_shape():
    config = NativeRuntimeConfig(model=make_model())

    assert config.host == DEFAULT_NATIVE_RUNTIME_HOST
    assert config.port == DEFAULT_NATIVE_RUNTIME_PORT
    assert config.api_base == "http://127.0.0.1:11434"


def test_validate_native_runtime_config_accepts_valid_settings():
    validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), threads=6, gpu_layers=4))


def test_validate_native_runtime_config_rejects_invalid_values():
    with pytest.raises(ValueError, match="contract name"):
        validate_native_runtime_config(
            NativeRuntimeConfig(
                model=NativeRuntimeModel(contract_name=" ", gguf_path=Path("models") / "test.gguf")
            )
        )

    with pytest.raises(ValueError, match="port"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), port=0))

    with pytest.raises(ValueError, match="context length"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), context_length=0))

    with pytest.raises(ValueError, match="threads"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), threads=0))

    with pytest.raises(ValueError, match="GPU layers"):
        validate_native_runtime_config(NativeRuntimeConfig(model=make_model(), gpu_layers=-1))


def test_native_runtime_response_builders_match_wrapper_contract_shapes():
    assert build_native_runtime_health_response() == {
        "status": "ok",
        "engine": "llama.cpp",
        "runtime": "native-wrapper",
    }
    assert build_native_runtime_tags_response(make_model()) == {
        "models": [{"name": "qwen2.5-coder:1.5b"}]
    }
    assert build_native_runtime_tags_response(None) == {"models": []}
    assert build_native_runtime_generate_response("pro-ai-server-ready") == {
        "response": "pro-ai-server-ready"
    }
    assert build_native_runtime_chat_response("hello") == {
        "message": {"role": "assistant", "content": "hello"}
    }


def test_native_runtime_error_dict_shape_is_stable():
    error = NativeRuntimeError(error="model_not_loaded", message="Requested model is not loaded.")

    assert error.to_dict() == {
        "error": "model_not_loaded",
        "message": "Requested model is not loaded.",
    }


def test_native_runtime_defaults_exist_for_known_profiles():
    lightweight = native_runtime_defaults_for_profile("lightweight")
    professional = native_runtime_defaults_for_profile("professional")
    maximum = native_runtime_defaults_for_profile("max")

    assert lightweight.chat_model_filename.endswith(".gguf")
    assert professional.context_length >= lightweight.context_length
    assert maximum.threads >= professional.threads


def test_load_native_runtime_manifest_reads_packaged_profile_defaults():
    manifest = load_native_runtime_manifest()

    assert manifest.engine == "llama.cpp"
    assert "lightweight" in manifest.profiles
    assert manifest.profiles["professional"].chat_model_filename == "qwen2.5-coder-3b-instruct-q4_k_m.gguf"


def test_load_native_runtime_manifest_reads_custom_file(tmp_path):
    manifest_path = tmp_path / "native-runtime-manifest.json"
    manifest_path.write_text(
        """{
          "engine": "test-engine",
          "policy": "test policy",
          "profiles": {
            "test": {
              "chat_model_filename": "chat.gguf",
              "autocomplete_model_filename": "autocomplete.gguf",
              "context_length": 2048,
              "threads": 2,
              "gpu_layers": 1
            }
          }
        }""",
        encoding="utf-8",
    )

    manifest = load_native_runtime_manifest(manifest_path)

    assert manifest.engine == "test-engine"
    assert manifest.policy == "test policy"
    assert manifest.profiles["test"] == NativeRuntimeProfileDefaults(
        chat_model_filename="chat.gguf",
        autocomplete_model_filename="autocomplete.gguf",
        context_length=2048,
        threads=2,
        gpu_layers=1,
    )


def test_load_native_runtime_manifest_rejects_empty_profiles(tmp_path):
    manifest_path = tmp_path / "native-runtime-manifest.json"
    manifest_path.write_text('{"profiles": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="at least one profile"):
        load_native_runtime_manifest(manifest_path)


def test_native_runtime_defaults_reject_unknown_profile():
    with pytest.raises(ValueError, match="Unknown native runtime profile"):
        native_runtime_defaults_for_profile("tiny")


def test_build_native_runtime_model_uses_models_root_and_filename():
    model = build_native_runtime_model(
        "qwen2.5-coder:3b",
        "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        models_root=Path("bundled-models"),
    )

    assert model.contract_name == "qwen2.5-coder:3b"
    assert model.gguf_path == Path("bundled-models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"


def test_build_native_runtime_config_for_model_plan_prefers_chat_model():
    plan = model_plan_for_profile("professional")

    config = build_native_runtime_config_for_model_plan(
        plan,
        models_root=Path("bundled-models"),
        prefer="chat",
    )

    assert config.model.contract_name == "qwen2.5-coder:3b"
    assert config.model.gguf_path == Path("bundled-models") / "qwen2.5-coder-3b-instruct-q4_k_m.gguf"
    assert config.context_length == 8192
    assert config.threads == 6


def test_build_native_runtime_config_for_model_plan_can_use_custom_manifest():
    manifest = NativeRuntimeManifest(
        engine="test",
        policy="test",
        profiles={
            "professional": NativeRuntimeProfileDefaults(
                chat_model_filename="custom-chat.gguf",
                autocomplete_model_filename="custom-autocomplete.gguf",
                context_length=2048,
                threads=2,
                gpu_layers=1,
            )
        },
    )

    config = build_native_runtime_config_for_model_plan(
        model_plan_for_profile("professional"),
        models_root=Path("custom-models"),
        manifest=manifest,
    )

    assert config.model.contract_name == "qwen2.5-coder:3b"
    assert config.model.gguf_path == Path("custom-models") / "custom-chat.gguf"
    assert config.context_length == 2048
    assert config.threads == 2
    assert config.gpu_layers == 1


def test_build_native_runtime_config_for_model_plan_can_prefer_autocomplete_model():
    plan = model_plan_for_profile("lightweight")

    config = build_native_runtime_config_for_model_plan(
        plan,
        models_root=Path("bundled-models"),
        prefer="autocomplete",
    )

    assert config.model.contract_name == "qwen2.5-coder:0.5b"
    assert config.model.gguf_path == Path("bundled-models") / "qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"


def test_build_native_runtime_config_for_model_plan_rejects_invalid_preference():
    with pytest.raises(ValueError, match="prefer value"):
        build_native_runtime_config_for_model_plan(model_plan_for_profile("lightweight"), prefer="summary")
