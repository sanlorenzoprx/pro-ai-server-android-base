# TKT-P23-001: Native Runtime Wrapper Config and Contract Scaffold

## Target Repo

Pro AI Server Android Base

## Target Area

`src/pro_ai_server/native_runtime.py` and native runtime contract docs

## Phase

Phase 23: Native Runtime Transition

## Source Docs

- `docs/PHONE_RUNTIME_TRANSITION.md`
- `docs/NATIVE_RUNTIME_RESEARCH_NOTE.md`
- `docs/LLAMA_CPP_WRAPPER_CONTRACT.md`
- `.agents/contracts/phase-23/native-runtime-wrapper-contract.md`
- `.agents/workflows/codeflow-build-bridge.md`

## User / Operator Served

Developers evolving the phone runtime without breaking the working Windows host control plane.

## Pain Solved

The project needs a concrete native-runtime boundary before deeper `llama.cpp` implementation starts. Without this scaffold, raw engine details would leak into the host, gateway, and product logic too early.

## Definition of Done

- Native runtime module exists with typed config and model identity structures.
- Wrapper config validates the required runtime settings.
- Profile defaults resolve `lightweight`, `professional`, and `max` into concrete GGUF-backed runtime configuration.
- Wrapper response builders preserve the current host-facing contract shapes.
- Docs describe the wrapper contract and connect it to the transition plan.
- Focused tests cover config validation, profile resolution, and response-shape stability.

## Expected Files to Change

- `src/pro_ai_server/native_runtime.py`
- `tests/test_native_runtime.py`
- `docs/LLAMA_CPP_WRAPPER_CONTRACT.md`
- `docs/PHONE_RUNTIME_TRANSITION.md`
- `docs/NEXT_MILESTONES.md`

## Contract Impact

- Endpoint: preserves local runtime response shapes
- Config: adds native runtime config model and defaults
- Schema: adds stable wrapper payload shapes
- CLI: none yet
- Network/security: preserves local USB-first host contract

## Validation

- `pytest tests/test_native_runtime.py tests/test_model_plan.py tests/test_docs.py`
- `ruff check src/pro_ai_server/native_runtime.py tests/test_native_runtime.py`

## Rollback Plan

Remove the native runtime scaffold module and restore the wrapper docs if the contract proves incompatible with the host-side assumptions.

## Dependencies

- `docs/PHONE_RUNTIME_TRANSITION.md`
- `docs/NATIVE_RUNTIME_RESEARCH_NOTE.md`
- `docs/LLAMA_CPP_WRAPPER_CONTRACT.md`

## Follow-Up Tickets Unlocked

- native runtime config inspection CLI
- native runtime manifest file format
- first native HTTP wrapper implementation
- first `llama.cpp` startup adapter
