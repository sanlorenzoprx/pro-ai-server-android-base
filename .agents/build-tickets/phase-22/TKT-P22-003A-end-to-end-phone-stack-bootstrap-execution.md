# TKT-P22-003A: End-to-End Phone Stack Bootstrap Execution

## Target Repo

Pro AI Server / Pro Agentic Coding Server

## Target Area

Production phone-side bootstrap execution

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/phone-stack-bootstrap-contract.md`

## User / Operator Served

Customer or operator expecting the plug-in-phone production promise.

## Pain Solved

The product cannot rely on customers manually discovering F-Droid pages, opening Termux, running bootstrap scripts, installing models, starting Ollama, and then returning to the host. The production setup path needs to orchestrate as much of that chain as Android permits and stop only with clear recovery instructions.

## Definition of Done

- `setup --production --execute --yes` defaults to pushing phone scripts.
- Setup can install or open F-Droid, Termux, and Termux:API using the existing APK trust lane.
- Setup verifies Termux readiness before script push.
- Generated scripts include a one-command phone stack bootstrap runner.
- Script push includes the runner and Termux RUN_COMMAND configuration.
- Setup requests the Termux runner and records endpoint/test-prompt verification.
- Docs and reports describe the remaining Android-imposed stops honestly.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/termux_scripts.py`
- `src/pro_ai_server/script_delivery.py`
- `tests/test_cli_workflows.py`
- `tests/test_termux_scripts.py`
- `tests/test_script_delivery.py`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`
- `docs/PRODUCTION_RC.md`
- `.agents/reports/TKT-P22-003A-report.md`

## Validation

- `pytest tests/test_cli_workflows.py tests/test_termux_scripts.py tests/test_script_delivery.py`
- `pytest tests/test_setup_workflow.py tests/test_setup_receipt.py tests/test_docs.py`
- `ruff check .`

## Dependencies

- TKT-P22-003

## Follow-Up Tickets Unlocked

- TKT-P22-004
