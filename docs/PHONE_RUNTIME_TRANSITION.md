# Phone Runtime Transition

This document defines the current phone runtime responsibilities, the host-side expectations that already exist in this repository, and the replacement boundary for moving beyond the current Termux/Debian/Ollama lane.

The goal is not to rethink the repo base. The goal is to replace the weakest part of the system without breaking the strongest part.

## Current System Truth

Today the repository is a Windows-managed Android AI host system.

What is already strong:

- Windows CLI and packaged executable flow
- ADB-based device detection and setup control
- Android compatibility checks
- Continue-compatible IDE configuration
- USB tunnel orchestration through `adb forward tcp:11434 tcp:11434`
- status, diagnostics, server-check, and test-prompt verification

What is still transitional:

- phone-side runtime packaging
- phone-side install friction
- phone-side lifecycle control
- model installation and recovery path

The current phone runtime is proven, but it is not yet the long-term product runtime.

## Current Phone Runtime Responsibilities

The current phone lane uses Termux, Debian `proot-distro`, and Ollama.

### Phone-side responsibilities today

1. Provide a local HTTP endpoint on the phone at `127.0.0.1:11434` in USB mode.
2. Start and keep the inference server process running.
3. Pull and store the selected chat and autocomplete models.
4. Expose model inventory through `GET /api/tags`.
5. Accept a non-streaming text generation request through `POST /api/generate`.
6. Support the current gateway-compatible surface for `GET /api/tags`, `POST /api/generate`, and `POST /api/chat`.
7. Remain reachable from Windows through `adb forward tcp:11434 tcp:11434`.

### Scripted runtime steps today

The generated Termux bundle currently does the following:

- `bootstrap.sh`
  - updates Termux packages
  - installs `proot-distro`, `curl`, and `termux-api`
  - installs Debian inside Termux

- `setup-ollama-debian.sh`
  - installs Ollama inside Debian

- `start-pro-ai-server.sh`
  - acquires a Termux wake lock
  - starts `ollama serve` inside Debian with the selected bind host

- `install-models.sh`
  - pulls the selected models inside Debian

- `bootstrap-phone-stack.sh`
  - runs bootstrap
  - installs Ollama in Debian
  - starts the server
  - pulls models
  - records logs and PID state

## What the Host Already Expects

The host side is already coded against a practical contract.

### Transport expectations

- ADB is the control channel.
- USB mode uses `adb forward tcp:11434 tcp:11434`.
- The host reaches the phone endpoint at `http://localhost:11434`.

### Runtime health expectations

The host verifies the phone runtime through:

- `curl http://localhost:11434/api/tags`
- `curl -X POST http://localhost:11434/api/generate`
- model inventory checks against the selected profile
- `status`
- `server-check`
- `test-prompt`
- `diagnose`

### Setup expectations

The host currently assumes it can:

- assess Android compatibility
- verify Termux and Termux:API readiness
- deliver scripts
- request the phone stack bootstrap
- verify endpoint health after bootstrap

### Behavioral expectations

The host does not care that the implementation is Termux/Debian/Ollama specifically.

What it actually cares about is:

- the runtime becomes reachable at the expected API base
- required models can be installed and enumerated
- test prompt succeeds
- recoverable failures produce actionable diagnostics

## Runtime Replacement Boundary

This is the most important section in the document.

We should replace the phone runtime behind a stable boundary, not rewrite the host control plane around the runtime.

### Can change safely

These can change without breaking the host tooling, as long as the external contract remains stable:

- Termux usage
- Debian `proot-distro` usage
- Ollama as the actual on-device server binary
- model storage layout on the phone
- phone-side process supervision implementation
- how models are downloaded internally
- whether the runtime is launched by shell script, native app service, or companion-managed worker

### Must stay stable during transition

These should remain stable while the runtime is replaced:

- host-side API base in USB mode: `http://localhost:11434`
- USB tunnel behavior: `adb forward tcp:11434 tcp:11434`
- model inventory semantics used by `server-check`
- test prompt semantics used by `test-prompt`
- setup receipt and diagnostics concepts
- compatibility scan and profile selection behavior

### Stable host contract

The runtime replacement should satisfy this contract:

1. Runtime can be started by the system or companion flow.
2. Runtime exposes a local HTTP endpoint.
3. Runtime responds to:
   - `GET /api/tags`
   - `POST /api/generate`
   - `POST /api/chat`
4. Runtime can report missing models clearly.
5. Runtime supports deterministic lightweight and professional model lanes.
6. Runtime failures can be surfaced as actionable setup or status errors.

## Native Runtime Evaluation

### Option A: stay longer with Termux/Debian/Ollama

Benefits:

- already proven on real hardware
- minimal immediate rewrite
- current CLI and docs already match this lane
- useful for continued hardware evidence gathering

Costs:

- high install friction
- Android storage and permission edge cases
- weak lifecycle control
- brittle package repair path
- difficult to make feel like a customer-grade install

Conclusion:

Useful as a transitional lane, not a strong long-term default.

### Option B: move to native runtime with `llama.cpp`

Benefits:

- more direct control over Android packaging
- better long-term fit for companion-app control
- broader ability to tune threads, memory, quantization, and lifecycle
- removes dependence on Debian-in-Termux as the main product path
- strongest path toward cleaner first-run installation

Costs:

- native Android runtime integration work
- model management and API shim must be built or adapted
- packaging and service control become our responsibility

Conclusion:

`llama.cpp` is the most likely long-term runtime base.

### Recommendation

Keep the current Termux/Debian/Ollama path as the transitional evidence lane while planning a native `llama.cpp` runtime that preserves the current host contract.

## API Compatibility Strategy

Compatibility must remain modular.

### Recommended surface

Primary runtime surface:

- Ollama-compatible:
  - `GET /api/tags`
  - `POST /api/generate`
  - `POST /api/chat`

Optional adapter later:

- OpenAI-compatible endpoints where useful for future integrations

### Why Ollama-compatible first

- the current host code already uses this shape
- Continue-compatible workflows already align with it
- the repository gateway layer already assumes an Ollama-compatible runtime
- it minimizes host-side churn during runtime replacement

### Runtime implementation rule

The runtime implementation must be swappable underneath the API surface.

That means:

- API contract is product-facing
- runtime engine is implementation-facing

The product should not require the host to care whether the phone uses:

- Ollama in Debian
- native `llama.cpp`
- a future packaged engine

## Transition Plan

### Stage 1: preserve the host contract

- keep current USB host flow working
- keep `status`, `server-check`, `test-prompt`, and `diagnose` stable
- keep compatibility and profile selection stable

### Stage 2: define the native runtime shim

- choose `llama.cpp` as the likely engine
- define model storage and lifecycle expectations
- define the local API shim that preserves `/api/tags`, `/api/generate`, and `/api/chat`

### Stage 3: run parallel runtime lanes

- transitional lane: Termux/Debian/Ollama
- new lane: native runtime prototype

Use the same host validation flow against both lanes where possible.

### Stage 4: promote the native lane

- once the native lane satisfies the host contract
- once install friction is materially lower
- once diagnostics and recovery are adequate

Then the native lane becomes the default supported phone runtime.

## Decision Summary

- Do not rethink the repo base again.
- Preserve the Windows control plane.
- Treat the current phone runtime as transitional.
- Preserve the Ollama-compatible host contract.
- Evaluate `llama.cpp` as the next runtime base.
- Replace the phone runtime behind a stable API and transport boundary.
