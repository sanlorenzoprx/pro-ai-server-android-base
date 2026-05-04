from pathlib import Path

from pro_ai_server.rag.store import IndexStore


def test_index_store_upserts_files_and_chunks(tmp_path):
    store = IndexStore(tmp_path / "index.sqlite")
    store.initialize()
    store.replace_file(
        path=Path("src/app.py"),
        language="python",
        sha256="abc",
        mtime=1.0,
        size=12,
        chunks=(("hello world", 1, 1), ("world again", 2, 2)),
    )

    status = store.status()
    assert status.file_count == 1
    assert status.chunk_count == 2
    result = store.search("world", limit=5)[0]
    assert result.path == Path("src/app.py")
    assert result.start_line == 1


def test_index_store_deletes_missing_files(tmp_path):
    store = IndexStore(tmp_path / "index.sqlite")
    store.initialize()
    store.replace_file(path=Path("gone.py"), language="python", sha256="1", mtime=1, size=1, chunks=(("gone", 1, 1),))
    store.replace_file(path=Path("keep.py"), language="python", sha256="2", mtime=1, size=1, chunks=(("keep", 1, 1),))

    deleted = store.delete_missing_files({Path("keep.py")})

    assert deleted == 1
    assert store.status().file_count == 1
    assert store.search("gone") == ()
