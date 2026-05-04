# Phase 14: Next-Action Selector And Execution Packets

## Goal

Select the next accepted unreported ticket and render a focused execution packet for implementation agents.

## Scope

- Select one ready ticket from the accepted-ticket handoff view.
- Keep selection deterministic by phase and ticket ID order.
- Render a packet with ticket text, scope guardrails, validation commands, and report command.
- Optionally include indexed context without calling an LLM.
- Support preview and explicit write modes.

## Tickets

- `TKT-P14-001`: Next-action selector model and stable selection.
- `TKT-P14-002`: Execution packet renderer.
- `TKT-P14-003`: Execution packet writer.
- `TKT-P14-004`: `agent next-action` and `agent packet` CLI commands.
- `TKT-P14-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
