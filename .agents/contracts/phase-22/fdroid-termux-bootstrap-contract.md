# Contract: F-Droid and Termux Bootstrap

## Phase

Phase 22: Production Hardware Validation and First Release Candidate

## Purpose

Make the phone bootstrap path match the product promise: plug in an Android phone and let Pro AI Server guide or perform the required app installation steps before Termux/Ollama setup.

## Required Behavior

- Detect whether F-Droid is installed.
- Install F-Droid from a provided local APK when `--fdroid-apk --yes` is used.
- Detect whether Termux and Termux:API are installed.
- Open F-Droid's "Install unknown apps" permission screen when F-Droid is present.
- Install Termux and Termux:API from provided local APKs when `--termux-apk`, `--termux-api-apk`, and `--yes` are used.
- Open trusted F-Droid package pages when local APKs are not provided.
- Never silently install APKs without explicit `--yes`.
- Tell the operator to open Termux once after install so the home directory initializes.

## Validation

- Tests cover F-Droid missing, F-Droid local APK install, permission screen opening, Termux page opening, local APK install, and refusal without `--yes`.
- Live hardware smoke records whether F-Droid, Termux, and Termux:API are installed.
