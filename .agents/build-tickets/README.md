# Build Tickets

Build tickets are concrete implementation units generated from phase plans.

They are the bridge between AI-layer planning and runtime code changes.

Rules:

- One ticket should be small enough to implement and validate independently.
- Each ticket must name expected files, dependencies, contracts, validation, rollback, and definition of done.
- Runtime implementation should reference the active build ticket in the implementation report.
- If code drifts from a contract, file a follow-up ticket or update the contract explicitly.

