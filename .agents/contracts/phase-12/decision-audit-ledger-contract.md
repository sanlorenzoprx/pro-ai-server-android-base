# Phase 12 Decision Audit Ledger Contract

## Commands

```powershell
pro-ai-server agent decide TKT-P11-001 --decision deferred --reason "Needs review."
pro-ai-server agent history
pro-ai-server agent queue
```

## Files

Current-state queue:

```text
.agents/queue/ticket-decisions.json
```

Append-only history:

```text
.agents/queue/ticket-decisions.jsonl
```

## Rules

- Each `agent decide` call appends one JSONL event.
- Current-state JSON is derived from the latest event per ticket.
- Event order is deterministic by sequence number.
- No timestamps, LLM calls, GitHub calls, or network services are required.
