from repo_to_skill.scanner.filesystem import scan_repository


def test_scan_repository_records_relative_files_and_hashes(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (repo / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    (repo / "id_rsa").write_text("private\n", encoding="utf-8")
    (repo / "large.txt").write_text("x" * (1024 * 1024 + 1), encoding="utf-8")
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02")

    result = scan_repository(repo)

    paths = [record.path for record in result.files]
    assert paths == ["app.py"]
    record = result.files[0]
    assert record.size == len("print('hello')\n")
    assert record.line_count == 1
    assert len(record.sha256) == 64
    assert record.language == "Python"
    assert record.role == "source"
    assert ".env" in result.skipped
    assert "id_rsa" in result.skipped
    assert "large.txt" in result.skipped
    assert "binary.bin" in result.skipped


def test_scan_repository_skips_symlink_to_file_outside_repo(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside-secret.py"
    outside.write_text("print('do not scan')\n", encoding="utf-8")
    (repo / "linked.py").symlink_to(outside)

    result = scan_repository(repo)

    assert [record.path for record in result.files] == []
    assert "linked.py: symlink" in result.skipped


def test_scan_repository_skips_local_run_artifacts(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    runs = repo / ".runs" / "previous"
    runs.mkdir(parents=True)
    (runs / "scan.json").write_text("{}\n", encoding="utf-8")

    result = scan_repository(repo)

    assert [record.path for record in result.files] == ["app.py"]
    assert ".runs/previous/scan.json" in result.skipped


def test_scan_repository_skips_generated_graph_cache(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "Program.cs").write_text("class Program {}\n", encoding="utf-8")
    cache = repo / "graphify-out" / "cache" / "ast"
    cache.mkdir(parents=True)
    (cache / "node.json").write_text('{"generated": true}\n', encoding="utf-8")
    artifacts = repo / "Build" / "Artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "bundle.txt").write_text("generated\n", encoding="utf-8")

    result = scan_repository(repo)

    assert [record.path for record in result.files] == ["Program.cs"]
    assert "graphify-out/cache/ast/node.json" in result.skipped
    assert "Build/Artifacts/bundle.txt" in result.skipped
