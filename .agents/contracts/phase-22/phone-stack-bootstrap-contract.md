# Contract: Phone Stack Bootstrap Execution

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Make the production setup path drive the phone-side AI stack bootstrap instead of leaving operators to manually stitch together F-Droid, Termux, script push, Ollama startup, endpoint verification, and Continue readiness.

## Required Behavior

- `setup --production --execute --yes` defaults to the USB-first production path.
- Production execute installs or opens F-Droid, Termux, and Termux:API before script push when app bootstrap is enabled.
- Local or pinned APK inputs are verified through the existing checksum-gated APK path.
- The installer opens Termux once and verifies Termux, Termux:API, and Termux home readiness before pushing scripts.
- Generated Termux files include a one-command phone stack runner for bootstrap, Ollama install, model pull, and server start.
- Script delivery pushes the one-command runner and Termux `allow-external-apps` configuration.
- Production execute requests the Termux runner through Android's RUN_COMMAND path and clearly reports if Android blocks command execution.
- Production execute creates or preserves the USB-local endpoint path, verifies model inventory, and sends the test prompt.
- Receipts and docs record recoverable Android stops instead of claiming success when the endpoint is not reachable.

## Validation

- `pytest tests/test_cli_workflows.py tests/test_termux_scripts.py tests/test_script_delivery.py`
- `pytest tests/test_setup_workflow.py tests/test_setup_receipt.py tests/test_docs.py`
- `ruff check .`
- Live hardware: `pro-ai-server setup --production --execute --yes --serial <serial>`
