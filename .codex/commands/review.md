# Review

Review changes before merge.

Prioritize:

- behavioral regressions
- missing tests
- broken CLI compatibility
- unsafe device/network behavior
- weak validation
- unclear docs

Review process:

1. Inspect `git diff --stat`.
2. Inspect changed files.
3. Compare changes to the approved plan.
4. Run or verify validation.
5. Report findings by severity with file references.

