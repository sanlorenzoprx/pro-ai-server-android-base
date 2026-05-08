# llama.cpp Wrapper Contract

This document defines the wrapper boundary for a native `llama.cpp` phone runtime.

It exists to protect the rest of the product from raw engine details while preserving the current host-side contract already used by the Windows CLI, gateway, diagnostics, and IDE workflows.

See:

- [PHONE_RUNTIME_TRANSITION.md](PHONE_RUNTIME_TRANSITION.md)
- [NATIVE_RUNTIME_RESEARCH_NOTE.md](NATIVE_RUNTIME_RESEARCH_NOTE.md)
- [GATEWAY.md](GATEWAY.md)

Current scaffold:

- [src/pro_ai_server/native_runtime.py](/abs/c:/repos/pro-ai-server-android-base/src/pro_ai_server/native_runtime.py)
- [src/pro_ai_server/native-runtime-manifest.json](/abs/c:/repos/pro-ai-server-android-base/src/pro_ai_server/native-runtime-manifest.json)
- `pro-ai-server native-runtime-config --profile professional --prefer chat`
- `pro-ai-server native-runtime-plan --profile professional`
- `pro-ai-server native-runtime-start --profile professional`
- `pro-ai-server native-runtime-status`
- `pro-ai-server native-runtime-stop`
- `pro-ai-server native-runtime-doctor`
- `pro-ai-server native-runtime-android-plan`
- `pro-ai-server native-runtime-android-install`
- `pro-ai-server native-runtime-android-start`
- `pro-ai-server native-runtime-android-status`
- `pro-ai-server native-runtime-android-smoke`
- `pro-ai-server native-runtime-android-smoke-path`
- `pro-ai-server native-runtime-android-stop`

## Purpose

The wrapper is the controlled layer between:

- the host and product logic
- the native inference engine

The host should talk to a stable local runtime contract.

The wrapper should handle:

- engine startup and shutdown
- model loading and unloading
- runtime configuration
- request translation
- health and status reporting
- structured error reporting

The host should not need to know whether the phone runtime uses:

- Ollama in Debian
- native `llama.cpp`
- a future packaged engine

## Non-Negotiable Host Contract

The wrapper must preserve these existing expectations:

1. USB host path reaches the runtime through `adb forward tcp:11434 tcp:11434`.
2. The host checks the phone at `http://localhost:11434`.
3. The runtime supports:
   - `GET /api/tags`
   - `POST /api/generate`
   - `POST /api/chat`
4. `status`, `server-check`, `test-prompt`, and `diagnose` remain meaningful without large host-side rewrites.
5. Model inventory and missing-model behavior remain deterministic.

## Runtime Responsibilities

The wrapper runtime is responsible for:

- exposing the local HTTP API
- loading a selected GGUF model
- starting inference with runtime settings
- reporting loaded model metadata
- translating generate/chat requests into `llama.cpp` calls
- returning structured errors when startup, model loading, or inference fails

## Local Runtime Endpoints

### `GET /health`

Purpose:

- internal runtime health endpoint
- useful for future companion app and richer diagnostics

Minimum response:

```json
{
  "status": "ok",
  "engine": "llama.cpp",
  "runtime": "native-wrapper"
}
```

### `GET /api/tags`

Purpose:

- preserve current model inventory contract

Minimum response shape:

```json
{
  "models": [
    {
      "name": "qwen2.5-coder:1.5b"
    }
  ]
}
```

Contract notes:

- model entries must include a stable string name
- names must match host-side configured model expectations
- if no model is loaded, return an empty `models` list or a structured runtime error, but keep behavior deterministic

### `POST /api/generate`

Purpose:

- preserve current non-streaming generation contract

Minimum request shape:

```json
{
  "model": "qwen2.5-coder:1.5b",
  "prompt": "Reply with exactly: pro-ai-server-ready",
  "stream": false
}
```

Minimum success response shape:

```json
{
  "response": "pro-ai-server-ready"
}
```

Contract notes:

- non-streaming support is required
- `stream: true` may be rejected explicitly during the initial native lane
- missing `model` may be accepted later, but the first implementation should prefer explicit model handling

### `POST /api/chat`

Purpose:

- preserve gateway-compatible chat surface

Minimum request shape:

```json
{
  "model": "qwen2.5-coder:1.5b",
  "messages": [
    {
      "role": "user",
      "content": "Say hello"
    }
  ],
  "stream": false
}
```

Minimum success response shape:

```json
{
  "message": {
    "role": "assistant",
    "content": "hello"
  }
}
```

Contract notes:

- shape should remain compatible with current gateway expectations
- first implementation can stay non-streaming

## Runtime Configuration Inputs

The wrapper should accept configuration for:

- model file path
- exposed model name
- host bind address
- port
- context length
- threads
- GPU/offload setting when supported
- temperature and generation defaults later if needed

The host should not need to know raw engine flag details.

The current scaffold includes a profile-to-runtime mapping layer in
[native_runtime.py](/abs/c:/repos/pro-ai-server-android-base/src/pro_ai_server/native_runtime.py)
that resolves:

- product model profile
- preferred runtime role such as `chat` or `autocomplete`
- stable contract name
- concrete GGUF filename
- runtime defaults such as context length and threads

