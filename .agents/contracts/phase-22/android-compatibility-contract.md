# Contract: Android Compatibility and APK Manifest Matrix

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Define the supported Android device net before production install so the plug-in-phone promise is honest across old and new Android phones.

## Required Behavior

- Classify Android devices as green, yellow, or red.
- Require Android 7.0+ for the supported Termux production lane.
- Require arm64 for the supported local LLM production lane.
- Use conservative model-tier guidance by Android version and RAM.
- Detect Play Store Termux conflicts.
- Warn when Termux and Termux:API come from different installer sources.
- Document APK manifest fields for F-Droid, Termux, and Termux:API.
- Keep exact pinned APK versions and checksums as reviewed manifest values, not guesses.

## Validation

- Tests cover green, yellow, and red device classes.
- Tests cover Android below 7, 32-bit ABI, Play Store conflict, mixed installer warning, and manifest selection.
- Live hardware compatibility is recorded in production RC evidence.
