# Phase 16: Session-Aware Next Action Selection

## Goal

Use work-session state to choose the next accepted unreported ticket before implementation reports exist.

## Scope

- Join ready handoff tickets with current work-session state.
- Skip finished session tickets by default.
- Support a resume policy that prioritizes picked-up or started tickets.
- Support an all policy for audit/recovery selection.
- Apply the same policy to next-action and packet generation commands.

## Tickets

- `TKT-P16-001`: Session-aware selector policy.
- `TKT-P16-002`: Session state in next-action rendering.
- `TKT-P16-003`: Session-aware packet generation.
- `TKT-P16-004`: CLI session policy options.
- `TKT-P16-005`: Docs, tests, and closeout.

## Validation

```powershell
ruff check .
pytest
pro-ai-server validate-release
```
