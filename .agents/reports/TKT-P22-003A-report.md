# TKT-P22-003A Implementation Report

## Ticket

TKT-P22-003A: End-to-End Phone Stack Bootstrap Execution

## Status

Implemented in source; live hardware completion is still blocked until Android app install/Termux initialization is approved on the phone or trusted APKs are supplied.

## Summary

- Added a Phase 22 ticket and contract for the one-command phone stack bootstrap path.
- Updated `setup --production --execute --yes` so production execute defaults to script push.
- Added setup options for the existing trusted APK lane:
  - `--fdroid-apk`, `--fdroid-url`, `--fdroid-sha256`
  - `--termux-apk`, `--termux-url`, `--termux-sha256`
  - `--termux-api-apk`, `--termux-api-url`, `--termux-api-sha256`
- Production execute now installs or opens F-Droid, Termux, and Termux:API before script push when app bootstrap is enabled.
- Production execute opens Termux once, verifies Termux readiness, and pauses before script push when Android still blocks install/home initialization.
- Generated Termux files now include:
  - `bootstrap-phone-stack.sh`
  - `.termux/termux.properties`
- Script delivery pushes the one-command runner and Termux RUN_COMMAND configuration.
- Production execute requests `bootstrap-phone-stack.sh` through Termux RUN_COMMAND, then verifies Ollama tags, model inventory, and test prompt status in the setup receipt.

## Files Changed

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/phone-stack-bootstrap-contract.md`
- `.agents/build-tickets/phase-22/TKT-P22-003A-end-to-end-phone-stack-bootstrap-execution.md`
- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/termux_scripts.py`
- `src/pro_ai_server/script_delivery.py`
- `tests/test_cli_workflows.py`
- `tests/test_termux_scripts.py`
- `tests/test_script_delivery.py`
- `tests/test_setup_receipt.py`
- `tests/test_docs.py`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-003A-report.md`

## Validation

- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_termux_scripts.py tests/test_script_delivery.py tests/test_cli_workflows.py -q`
  - 102 passed
- `.\\.venv\\Scripts\\python.exe -m pytest tests/test_cli_workflows.py tests/test_termux_scripts.py tests/test_script_delivery.py tests/test_setup_workflow.py tests/test_setup_receipt.py tests/test_docs.py -q`
  - 139 passed
- `.\\.venv\\Scripts\\python.exe -m ruff check .`
  - Passed
- `.\\.venv\\Scripts\\pro-ai-server.exe validate-release`
  - Passed
- `.\\.venv\\Scripts\\python.exe -m pytest`
  - 417 passed

## Live Hardware Note

The connected Moto g 5G (2022) still needs Termux and Termux:API installed or approved before a full live bootstrap can complete. The new setup path will now pause before script push with explicit recovery instead of silently leaving the operator to discover the missing phone-side pieces.

## Follow-Up

- Run `setup --production --execute --yes --serial ZY22GKMWPN` with trusted Termux and Termux:API APKs or official pinned APK manifest values.
- Rerun TKT-P22-003 live Continue proof after the local endpoint responds.
