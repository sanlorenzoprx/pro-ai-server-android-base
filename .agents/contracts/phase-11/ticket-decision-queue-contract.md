# Phase 11 Ticket Decision Queue Contract

## Commands

```powershell
pro-ai-server agent decide TKT-P10-006 --decision accepted --reason "Ready for implementation."
pro-ai-server agent decide TKT-P10-006 --decision deferred --reason "Needs product review."
pro-ai-server agent decide TKT-P10-006 --decision rejected --reason "Out of scope."
pro-ai-server agent queue
pro-ai-server agent queue --phase phase-11
```

## Decisions

Allowed decisions:

- `accepted`
- `deferred`
- `rejected`

## Storage

Default path:

```text
.agents/queue/ticket-decisions.json
```

The file records the latest decision per ticket ID in canonical JSON with sorted keys.

## Constraints

- Do not execute ticket implementation automatically.
- Do not call an LLM, GitHub, or a network service.
- Keep output deterministic and reviewable.
