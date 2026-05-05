# Contract: Windows Packaging

## Phase

Phase 20: Production Installer Hardening

## Purpose

Ship Pro AI Server as a Windows executable that does not require a customer-managed Python environment.

## Required Behavior

- Build artifact runs on Windows from a clean folder.
- Bundled ADB lookup works from the packaged layout.
- CLI entry point supports doctor, setup, status, diagnose, and validate commands.
- Version and release metadata are visible.
- Packaging excludes caches, virtualenvs, and local secrets.

## Validation

- Packaging command creates a local artifact.
- Artifact can run `doctor` and `validate-platform-tools`.
- Release checklist documents build and smoke steps.