The default manifest is packaged at
[native-runtime-manifest.json](/abs/c:/repos/pro-ai-server-android-base/src/pro_ai_server/native-runtime-manifest.json).
It keeps the initial model catalog data-driven so curated model choices can change
without rewriting host or gateway logic.

The current CLI inspection surface is:

```powershell
pro-ai-server native-runtime-config --profile professional --prefer chat
```

It also renders the planned `llama-server` startup command without launching the
engine. The command builder follows the official `llama-server` direction from
`llama.cpp`, where the HTTP server is started with a GGUF model and bind port.

The current launch-plan inspection surface is:

```powershell
pro-ai-server native-runtime-plan --profile professional
```

It checks whether the selected `llama-server` executable and resolved GGUF model
file are present before any future launch command starts a long-running process.

The controlled startup surface is:

```powershell
pro-ai-server native-runtime-start --profile professional
```

Startup must:

- refuse to launch when the plan is not ready unless `--force` is passed
- start `llama-server` from the rendered command
- poll the local `/api/tags` endpoint for readiness
- report the process PID and readiness result

## Lifecycle State

Native runtime startup writes a local state file:

```text
.cache/pro-ai-server/native-runtime-state.json
```

The state file records:

- PID
- startup command
- API base
- model contract name
- GGUF path
- start timestamp

`native-runtime-status` reads this state file, checks the recorded process, and
polls `/api/tags`.

`native-runtime-stop` only targets the recorded PID and removes the state file
after a stop attempt.

`native-runtime-doctor` combines profile resolution, manifest loading, launch
readiness, lifecycle state, and `/api/tags` readiness into one read-only
preflight report.

## Android Asset Placement

The native Android asset lane places files under:

```text
/data/local/tmp/pro-ai-server/native-runtime
```

The default layout is:

- `bin/llama-server`
- `models/<selected-model>.gguf`
- `config/native-runtime-manifest.json`
- `state/`
- `logs/`

`native-runtime-android-plan` renders the ADB commands without mutating the
phone.

`native-runtime-android-install --execute --yes` creates the remote directories,
pushes the selected runtime binary, selected GGUF model, and manifest, marks the
runtime binary executable, and requests `adb forward tcp:11434 tcp:11434`.

`native-runtime-android-start --execute --yes` requests a remote `llama-server`
start under the same Android layout, writes a remote PID file, writes logs, and
requests `adb forward tcp:11434 tcp:11434`.

`native-runtime-android-status --execute` checks the remote PID file, process
state, recent logs, and requested ADB forward.

`native-runtime-android-smoke --execute` requests the same ADB forward, checks
the forwarded `/api/tags` inventory, and sends a tiny non-streaming
`/api/generate` prompt through the native Android runtime.

`native-runtime-android-smoke-path --execute --yes` chains install, start, and
smoke into one guarded operator path once the local `llama-server` binary and
GGUF models are available.

`native-runtime-android-stop --execute --yes` stops only the PID recorded in the
remote PID file, removes that PID file, and removes the host ADB forward.

Alternate manifests can be inspected with:

```powershell
pro-ai-server native-runtime-config --profile professional --manifest .\native-runtime-manifest.json
```

It should render:

- selected profile
- selected runtime role
- stable contract model name
- resolved GGUF path
- API base
- runtime defaults

## Model Identity Rule

The wrapper must separate:

- model display or contract name
- model file path on disk

Example:

- contract name: `qwen2.5-coder:1.5b`
- GGUF file: `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`

This is critical so the host can keep stable profile names while the on-disk model package can evolve.

## Error Contract

The wrapper must return structured, actionable errors.

Minimum error response shape:

```json
{
  "error": "model_not_loaded",
  "message": "Requested model is not loaded."
}
```

Initial required error categories:

- `runtime_not_ready`
- `model_not_loaded`
- `model_load_failed`
- `invalid_request`
- `unsupported_streaming`
- `generation_failed`

## Startup Contract

The wrapper should support a simple lifecycle:

1. runtime starts
2. configuration is loaded
3. selected model is loaded
4. HTTP API becomes available
5. `GET /api/tags` returns visible model inventory

The host-side success criteria remain:

- `status` sees a responsive runtime
- `server-check` sees required models
- `test-prompt` receives valid generated text

## Modularity Rule

The wrapper is where engine-specific logic belongs.

The host and gateway layers should not contain:

- raw `llama.cpp` CLI flag construction
- GGUF parsing assumptions
- engine-specific thread tuning logic
- engine-specific lifecycle behavior

Those concerns belong inside the wrapper.

## First Implementation Boundary

The first native wrapper does not need to solve everything.

It should solve:

- one loaded model at a time
- non-streaming `/api/generate`
- non-streaming `/api/chat`
- inventory via `/api/tags`
- structured startup and generation errors

It can defer:

- streaming
- embeddings
- multiple concurrently loaded models
- advanced tool calling
- remote management features

## Build Target

The first implementation target is not "replace the whole system."

The first implementation target is:

- satisfy the existing host contract
- lower phone-side runtime friction
- prove that native `llama.cpp` can sit behind the same local API shape
