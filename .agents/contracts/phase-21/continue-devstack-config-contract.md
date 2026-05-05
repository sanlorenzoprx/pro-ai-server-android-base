# Contract: Continue DevStack Config

## Phase

Phase 21: DevStack Coding Server Launch

## Purpose

Generate Continue.dev config suitable for a local coding assistant demo.

## Required Behavior

- Configure chat model from the selected hardware profile.
- Configure autocomplete model from the selected hardware profile.
- Use `http://localhost:11434` for USB launch mode.
- Back up existing user config before writing.
- Print backup and restore instructions.

## Validation

- Tests cover rendered config shape.
- Tests cover backup behavior.
- Manual demo confirms Cursor or VS Code can chat against the local endpoint.

