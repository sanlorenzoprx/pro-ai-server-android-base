# TKT-P20-003: End-to-End Ollama Test Prompt

## Target Repo

Pro AI Server

## Target Area

`src/pro_ai_server/ollama.py`, `src/pro_ai_server/cli.py`

## Phase

Phase 20: Production Installer Hardening

## Source Docs

- `.agents/phase-plans/phase-20-production-installer-hardening.md`
- `.agents/contracts/phase-20/ollama-test-prompt-contract.md`

## User / Operator Served

Customers and support operators who need proof that the local AI server actually responds.

## Pain Solved

An installer can pass file and tunnel checks while the model endpoint still fails. The production path needs a final AI response test.

## Definition of Done

- Add a test prompt function for Ollama-compatible `/api/generate`.
- Use the selected chat model by default.
- Parse success from a valid non-empty response.
- Return actionable failures for connection errors, missing models, invalid JSON, and empty output.
- Expose the check through production setup and status or a CLI command.
- Tests cover success and failure modes.

## Expected Files to Change

- `src/pro_ai_server/ollama.py`
- `src/pro_ai_server/cli.py`
- `src/pro_ai_server/setup_receipt.py`
- `tests/test_ollama.py`
- `tests/test_cli_workflows.py`
- `tests/test_setup_receipt.py`

## Validation

- `ruff check .`
- `pytest tests/test_ollama.py tests/test_cli_workflows.py tests/test_setup_receipt.py`
- Manual smoke through USB after `pro-ai-server tunnel`

## Dependencies

- TKT-P20-001
- TKT-P20-002

## Follow-Up Tickets Unlocked

- TKT-P20-004

