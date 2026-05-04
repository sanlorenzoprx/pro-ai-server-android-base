# Phase 1 Gateway Smoke Test

Run this after the gateway skeleton exists.

## Preconditions

- Phase 1 tickets TKT-P1-001 through TKT-P1-007 are complete.
- Gateway dependencies are installed.
- Default validation passes.

## Steps

1. Start the gateway:

   ```bash
   pro-ai-server gateway-start
   ```

2. Check health:

   ```bash
   curl http://localhost:8765/health
   ```

3. Check model route metadata:

   ```bash
   curl http://localhost:8765/models
   ```

4. Check route testing:

   ```bash
   pro-ai-server gateway-route-test --task chat
   pro-ai-server gateway-route-test --task autocomplete
   pro-ai-server gateway-route-test --task unknown
   ```

5. Record results in `.agents/reports/phase-1-gateway-skeleton-report.md`.

## Pass Criteria

- Health returns `status: ok`.
- Models response includes configured route metadata.
- Route test selects documented routes.
- Unknown task falls back safely to chat.
- No existing MVP CLI command regresses.

