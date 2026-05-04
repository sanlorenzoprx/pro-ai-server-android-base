# Phase Closeout Runbook

Use this before declaring any phase complete.

## Checklist

- Phase plan exists.
- Build tickets exist and are complete.
- Required contracts exist.
- Implementation reports exist.
- Validation evidence is recorded.
- Smoke test passed or documented as not applicable.
- Mistake records exist for preventable failures.
- Rules, commands, or memory were updated when failures showed a system gap.
- README or docs changed if user-facing behavior changed.
- Follow-up phase tickets are identified.

## Closeout Report

Create:

```text
.agents/reports/{phase}-closeout-report.md
```

Include:

- completed tickets
- final validation results
- known risks
- contract changes
- unresolved follow-ups
- next phase recommendation

