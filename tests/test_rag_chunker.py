from pathlib import Path

from pro_ai_server.rag.chunker import chunk_text, chunk_text_by_lines, should_index_file


def test_chunk_text_is_deterministic_with_overlap():
    chunks = chunk_text("one two three four five six", max_words=3, overlap_words=1)

    assert chunks == ("one two three", "three four five", "five six")


def test_should_index_file_ignores_build_and_binary_paths(tmp_path):
    assert should_index_file(Path("src/app.py"))
    assert not should_index_file(Path(".git/config"))
    assert not should_index_file(Path(".venv/Lib/site.py"))
    assert not should_index_file(Path("dist/package.whl"))
    assert not should_index_file(Path("image.png"))


def test_chunk_text_by_lines_includes_line_ranges():
    chunks = chunk_text_by_lines("a\nb\nc\nd", max_lines=2, overlap_lines=1)

    assert [(chunk.text, chunk.start_line, chunk.end_line) for chunk in chunks] == [
        ("a\nb", 1, 2),
        ("b\nc", 2, 3),
        ("c\nd", 3, 4),
    ]
