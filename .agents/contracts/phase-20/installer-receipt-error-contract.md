# Contract: Installer Receipts and Error States

## Phase

Phase 20: Production Installer Hardening

## Purpose

Give customers and support a clear summary of what happened during install.

## Receipt Must Include

- connected device serial and model when available
- selected model profile
- connection mode
- generated files
- pushed scripts
- Continue config path and backup path when written
- USB tunnel status
- Ollama server status
- test prompt result
- next action

## Error State Must Include

- human-readable problem
- likely cause
- exact recovery action
- debug detail for support reports

## Validation

- Receipt rendering is deterministic.
- Error states do not expose secrets.
- Diagnostics can include receipt context.

