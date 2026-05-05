# Contract: Live Continue IDE Validation

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Confirm the DevStack coding assistant works inside a launch IDE using Continue and the local phone endpoint.

## Required Behavior

- Validate either VS Code or Cursor readiness.
- Install or verify the Continue extension.
- Write the DevStack Continue config.
- Confirm the IDE can chat against `http://localhost:11434`.
- Confirm one autocomplete or coding assistance moment.
- Record the IDE, Continue state, prompt, model response, and any latency or low-RAM caveats.

## Validation

- `pro-ai-server devstack-ide-status`
- `pro-ai-server configure-devstack`
- Manual Continue chat in VS Code or Cursor
- Manual autocomplete or code assistance proof
