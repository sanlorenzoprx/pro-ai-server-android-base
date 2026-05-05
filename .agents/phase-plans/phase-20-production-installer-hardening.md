# Phase 20: Production Installer Hardening

## Goal

Turn the current Pro AI Server CLI setup flow into a production-ready Windows-first installer path for the core product.

This maps Roadmap v2 Phase 1: Core Product into buildable work: detect an Android phone, verify ADB, assess hardware, prepare Termux/Linux/Ollama, expose a safe USB endpoint, send a test prompt, and report clear success or error states.

## Non-Goals

- Do not make LAN or Tailscale the default production path.
- Do not build the full DevStack sales/demo funnel in this phase.
- Do not add autonomous coding-agent workflows to the customer installer.
- Do not hide required user approvals on Android.
- Do not require customers to install Python or developer tools.

## Build Tickets

| Ticket | Title | Depends On |
|---|---|---|
| TKT-P20-001 | Production installer state machine | Existing setup workflow |
| TKT-P20-002 | USB-first exposure guardrails | TKT-P20-001 |
| TKT-P20-003 | End-to-end Ollama test prompt | TKT-P20-001, TKT-P20-002 |
| TKT-P20-004 | Production receipts and error states | TKT-P20-001, TKT-P20-003 |
| TKT-P20-005 | Windows executable packaging | TKT-P20-001 through TKT-P20-004 |
| TKT-P20-006 | Simple Windows installer UI wrapper | TKT-P20-005 |
| TKT-P20-007 | Production installer docs and smoke script | TKT-P20-001 through TKT-P20-006 |

## Required Contracts

- `.agents/contracts/phase-20/installer-state-machine-contract.md`
- `.agents/contracts/phase-20/usb-production-mode-contract.md`
- `.agents/contracts/phase-20/ollama-test-prompt-contract.md`
- `.agents/contracts/phase-20/installer-receipt-error-contract.md`
- `.agents/contracts/phase-20/windows-packaging-contract.md`
- `.agents/contracts/phase-20/installer-ui-contract.md`

## Validation

```bash
ruff check .
pytest
pro-ai-server validate-release
pro-ai-server setup --mode usb
pro-ai-server setup --mode usb --execute --yes
pro-ai-server status
pro-ai-server diagnose --output diagnostics.txt
```

## Closeout Criteria

- The default production path is USB-only unless the operator explicitly enables advanced exposure.
- Installer output has stable step names and clear status.
- A final test prompt verifies that the local endpoint responds through USB.
- Windows packaging creates a runnable artifact that does not require a local Python install.
- The simple UI can run the production installer path and display clear success/error states.
- Docs explain Android approvals, Termux requirements, USB debugging, troubleshooting, and rollback.

