# Contract: Native Runtime Wrapper

## Phase

Phase 23: Native Runtime Transition

## Owner

Codex with user review

## Purpose

Stabilize the first native phone-runtime wrapper boundary so the Windows host control plane can continue to work while the phone runtime transitions away from the Termux/Debian/Ollama lane.

## In Scope

- Native runtime config model for a `llama.cpp`-backed phone runtime
- Stable model identity mapping from contract name to GGUF file path
- Stable non-streaming response shapes for:
  - `GET /api/tags`
  - `POST /api/generate`
  - `POST /api/chat`
- Validation helpers for runtime configuration
- Profile-to-runtime defaults for `lightweight`, `professional`, and `max`

## Out of Scope

- Real `llama.cpp` process startup
- HTTP server implementation for the native lane
- Streaming support
- Embeddings
- Multi-model concurrent runtime loading
- Companion app lifecycle integration

## Interface

Wrapper config must support:

- model contract name
- GGUF file path
- bind host
- bind port
- context length
- threads
- GPU layer count

Wrapper contract must preserve:

- host API base at `http://localhost:11434` in USB mode
- model inventory shape with `models[].name`
- generate response shape with `response`
- chat response shape with `message.role` and `message.content`

## Error Behavior

Wrapper config validation must reject:

- empty contract names
- non-positive ports
- non-positive context length
- non-positive thread counts
- negative GPU layer counts

Future runtime failures should map to structured wrapper error codes instead of raw engine output.

## Security / Privacy

- Runtime remains local-first and loopback-oriented in USB mode
- No cloud dependency is introduced by this wrapper layer
- Wrapper config must not require exposing the phone runtime beyond the current host contract

## Validation

- `pytest tests/test_native_runtime.py`
- `pytest tests/test_model_plan.py`
- `pytest tests/test_docs.py`

## Change Control

Changes to the wrapper contract should be reviewed against:

- `docs/PHONE_RUNTIME_TRANSITION.md`
- `docs/LLAMA_CPP_WRAPPER_CONTRACT.md`
- `docs/NATIVE_RUNTIME_RESEARCH_NOTE.md`

If changes alter the host contract or runtime direction materially, pause for explicit user go/no-go.
