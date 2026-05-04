# Contract: Agent Plan Generation

## Command

```bash
pro-ai-server agent plan "add route-test endpoint"
```

## Output

```text
.agents/plans/{slug}.plan.md
```

## Rules

- Plan generation does not call an LLM.
- Output is a deterministic draft.
- Plan includes summary, user story, context, files to change, tasks, validation, acceptance criteria, and rollback plan.
- The draft must be explicit that implementation should not start until the plan is reviewed.

