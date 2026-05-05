# TKT-P22-001B: Automated F-Droid and Termux Bootstrap Install Path

## Target Repo

Pro AI Server

## Target Area

Production Android bootstrap automation

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/fdroid-termux-bootstrap-contract.md`

## User / Operator Served

Customers and release operators expecting the plug-in-phone production promise.

## Pain Solved

The production path should not depend on the user manually discovering F-Droid, unknown-app permissions, Termux, or Termux:API.

## Definition of Done

- CLI includes F-Droid in the Termux app bootstrap flow.
- CLI can install F-Droid from a local APK with `--fdroid-apk --yes`.
- CLI opens F-Droid unknown-app permission when F-Droid is installed.
- CLI can install Termux and Termux:API from local APKs with `--yes`.
- CLI opens Termux and Termux:API F-Droid pages when local APKs are not provided.
- Docs and RC evidence describe the complete F-Droid -> permission -> Termux -> Termux:API path.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `tests/test_cli_workflows.py`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-001B-report.md`

## Validation

- `pytest tests/test_cli_workflows.py tests/test_docs.py`
- `ruff check .`
- `pro-ai-server validate-release`
- Hardware: `pro-ai-server install-termux-apps --serial <device-serial>`

## Dependencies

- TKT-P22-001

## Follow-Up Tickets Unlocked

- TKT-P22-002
