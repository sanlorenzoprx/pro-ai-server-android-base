# Mistake: CLI Config Precedence Regression

## Date

2026-05-03

## Context

Phase 3 added gateway YAML config loading, per-task route overrides, and CLI options that can override config.

## Failure

The first full test run failed `test_gateway_start_calls_server_with_configurable_models`.

## Root Cause

- The `gateway-start` command accidentally received an optional `None` `model_profile` default after the `gateway-route-test` config precedence change.
- `GatewaySettings` requires a concrete model profile, so `None` failed validation.

## Fix Applied

- Restored `gateway-start --model-profile` to the explicit default `professional`.
- Made `gateway-route-test --model-profile` optional so config wins unless the user explicitly overrides it.

## System Improvement

Keep separate rules for commands that start services with explicit defaults and commands that load optional config overlays.

## Prevent Next Time

When adding config precedence to CLI options, test both:

- a command with no config file and explicit defaults
- a command with a config file where CLI options are intentionally omitted

