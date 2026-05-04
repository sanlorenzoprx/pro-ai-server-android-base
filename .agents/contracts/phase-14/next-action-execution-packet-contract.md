# Phase 14 Next-Action Execution Packet Contract

## Commands

```powershell
pro-ai-server agent next-action
pro-ai-server agent next-action --phase phase-14
pro-ai-server agent packet
pro-ai-server agent packet --phase phase-14
pro-ai-server agent packet --phase phase-14 --context
pro-ai-server agent packet --phase phase-14 --write
```

## Inputs

- Tickets from `.agents/build-tickets/**/*.md`.
- Decisions from `.agents/queue/ticket-decisions.json`.
- Reports from `.agents/reports/*.md`.
- Optional indexed context from the local code index.

## Rules

- Only accepted tickets without implementation reports are eligible.
- Selection uses the first ready handoff item after stable phase and ticket ID sorting.
- Packet rendering does not call an LLM.
- Packet writes are explicit and go under `.agents/execution/` by default.
- The packet includes validation commands and a completion report command.
