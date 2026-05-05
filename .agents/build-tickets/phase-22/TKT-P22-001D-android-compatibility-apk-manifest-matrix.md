# TKT-P22-001D: Android Compatibility and APK Manifest Matrix

## Target Repo

Pro AI Server

## Target Area

Android compatibility, APK manifest policy, and production install preflight

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/android-compatibility-contract.md`

## User / Operator Served

Customers and release operators validating which old and new Android phones can be supported.

## Pain Solved

The product needs a wide device net without overpromising unsupported Android versions, 32-bit phones, or low-RAM local LLM performance.

## Definition of Done

- Compatibility matrix defines green, yellow, and red Android device classes.
- APK manifest schema documents F-Droid, Termux, and Termux:API pinning fields.
- CLI compatibility command reports tier, model tier, warnings, blockers, and Termux installer source.
- Play Store Termux conflict is detected as a blocker.
- Mixed Termux and Termux:API installer sources are warned.
- Docs explain Android 7+ and arm64 support boundaries.

## Expected Files to Change

- `src/pro_ai_server/android_compatibility.py`
- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/termux_readiness.py`
- `tests/test_android_compatibility.py`
- `tests/test_cli_workflows.py`
- `tests/test_termux_readiness.py`
- `docs/ANDROID_COMPATIBILITY.md`
- `docs/CLI_WORKFLOW.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001D-report.md`

## Validation

- `pytest tests/test_android_compatibility.py tests/test_cli_workflows.py tests/test_termux_readiness.py tests/test_docs.py`
- `ruff check .`
- `pro-ai-server validate-release`
- Hardware: `pro-ai-server android-compatibility --serial <device-serial>`

## Dependencies

- TKT-P22-001B

## Follow-Up Tickets Unlocked

- Official pinned APK manifest values
- TKT-P22-002
