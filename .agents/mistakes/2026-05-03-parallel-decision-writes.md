# Mistake: Parallel Writes To Decision Queue

## Date

2026-05-03

## Context

Phase 11 added `pro-ai-server agent decide`, which writes `.agents/queue/ticket-decisions.json`.

## Failure

I initially dogfooded multiple `agent decide` writes in parallel against the same JSON file.

## Root Cause

Parallel writes to the same state file can race and lose updates because each process reads, modifies, and writes the full file.

## Fix Applied

I re-recorded the Phase 11 decisions sequentially and verified the final queue contains all five decisions.

## System Improvement

State-file writes should be treated as serialized operations unless the module implements explicit locking or append-only semantics.

## Prevent Next Time

Do not run parallel CLI commands that write the same local state file; use sequential execution for `.agents/queue` updates.
