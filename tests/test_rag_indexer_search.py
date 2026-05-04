from pathlib import Path

from pro_ai_server.rag.context import build_context
from pro_ai_server.rag.indexer import index_project
from pro_ai_server.rag.search import search_index
from pro_ai_server.rag.store import IndexStore


def test_index_project_indexes_searchable_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "gateway.py").write_text("continue config gateway support", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "ignored.txt").write_text("gateway hidden", encoding="utf-8")
    db_path = tmp_path / ".pro-ai-server" / "index.sqlite"

    result = index_project(tmp_path, db_path=db_path)

    assert result.file_count == 1
    assert result.chunk_count == 1
    matches = search_index("gateway", db_path=db_path)
    assert matches[0].path == Path("src/gateway.py")
    assert matches[0].start_line == 1


def test_index_project_reconciles_deleted_files(tmp_path):
    (tmp_path / "src").mkdir()
    indexed = tmp_path / "src" / "gateway.py"
    indexed.write_text("gateway support", encoding="utf-8")
    db_path = tmp_path / ".pro-ai-server" / "index.sqlite"
    index_project(tmp_path, db_path=db_path)
    indexed.unlink()

    result = index_project(tmp_path, db_path=db_path)

    assert result.file_count == 0
    assert search_index("gateway", db_path=db_path) == ()


def test_build_context_includes_project_memory_and_snippets(tmp_path):
    store = IndexStore(tmp_path / "index.sqlite")
    store.initialize()
    store.replace_file(
        path=Path("README.md"),
        language="markdown",
        sha256="abc",
        mtime=1,
        size=20,
        chunks=(("gateway support docs", 3, 4),),
    )

    context = build_context("gateway", db_path=tmp_path / "index.sqlite", project_summary="Project summary")

    assert "Project summary" in context
    assert "README.md:3-4 chunk 0" in context
    assert "gateway support docs" in context
