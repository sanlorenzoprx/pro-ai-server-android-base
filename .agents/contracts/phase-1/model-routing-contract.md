# Contract: Model Routing

## Phase

Phase 1: Gateway Skeleton

## Purpose

Define deterministic task-to-model selection before gateway proxy behavior is added.

Routes should use configurable model choices. The table below defines initial defaults only; implementation must not bury these LLM names in endpoint code.

## Routes

| Task | Profile | Preferred Model | Fallback Model |
|---|---|---|---|
| autocomplete | fast | `qwen2.5-coder:0.5b` | `qwen2.5-coder:1.5b-base` |
| chat | balanced | `qwen2.5-coder:3b` | `qwen2.5-coder:1.5b` |
| refactor | deep | `qwen2.5-coder:7b` | `qwen2.5-coder:3b` |
| test_generation | balanced | `qwen2.5-coder:3b` | `qwen2.5-coder:1.5b` |
| documentation | fast | `qwen2.5-coder:1.5b` | `qwen2.5-coder:0.5b` |

## Fallback

Unknown tasks select the `chat` route.

## Configuration Rule

- Existing profile defaults come from `src/pro_ai_server/models.py`.
- Gateway settings may override chat and autocomplete models.
- Future route settings may override any task route without changing endpoint code.
- Tests should prove custom model values can flow through settings.

## Validation

- Unit tests cover every route.
- Unit tests cover unknown task fallback.
- Route-test endpoint and CLI must use the same routing module.
