# TKT-P9-002 Report Validation Scanner

## Objective

Classify validation evidence recorded in implementation and closeout reports.

## Acceptance Criteria

- Reports with passed evidence are classified as `passed`.
- Reports with `TBD` are classified as `incomplete`.
- Reports without validation sections are classified as `missing`.
- Failed or error evidence is classified as `needs-review`.
