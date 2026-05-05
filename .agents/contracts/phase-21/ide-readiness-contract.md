# Contract: IDE Readiness Matrix

## Phase

Phase 21: DevStack Coding Server Launch

## Purpose

Define launch-ready IDE support for Pro Agentic Coding Server.

## Launch IDEs

- VS Code
- Cursor

## Follow-Up IDEs

- Windsurf
- JetBrains

## Required Behavior

- Detect installed launch IDE CLIs.
- Detect whether Continue is installed for supported IDEs.
- Offer an install command for Continue when supported by the IDE CLI.
- Print clear next action when the IDE CLI is missing.

## Validation

- Tests cover installed, missing, and Continue-not-installed cases.
- Docs include Windows command examples.

