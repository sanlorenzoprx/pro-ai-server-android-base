# Contract: Gateway Validation

## Phase

Phase 1: Gateway Skeleton

## Purpose

Define the minimum evidence needed before Phase 1 can close.

## Required Automated Checks

```bash
ruff check .
pytest
pro-ai-server validate-release
```

## Required Gateway Checks

After the gateway exists:

```bash
pro-ai-server gateway-route-test --task chat
curl http://localhost:8765/health
```

## Required Reports

- `.agents/reports/phase-1-gateway-skeleton-report.md`
- Any mistake records for preventable failures
- Updated contracts if implementation drifts

## Closeout Rule

Phase 1 cannot close while any build ticket is incomplete or validation evidence is missing.

