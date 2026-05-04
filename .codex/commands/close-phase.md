# Close Phase

Use this after all build tickets for a phase are implemented.

Read:

- `.agents/phase-plans/{phase}.md`
- `.agents/build-tickets/{phase}/`
- `.agents/contracts/{phase}/`
- `.agents/reports/`
- `.agents/runbooks/phase-closeout.md`

Run or verify:

```bash
ruff check .
pytest
pro-ai-server validate-release
```

For gateway phases, also verify:

```bash
pro-ai-server gateway-route-test --task chat
curl http://localhost:8765/health
```

Output:

```text
.agents/reports/{phase}-closeout-report.md
```

The closeout report must include:

- completed tickets
- validation evidence
- contract changes
- smoke-test result
- mistake records or rule updates
- known risks
- next phase recommendation

Do not mark a phase complete if validation evidence is missing.

