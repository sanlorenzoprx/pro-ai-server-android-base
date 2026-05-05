# Agent Workflows

Phase 6 adds agent-ready context commands.

## DevStack Launch IDE Readiness

Phase 21 launch support is intentionally narrow:

- Launch IDEs: VS Code (`code`) and Cursor (`cursor`)
- Follow-up IDEs: Windsurf and JetBrains

Check the launch matrix:

```powershell
pro-ai-server devstack-ide-status
```

Ready means the IDE CLI is installed and the Continue extension is present. If Continue is missing, install it with:

```powershell
pro-ai-server install-continue-extension --ide code
pro-ai-server install-continue-extension --ide cursor
```

After an IDE is ready, write the USB Continue config:

```powershell
pro-ai-server configure-continue --mode usb
```

## Prime

```powershell
pro-ai-server agent prime
```

Writes:

```text
.agents/memory/last-prime.md
```

The report includes git branch, status, recent commits, diff stat, index status, validation commands, and risks.

## Context

```powershell
pro-ai-server agent context "add gateway support"
```

The command combines project memory from `.agents/memory/project-memory.md` with line-aware snippets from the local code index.

Run `pro-ai-server index .` first for best results.

## Plan

```powershell
pro-ai-server agent plan "add gateway route support"
pro-ai-server agent plan "add gateway route support" --slug gateway-route-support
```

Writes:

```text
.agents/plans/add-gateway-route-support.plan.md
```

The generated plan is a deterministic draft built from project memory, the last prime report, and indexed context. It does not call an LLM and should be reviewed before implementation.

## Report

```powershell
pro-ai-server agent report TKT-P8-001 --summary "Implemented ticket status tracking."
pro-ai-server agent report TKT-P8-001 --summary "Implemented ticket status tracking." --file-updated src/pro_ai_server/cli.py --validation "pytest tests/test_agent_reporter.py"
```

Writes:

```text
.agents/reports/TKT-P8-001-report.md
```

The generated report records summary, ticket reference, changed files, validation evidence, deviations, and follow-up notes. It is deterministic and does not call an LLM.

## Status

```powershell
pro-ai-server agent status
pro-ai-server agent status --phase phase-8
```

The command scans `.agents/build-tickets/**/*.md` and `.agents/reports/*.md`, then prints ticket counts and a status table. Tickets with matching reports are `reported`, tickets without reports are `planned`, and report files without matching tickets are `orphan-report`.

## Improve

```powershell
pro-ai-server agent improve
pro-ai-server agent improve --phase phase-9
pro-ai-server agent improve --write
```

The command reviews ticket status, report validation evidence, and mistake records, then prints deterministic process recommendations. With `--write`, it writes:

```text
.agents/reports/self-improvement-review.md
```

This is a local self-correction loop. It does not call an LLM; it turns existing project evidence into a review agents can act on before the next phase.

## Ticketize

```powershell
pro-ai-server agent ticketize --accept "validation"
pro-ai-server agent ticketize --all
pro-ai-server agent ticketize --all --write
```

The command reads `.agents/reports/self-improvement-review.md` and turns accepted recommendations into deterministic build-ticket drafts. Preview is the default; tickets are written only with `--write`.

Written tickets go under:

```text
.agents/build-tickets/{phase}/
```

Use `--phase`, `--ticket-prefix`, and `--start` when drafting tickets for a future phase. Existing ticket files are protected unless `--force` is passed.

## Decide And Queue

```powershell
pro-ai-server agent decide TKT-P10-006 --decision accepted --reason "Ready for implementation."
pro-ai-server agent decide TKT-P10-006 --decision deferred --reason "Needs product review."
pro-ai-server agent queue
pro-ai-server agent queue --phase phase-11
```

Decisions are stored locally in:

```text
.agents/queue/ticket-decisions.json
```

Allowed decisions are `accepted`, `deferred`, and `rejected`. The queue records current decision state only; it does not execute implementation work or call external services.

## Decision History

```powershell
pro-ai-server agent history
```

Each `agent decide` call also appends one event to:

```text
.agents/queue/ticket-decisions.jsonl
```

The JSON queue remains the latest current-state view, while the JSONL file preserves decision history. This is still a single-writer local workflow; do not run parallel commands that write the same queue files.

## Handoff

