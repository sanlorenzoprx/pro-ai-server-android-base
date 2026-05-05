# Production Release Candidate

Phase 22 validates the first production release candidate on real hardware before private beta, creator traffic, affiliate traffic, or paid launch.

The release-candidate path is intentionally narrow:

- Windows first.
- USB-first Android phone connection.
- Local Ollama-compatible endpoint at `http://localhost:11434`.
- VS Code or Cursor through Continue.
- No LAN, Tailscale, JetBrains, or Windsurf as release blockers.

## Required Gates

Run source-tree gates before building the packaged artifact:

```powershell
pro-ai-server validate-release
pytest
ruff check .
```

Build and smoke the Windows release candidate:

```powershell
scripts/build-windows-exe.ps1
dist\pro-ai-server\pro-ai-server.exe validate-release
dist\pro-ai-server\pro-ai-server.exe setup --production
dist\pro-ai-server\pro-ai-server.exe status
dist\pro-ai-server\pro-ai-server.exe diagnose --output diagnostics.txt
```

Run real hardware smoke with a connected Android phone:

```powershell
scripts/smoke-production-installer.ps1 -WithPhone
pro-ai-server setup --execute --yes
pro-ai-server tunnel
pro-ai-server test-prompt
pro-ai-server status
```

Run DevStack IDE validation:

```powershell
pro-ai-server devstack-ide-status
pro-ai-server configure-devstack
```

Then confirm Continue chat and one coding assistance moment inside VS Code or Cursor.

## Hardware Smoke Matrix

Record one row per phone:

| Phone | Android | Serial Recorded | RAM Profile | Chat Model | Autocomplete Model | Setup Execute | Tunnel | Test Prompt | Status | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Failure notes:

- Record missing phone, unauthorized phone, missing Termux, missing Ollama, tunnel failure, model pull failure, slow response, and test prompt failure.
- Record recovery steps and whether the issue blocks release.

## Packaged Exe Evidence

Record:

- Artifact path: `dist\pro-ai-server\pro-ai-server.exe`
- Build command and result.
- `validate-release` result.
- No-phone smoke result.
- With-phone smoke result when available.
- Bundled ADB validation result.
- Known packaging limitations.

## Live IDE Evidence

Record:

- IDE: VS Code or Cursor.
- Continue extension state.
- API base: `http://localhost:11434`.
- Chat prompt used.
- Response summary.
- Autocomplete or coding assistance proof.
- Latency or low-RAM caveats.
- Screenshot or recording filename when available.

## Release Evidence Bundle

The final evidence bundle should include:

- Hardware smoke matrix.
- Packaged exe smoke results.
- Live IDE validation notes.
- Demo recording or screenshot filenames.
- Known limitations.
- Customer-safe support notes.
- Go/no-go decision.

## RC Decision

Use one of these decisions:

- `go`: all release-candidate gates passed and no blocking issues remain.
- `go-with-limitations`: the narrow launch path works, but documented limitations must be shown before private beta.
- `no-go`: a blocking issue prevents private beta or paid install.

Do not mark `go` unless at least one Android phone, the packaged Windows executable, and one launch IDE have completed the Phase 22 evidence path.
