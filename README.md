# Pro AI Server

Turn a spare Android phone into a local AI coding server for Continue-compatible IDEs such as VS Code, Cursor, VSCodium, and Windsurf.

Repository:

```text
https://github.com/sanlorenzoprx/pro-ai-server.git
```

## Product direction

Pro AI Server helps a developer reuse an Android phone as a dedicated local AI server for coding workflows.

The product value is:

- local privacy for code and prompts
- lower load on the main laptop or desktop
- reuse of existing Android hardware
- optional USB, local network, or private tunnel connection modes
- IDE integration through Continue and Ollama-compatible APIs

## MVP scope

The first release should include:

1. A Python CLI installer and manager.
2. `doctor` command for host checks.
3. `scan` command for Android hardware assessment.
4. `generate` command for Termux bootstrap scripts and Continue config.
5. `tunnel` command for `adb reverse tcp:11434 tcp:11434`.
6. `diagnose` command for support logs.
7. Clear docs for manual phone setup.

## Design principles

- Ask before changing device or IDE settings.
- Back up existing Continue configuration before writing a new one.
- Prefer inspectable scripts over invisible automation.
- Keep the Ollama server bound to safe defaults unless the user explicitly chooses LAN or private tunnel mode.
- Detect RAM, storage, CPU architecture, Android version, battery, and Termux readiness before model install.
- Treat low-memory phones as experimental/lightweight devices.

## Recommended local path

```powershell
cd "C:\repos\Pro AI Server"
git clone https://github.com/sanlorenzoprx/pro-ai-server.git .
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
pro-ai-server doctor
```

## Current status

Initial planning and bootstrap stage.
