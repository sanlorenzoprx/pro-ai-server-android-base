# TKT-P10-001 Recommendation Extraction

## Objective

Extract recommendations from self-improvement review markdown and select accepted items.

## Acceptance Criteria

- Recommendations are read from the `## Recommendations` section.
- Repeatable `--accept` values can match exact or partial recommendation text.
- `--all` selects all recommendations.
- Empty selections produce a safe preview.
