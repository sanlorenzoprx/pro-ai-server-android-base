# Project Memory

Pro AI Server turns an Android phone into a local AI coding server for Continue-compatible IDEs.

Current foundation:

- Python 3.11+ package with a Typer CLI and Rich console output.
- Bundled Windows ADB resolver with system ADB fallback.
- Android hardware scanning and model profile recommendations.
- Termux/Ollama setup script generation.
- Continue configuration generation with backup protection.
- USB ADB tunnel, LAN/Tailscale modes, status, diagnostics, and release validation.

Agentic Codeflow direction:

- Treat the AI layer as a second codebase.
- Use a Plan, Implement, Validate loop.
- Use the CodeFlow Build Bridge to convert phases into concrete build tickets before runtime work starts.
- Use a Research Pause before major new directions so we adapt proven external patterns before writing big tickets.
- Treat research and adaptation judgment as core product-building capabilities.
- Define endpoint, config, schema, and validation contracts before implementation.
- Store plans, reports, mistakes, and rules in version control.
- Prefer small, tested runtime changes staged by phase.
- Preserve existing CLI behavior while adding gateway, RAG, and agent workflows.

Official product name for this clone:

- Pro CodeFlow Server

Philosophy:

- We are building a product and an adaptable build platform at the same time.
- The project should teach us how to build the next layer with better judgment.
- The ability to adopt, adapt, or discard outside work is part of the core craft here.

Build bridge rule:

- No major runtime implementation begins until a matching build ticket and any required contracts exist in `.agents/`.
- No major new direction should skip `docs/RESEARCH_PAUSE_SOP.md` when similar external work likely exists.

Default validation:

```bash
ruff check .
pytest
pro-ai-server validate-release
```
