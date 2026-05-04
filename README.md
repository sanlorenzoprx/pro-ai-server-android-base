# Pro AI Server

Turn a spare Android phone into a local AI coding server for Continue-compatible IDEs such as VS Code, Cursor, VSCodium, and Windsurf.

Repository:

```text
https://github.com/sanlorenzoprx/pro-ai-server.git
```

## Current MVP

This branch contains the Python CLI MVP for preparing an Android phone to run Ollama from Termux and expose it to Continue.

The CLI currently supports:

- `doctor` host checks for Python, IDE CLIs, and ADB availability.
- `validate-platform-tools` checks for bundled Windows Platform Tools runtime files.
- `scan --serial <device>` Android hardware assessment over ADB.
- `generate-scripts` creation of inspectable Termux bootstrap, start, model install, Android optimization, and Termux:Widget helper files.
- `push-scripts --serial <device>` delivery of generated Termux files with `adb push`.
- `configure-continue --mode usb` Continue `config.yaml` generation, with backup protection for an existing config.
- `tunnel --serial <device>` USB forwarding with `adb reverse tcp:11434 tcp:11434`.
- `setup` plan mode and `setup --execute --yes` for the guided MVP flow.
- `setup-tailscale` host/phone Tailscale readiness checks with Windows `winget`, Android APK install, and Play Store launch support.
- `status` concise readiness summary for phone, USB tunnel, Ollama, and IDE integration.
- `diagnose --output diagnostics.txt` support reports for host, phone, tunnel, and local Ollama checks.

The MVP prefers bundled ADB at `embedded-tools/windows/platform-tools/adb.exe`, then falls back to system `adb` on `PATH`. Fastboot is not used by MVP behavior.

Cursor integration is supported through the Continue extension. `doctor` detects the `cursor` CLI on the host, and `configure-continue` writes the same `%USERPROFILE%\.continue\config.yaml` used by Continue-compatible IDEs on Windows.

## Agentic Codeflow

This clone adds an AI layer for evolving Pro AI Server into Pro CodeFlow Server, a local-first agentic coding assistant.

The AI layer lives in `.agents/`, `.codex/`, and `.cursor/`. These folders store project memory, PRDs, implementation plans, validation reports, mistake records, workflow definitions, Codex command templates, and Cursor rules so agents can follow a repeatable Plan, Implement, Validate, Report, and Improve loop.

The CodeFlow Build Bridge adds the missing step between roadmap and code: phase plans become build tickets, tickets reference contracts, implementation happens one ticket at a time, validation evidence is written back to reports, and phase closeout records whether the work is actually done.

## Gateway Preview

The gateway adds a dependency-light local gateway foundation for future Continue/Cursor routing:

- `pro-ai-server gateway-start`
- `pro-ai-server gateway-status`
- `pro-ai-server gateway-route-test --task chat`
- `pro-ai-server gateway-proxy-test --task chat`

Gateway defaults use `127.0.0.1:8765` and route through the configured Ollama API base. Model choices are configurable with `--model-profile`, `--chat-model`, and `--autocomplete-model`; the gateway does not hard-code one required LLM.

The current proxy supports non-streaming Ollama-compatible `GET /api/tags`, `POST /api/generate`, and `POST /api/chat`. Streaming proxy responses are deferred.

Gateway settings and per-task routes can be configured in `~/.pro-ai-server/config.yaml` or `.pro-ai-server/config.yaml`. Project config overrides user config, and CLI options override config.

## Code Index Preview

The Phase 4 code index adds local keyword search and prompt context generation:

- `pro-ai-server index .`
- `pro-ai-server index-status`
- `pro-ai-server search "gateway config"`
- `pro-ai-server context "add route support"`

The default SQLite database is `.pro-ai-server/index.sqlite`. See [docs/CODE_INDEX.md](docs/CODE_INDEX.md).

## Agent Workflows

Agent-ready workflows use git memory and the local code index:

- `pro-ai-server agent prime`
- `pro-ai-server agent context "gateway support"`
- `pro-ai-server agent plan "add gateway support"`

See [docs/AGENT_WORKFLOWS.md](docs/AGENT_WORKFLOWS.md).

See [docs/GATEWAY.md](docs/GATEWAY.md) for endpoint contracts and smoke-test steps.

## Windows Quickstart

```powershell
cd "C:\repos\Pro-AI-Server"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]

pro-ai-server doctor
pro-ai-server validate-platform-tools
pro-ai-server scan
pro-ai-server generate-scripts --mode usb
pro-ai-server push-scripts
pro-ai-server configure-continue --mode usb
pro-ai-server tunnel
```

When multiple phones are connected, pass `--serial <device>` to ADB-backed commands such as `scan`, `push-scripts`, and `tunnel`.

See [docs/CLI_WORKFLOW.md](docs/CLI_WORKFLOW.md) for the full MVP CLI flow, including setup plan/execute mode, LAN/Tailscale warnings, Continue backup behavior, and Termux:Widget placement.

## Connection Modes

USB is the default and safest MVP mode. It keeps Ollama bound to `127.0.0.1:11434` on the phone and uses `adb reverse` so Continue talks to `http://localhost:11434` on the host.

LAN and Tailscale modes require `--host` when configuring Continue or planning setup. LAN exposes Ollama to devices on the local network. Tailscale should use a private Tailscale hostname or `100.x.x.x` IP address.

Use `pro-ai-server setup-tailscale` to check Windows and Android Tailscale readiness. It can install the Windows client with `winget` using `--install-host --yes`, install a local Android APK with `--android-apk <path> --yes`, or open the Android Play Store page on the connected phone.

## Design Principles

- Ask before changing device or IDE settings.
- Back up existing Continue configuration before writing a new one.
- Prefer inspectable scripts over invisible automation.
- Keep the Ollama server bound to safe defaults unless the user explicitly chooses LAN or private tunnel mode.
- Detect RAM, storage, CPU architecture, Android version, battery, and Termux readiness before model install.
- Treat low-memory phones as experimental/lightweight devices.
