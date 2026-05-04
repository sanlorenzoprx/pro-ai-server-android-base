# Plan -> Implement -> Validate Loop

## Plan

- Load project context.
- Read relevant files.
- Study existing patterns.
- Create a plan.
- Do not write code.

## Implement

- Start from an approved plan.
- Work one task at a time.
- Validate after each task.
- Do not accumulate broken state.

## Validate

Run:

```bash
ruff check .
pytest
pro-ai-server validate-release
```

Add extra checks for the feature being changed.

## Report

Write an implementation report in `.agents/reports/`.

## Improve

If failures happened, update `.agents/mistakes/` and propose rule improvements.

