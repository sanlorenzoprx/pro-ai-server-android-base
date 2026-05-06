# TKT-P22-003B: Installer Automation Hardening From Moto Live Smoke

## Target Repo

Pro AI Server and Pro Agentic Coding Server

## Target Area

Production phone setup and USB endpoint automation

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Source Docs

- `.agents/phase-plans/phase-22-production-hardware-validation-rc.md`
- `.agents/contracts/phase-22/phone-stack-bootstrap-contract.md`
- `docs/PRODUCTION_RC.md`

## User / Operator Served

Founder/operator running the first private beta install on real Android hardware.

## Pain Solved

The Moto g 5G live smoke proved the endpoint works, but also exposed manual recovery steps that must be made explicit or automated before a customer-safe installer claim.

## Definition of Done

- USB tunnel creation uses host-to-phone `adb forward tcp:11434 tcp:11434`.
- Phone stack bootstrap starts Ollama before pulling models.
- Setup docs record that Android 13 can block direct private Termux home writes from ADB.
- Troubleshooting includes Termux package repair for stale `curl`/OpenSSL linkage.
- Background execution prompt is documented as a required Android approval.
- Tests cover tunnel direction and phone bootstrap ordering.

## Expected Files to Change

- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/status.py`
- `src/pro_ai_server/setup_workflow.py`
- `src/pro_ai_server/setup_receipt.py`
- `src/pro_ai_server/termux_scripts.py`
- `tests/`
- `docs/PRODUCTION_RC.md`
- `docs/CLI_WORKFLOW.md`
- `docs/TROUBLESHOOTING.md`

## Validation

- `pytest tests/test_adb.py tests/test_status.py tests/test_setup_workflow.py tests/test_setup_receipt.py tests/test_termux_scripts.py`
- `pro-ai-server status`
- `pro-ai-server server-check --profile lightweight`
- `pro-ai-server test-prompt --profile lightweight`

## Dependencies

- TKT-P22-003A

## Follow-Up Tickets Unlocked

- TKT-P22-004A
