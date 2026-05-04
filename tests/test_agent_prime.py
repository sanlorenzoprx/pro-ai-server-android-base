from pro_ai_server.agent.prime import build_prime_report, write_prime_report


def test_build_prime_report_includes_git_and_index_status():
    commands = {
        ("git", "branch", "--show-current"): "main",
        ("git", "status", "--short"): " M README.md",
        ("git", "log", "--oneline", "-n", "20"): "abc first",
        ("git", "diff", "--stat"): "README.md | 1 +",
    }

    def runner(command):
        return commands[tuple(command)]

    report = build_prime_report(command_runner=runner, index_file_count=2, index_chunk_count=3)

    assert "# Agent Prime" in report
    assert "Branch: main" in report
    assert "M README.md" in report
    assert "abc first" in report
    assert "Indexed files: 2" in report
    assert "pytest" in report


def test_write_prime_report_creates_memory_file(tmp_path):
    path = write_prime_report("prime", root=tmp_path)

    assert path == tmp_path / ".agents" / "memory" / "last-prime.md"
    assert path.read_text(encoding="utf-8") == "prime"
