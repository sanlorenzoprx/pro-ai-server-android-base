# CodeFlow Build Bridge

The CodeFlow Build Bridge turns a large product phase into enforceable implementation work.

It sits between project vision and code changes:

```text
roadmap / PRD
-> phase plan
-> build-ticket register
-> contracts
-> one-ticket implementation
-> validation evidence
-> report
-> closeout
```

## Purpose

- Prevent vague phase work from turning into oversized implementation.
- Keep runtime changes tied to explicit tickets.
- Define endpoint, config, schema, and validation contracts before code.
- Return validation evidence to `.agents/reports/`.
- Feed mistakes back into rules and memory.

## Rules

1. No major runtime work begins without a matching build ticket.
2. Each build ticket names target files, dependencies, validation, and rollback.
3. Contract-impacting work must reference `.agents/contracts/`.
4. One branch or PR should map to one build ticket when practical.
5. Validation evidence must be recorded before a ticket is considered done.
6. Phase closeout happens only after all tickets, contracts, reports, and smoke tests are complete.

## Pro CodeFlow Server Adaptation

For Pro CodeFlow Server, contracts usually describe:

- gateway endpoints
- model routing behavior
- CLI command behavior
- local config shape
- index/RAG storage shape
- agent report formats
- network exposure and privacy boundaries

