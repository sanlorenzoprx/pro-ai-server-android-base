# Phase 21: DevStack Coding Server Launch

## Goal

Package Pro Agentic Coding Server as the first cash-flow product for developers, vibe coders, and indie builders.

This maps Roadmap v2 Phase 2: Cash Flow Product into buildable work. The offer is: turn your old Android phone into a private AI coding assistant for Cursor, VS Code, and Continue-compatible IDEs with no monthly AI model bill for supported local workflows.

## Non-Goals

- Do not delay the core installer on pricing, affiliate, or B2B receptionist work.
- Do not require LAN or Tailscale for the first DevStack demo.
- Do not support JetBrains as a launch blocker.
- Do not build a complex SaaS backend before the local demo converts.
- Do not promise model performance beyond what the scanned phone profile supports.

## Build Tickets

| Ticket | Title | Depends On |
|---|---|---|
| TKT-P21-001 | Launch IDE readiness matrix | Phase 20 USB installer |
| TKT-P21-002 | Continue.dev coding config presets | TKT-P21-001 |
| TKT-P21-003 | DevStack demo script and smoke path | TKT-P21-001, TKT-P21-002 |
| TKT-P21-004 | DevStack offer and pricing docs | TKT-P21-003 |
| TKT-P21-005 | Demo capture checklist | TKT-P21-003, TKT-P21-004 |
| TKT-P21-006 | Launch-page instrumentation plan | TKT-P21-004 |

## Required Contracts

- `.agents/contracts/phase-21/ide-readiness-contract.md`
- `.agents/contracts/phase-21/continue-devstack-config-contract.md`
- `.agents/contracts/phase-21/devstack-demo-contract.md`
- `.agents/contracts/phase-21/devstack-offer-contract.md`
- `.agents/contracts/phase-21/launch-tracking-contract.md`

## Validation

```bash
ruff check .
pytest
pro-ai-server validate-release
pro-ai-server doctor
pro-ai-server install-continue-extension --ide cursor
pro-ai-server configure-continue --mode usb
pro-ai-server status
```

## Closeout Criteria

- VS Code and Cursor readiness are documented and test-covered.
- Continue config has launch-ready chat and autocomplete presets.
- Windsurf and JetBrains are follow-up support, not launch blockers.
- A simple DevStack demo script exists for screen recording and live sales calls.
- Pricing docs define trial, starter, and pro-install offers.
- Tracking parameters and launch events are specified before paid traffic or affiliate pushes.

