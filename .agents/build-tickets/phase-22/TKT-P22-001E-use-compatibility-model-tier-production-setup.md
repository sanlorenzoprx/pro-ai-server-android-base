# TKT-P22-001E: Use Compatibility Model Tier in Production Setup

## Target Repo

Pro AI Server

## Target Area

Production setup model selection

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/android-compatibility-contract.md`

## User / Operator Served

Customers and release operators relying on the production installer promise.

## Pain Solved

The raw hardware scanner can recommend a more aggressive model profile than the production compatibility gate. Production setup should use the safer compatibility model tier by default.

## Definition of Done

- `setup --production` uses the compatibility model tier when no explicit `--profile` or `--ram-gb` override is provided.
- Explicit operator overrides still work.
- Output shows production compatibility tier and production model profile.
- Yellow devices default to lightweight.
- Unsupported red devices block production setup.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `tests/test_cli_workflows.py`
- `.agents/reports/TKT-P22-001E-report.md`

## Validation

- `pytest tests/test_cli_workflows.py tests/test_android_compatibility.py tests/test_termux_readiness.py`
- `ruff check .`
- `pro-ai-server validate-release`
- `pytest`

## Dependencies

- TKT-P22-001D

## Follow-Up Tickets Unlocked

- TKT-P22-002
