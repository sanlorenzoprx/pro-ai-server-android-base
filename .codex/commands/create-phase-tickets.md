# Create Phase Tickets

Convert a phase plan into concrete build tickets.

Usage:

```text
/create-phase-tickets Phase 1
```

Read:

- `.agents/phase-plans/{phase}.md`
- `.agents/PRDs/`
- `.agents/memory/project-memory.md`
- `.agents/workflows/codeflow-build-bridge.md`
- relevant source files and docs

Output:

```text
.agents/build-tickets/{phase}/TKT-*.md
.agents/contracts/{phase}/*.md
```

Rules:

1. No major implementation begins until phase tickets exist.
2. Each ticket must be independently implementable and testable.
3. Each ticket must name expected files, dependencies, validation, rollback, and definition of done.
4. Contract-impacting tickets must reference contract files.
5. The final ticket should cover docs, smoke test, and implementation report.

Ticket template:

```text
.agents/build-tickets/_template.md
```

Stop after creating tickets and contracts. Do not implement runtime code.

