# Validate

Run all checks and report results.

Default commands:

```bash
ruff check .
pytest
pro-ai-server validate-release
python -m pip wheel . --no-deps --wheel-dir dist
```

Report format:

```md
# Validation Report

| Check | Result | Notes |
|---|---|---|
| Ruff | pass/fail | |
| Pytest | pass/fail | |
| Release validation | pass/fail | |
| Wheel build | pass/fail | |

## Failures

List file, line, error, and likely fix.
```

