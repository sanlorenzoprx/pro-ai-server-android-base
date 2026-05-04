from pathlib import Path

from pro_ai_server.agent.context import build_agent_context
from pro_ai_server.rag.store import IndexStore


def test_build_agent_context_includes_memory_and_index_results(tmp_path):
    db = tmp_path / "index.sqlite"
    store = IndexStore(db)
    store.initialize()
    store.replace_file(
        path=Path("src/app.py"),
        language="python",
        sha256="abc",
        mtime=1,
        size=10,
        chunks=(("gateway context", 2, 3),),
    )
    memory = tmp_path / ".agents" / "memory" / "project-memory.md"
    memory.parent.mkdir(parents=True)
    memory.write_text("Memory summary", encoding="utf-8")

    context = build_agent_context("gateway", root=tmp_path, db_path=db)

    assert "Memory summary" in context
    assert "src/app.py:2-3 chunk 0" in context
    assert "gateway context" in context


def test_build_agent_context_handles_missing_index(tmp_path):
    context = build_agent_context("gateway", root=tmp_path, db_path=tmp_path / "missing" / "index.sqlite")

    assert "No indexed context found" in context
