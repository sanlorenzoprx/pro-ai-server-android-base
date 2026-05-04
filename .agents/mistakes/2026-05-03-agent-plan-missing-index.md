# Mistake: Agent Plan Failed Without Index

## Date

2026-05-03

## Context

Phase 7 added `pro-ai-server agent plan`.

## Failure

Focused validation showed that plan generation failed when the default index database directory did not exist.

## Root Cause

The agent context builder delegated directly to indexed search and did not handle a missing index database.

## Fix Applied

`build_agent_context` now catches unavailable index errors and returns deterministic Markdown that tells the user to run `pro-ai-server index .`.

## System Improvement

Agent workflow commands should produce useful drafts before all optional local context exists.

## Prevent Next Time

For new agent workflow commands, add tests for missing optional memory/index inputs.

