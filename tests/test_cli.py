from typer.testing import CliRunner

import repo_to_skill.cli as cli_module
from repo_to_skill.cli import app


runner = CliRunner()


def test_doctor_runs_and_reports_local_checks() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "repo-to-skill doctor" in result.stdout
    assert "Python version" in result.stdout
    assert "Package import" in result.stdout
    assert "Package files" in result.stdout
    assert "Project templates" not in result.stdout
    assert "README.md" not in result.stdout
    assert "examples/tiny-python-app" not in result.stdout
    assert "Network access" in result.stdout
    assert "disabled" in result.stdout


def test_doctor_does_not_require_source_tree_files(monkeypatch, tmp_path) -> None:
    installed_package = tmp_path / "site-packages" / "repo_to_skill"
    installed_package.mkdir(parents=True)
    installed_cli = installed_package / "cli.py"
    installed_cli.write_text("", encoding="utf-8")
    monkeypatch.setattr(cli_module, "__file__", str(installed_cli))

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Project templates" not in result.stdout
    assert "README.md" not in result.stdout
    assert "examples/tiny-python-app" not in result.stdout


def test_analyze_writes_expected_local_artifacts(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        """
[project]
name = "sample-app"
description = "Sample app."

[project.scripts]
sample-app = "sample.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo / "sample.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (repo / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    output = tmp_path / "run"

    result = runner.invoke(app, ["analyze", str(repo), "--output", str(output)])

    assert result.exit_code == 0
    expected = {
        "scan.json",
        "profile.json",
        "capability_evidence.json",
        "capability_graph.json",
        "skill_spec.yaml",
        "verification_report.json",
        "confidence-report.md",
        "callable_capabilities.json",
    }
    assert {path.name for path in output.iterdir()} == expected
    assert str(repo) not in (output / "confidence-report.md").read_text(encoding="utf-8")
    assert "sample-app" in (output / "skill_spec.yaml").read_text(encoding="utf-8")


def test_analyze_rejects_output_equal_to_target_repo(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    result = runner.invoke(app, ["analyze", str(repo), "--output", str(repo)])

    assert result.exit_code != 0
    assert "output must be outside target repository" in result.stdout


def test_analyze_rejects_output_inside_target_repo(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    output = repo / ".runs"

    result = runner.invoke(app, ["analyze", str(repo), "--output", str(output)])

    assert result.exit_code != 0
    assert "output must be outside target repository" in result.stdout
    assert not output.exists()