```powershell
pro-ai-server agent handoff
pro-ai-server agent handoff --phase phase-13
pro-ai-server agent handoff --ticket TKT-P13-001
pro-ai-server agent handoff --include-reported
```

The command shows accepted tickets that are ready for implementation. By default, tickets that already have implementation reports are hidden. Use `--include-reported` for review/audit handoffs.

## Next Action And Packet

```powershell
pro-ai-server agent next-action
pro-ai-server agent next-action --phase phase-14
pro-ai-server agent packet
pro-ai-server agent packet --phase phase-14
pro-ai-server agent packet --phase phase-14 --context
pro-ai-server agent packet --phase phase-14 --write
```

`agent next-action` selects the first accepted unreported ticket from the handoff view by stable phase and ticket ID order. `agent packet` renders a focused execution packet with ticket text, scope guardrails, validation commands, and the completion report command. Preview is the default; `--write` writes:

```text
.agents/execution/{ticket}.execution.md
```

Use `--context` to include local indexed context for the selected ticket. The packet workflow is deterministic and does not call an LLM.

Selection is session-aware when work sessions exist:

```powershell
pro-ai-server agent next-action --session-policy available
pro-ai-server agent next-action --session-policy resume
pro-ai-server agent next-action --session-policy all
pro-ai-server agent packet --session-policy resume
```

`available` is the default: finished session tickets are skipped and tickets with no session are preferred. `resume` prioritizes picked-up or started tickets. `all` includes finished session tickets for audit or recovery. Reports still close tickets; session state only affects selection while a ticket is unreported.

## Work Sessions

```powershell
pro-ai-server agent session TKT-P15-001 --event picked-up --note "Taking it."
pro-ai-server agent session TKT-P15-001 --event started --note "Working."
pro-ai-server agent session TKT-P15-001 --event finished --note "Ready for report."
pro-ai-server agent sessions
pro-ai-server agent sessions --phase phase-15
pro-ai-server agent session-history
```

Session tracking records packet consumption and work progress separately from implementation reports. Events append to:

```text
.agents/execution/work-sessions.jsonl
```

The latest event per ticket is also written to:

```text
.agents/execution/work-sessions.json
```

Valid events are `picked-up`, `started`, and `finished`; the CLI also accepts `pickup`, `start`, and `finish` aliases. This workflow does not create reports, so use `pro-ai-server agent report` after implementation and validation are complete.

## Reconcile Sessions And Reports

```powershell
pro-ai-server agent reconcile
pro-ai-server agent reconcile --phase phase-17
pro-ai-server agent reconcile --ticket TKT-P17-001
pro-ai-server agent reconcile --fail-on-warning
```

Reconciliation joins current work sessions, ticket files, and implementation reports. It warns when active sessions already have reports, finished sessions are missing reports, finished sessions still linger after reports exist, or sessions reference missing ticket files. Use `--fail-on-warning` as an autopilot preflight gate.

## Archive Finished Sessions

```powershell
pro-ai-server agent session-archive
pro-ai-server agent session-archive --phase phase-19
pro-ai-server agent session-archive --ticket TKT-P19-001
pro-ai-server agent session-archive --phase phase-19 --write
```

Session archive removes finished reported sessions from current autopilot state while preserving the append-only work-session history. Preview is the default. With `--write`, archive records append to:

```text
.agents/execution/archived-work-sessions.jsonl
```

Only `finished-session-reported` reconciliation warnings are archive candidates. Finished unreported sessions still need reports, and active reported sessions still need session reconciliation before archive.

## Autopilot

```powershell
pro-ai-server agent autopilot --phase phase-18
pro-ai-server agent autopilot --phase phase-18 --execute
pro-ai-server agent autopilot --phase phase-18 --execute --start-session
pro-ai-server agent autopilot --phase phase-18 --fail-on-stop
```

Autopilot runs one controlled tick. It reconciles sessions and reports, selects the next ready ticket with session-aware policy, and shows validation and report gates. Preview is the default and writes nothing. With `--execute`, it writes one execution packet; with `--start-session`, it also records `picked-up` and `started`.

Autopilot stops after packet/session setup. Implementation, validation, and `agent report` remain explicit gates. Reconciliation warnings stop autopilot before any writes, and active picked-up or started sessions stop default autopilot before another ticket is selected. Use `--session-policy resume` when intentionally continuing active work.
