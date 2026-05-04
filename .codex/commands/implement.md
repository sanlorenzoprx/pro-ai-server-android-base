# Implement

Implement an approved plan.

Rules:

- Read the plan.
- Check git status.
- Create a branch if on main and clean.
- Implement one task at a time.
- Validate after every task.
- Do not proceed while checks are failing.
- Write tests for new behavior.
- Write an implementation report.

Default validation:

```bash
ruff check .
pytest
pro-ai-server validate-release
```

Output:

```text
.agents/reports/{feature}-report.md
```

