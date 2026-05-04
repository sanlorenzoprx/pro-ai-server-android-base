# Contract: RAG Index

## Storage

Default path:

```text
.pro-ai-server/index.sqlite
```

## Tables

- `files`: path, language, sha256, mtime, size
- `chunks`: file path, chunk index, text

## CLI

```bash
pro-ai-server index .
pro-ai-server index-status
pro-ai-server search "continue config"
pro-ai-server context "add gateway support"
```

## Rules

- Ignore `.git`, `.venv`, caches, build artifacts, dist artifacts, and binary files.
- Search is keyword-based in Phase 4.
- Output must be deterministic.

