# Code Index

The code index is the Phase 4 foundation for local RAG.

It uses stdlib SQLite and deterministic keyword search. Embeddings and semantic ranking are intentionally deferred.

## Commands

```powershell
pro-ai-server index .
pro-ai-server index-status
pro-ai-server search "continue config"
pro-ai-server context "add gateway support"
```

Default database:

```text
.pro-ai-server/index.sqlite
```

## Indexed Files

The index includes text-like project files such as Python, Markdown, TOML, YAML, JSON, PowerShell, shell, and text files.

Ignored by default:

- `.git`
- `.venv`
- `__pycache__`
- `.pytest_cache`
- `.ruff_cache`
- `build`
- `dist`
- `node_modules`
- common binary extensions

## Limitations

- Search is lexical keyword search.
- Chunks are line-aware but not AST-aware yet.
- No embeddings are generated.
- No background watcher exists yet.
- Re-indexing reconciles deleted files from the index.

## Context Format

`pro-ai-server context` emits stable Markdown blocks:

```text
## src/example.py:12-38 chunk 0
...
---
```

The line range helps agents cite and inspect the source quickly.
