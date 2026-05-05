# TKT-P20-006 Implementation Report

## Ticket

TKT-P20-006: Simple Windows Installer UI

## Summary

Added the first simple installer UI wrapper over the production installer state machine.

This is a Windows-first text UI preview, not a separate setup path. It derives screens from `plan_production_installer` so the UI stays aligned with the production CLI flow.

## Changes

- Added `pro_ai_server.installer_ui`.
- Added `InstallerUIScreen` and `InstallerUIFlow`.
- Added screen grouping for welcome, device detection, hardware scan, install progress, test prompt, IDE configuration, success receipt, and recoverable error.
- Added `pro-ai-server installer-ui`.
- Added `--mock-failure <step-key>` to smoke recoverable errors without a phone.
- Added `docs/INSTALLER_UI.md`.
- Added UI flow and CLI preview tests.

## Validation

```bash
.\.venv\Scripts\python.exe -m pytest tests/test_installer_ui.py tests/test_setup_workflow.py tests/test_cli_workflows.py tests/test_docs.py
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\pro-ai-server.exe validate-release
.\.venv\Scripts\python.exe -m pytest
```

Results:

- Focused tests passed: 90 tests.
- Ruff passed.
- Release validation passed.
- Full suite passed: 375 tests.

## Manual Smoke

Mockable no-phone UI smoke:

```powershell
pro-ai-server installer-ui
pro-ai-server installer-ui --mock-failure termux-readiness
```

## Follow-Up

- TKT-P20-007 should close Phase 20 with production installer docs and smoke evidence.

