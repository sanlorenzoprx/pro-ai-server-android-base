# TKT-P14-004 Agent Packet CLI

## Objective

Expose next-action selection and packet generation through agent CLI commands.

## Acceptance Criteria

- `agent next-action` prints the selected ready ticket or idle state.
- `agent packet` previews the execution packet.
- `agent packet --write` writes the packet.
- `agent packet --context` includes indexed context when requested.
