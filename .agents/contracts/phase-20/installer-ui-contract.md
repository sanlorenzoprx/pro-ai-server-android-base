# Contract: Simple Installer UI

## Phase

Phase 20: Production Installer Hardening

## Purpose

Provide a simple Windows-first UI over the production installer state machine.

## Required Screens

- welcome and USB debugging checklist
- device detection
- hardware scan and model recommendation
- install progress
- test prompt result
- IDE configuration prompt
- success receipt
- recoverable error state

## Behavior

- UI must call the same state machine as the CLI.
- UI must show one current step and a compact step list.
- UI must preserve support/debug details for copyable diagnostics.
- UI must not expose advanced network modes during first-run setup.

## Validation

- UI smoke can run without a phone using mocked step results.
- Manual smoke verifies readable success and failure states.

