from __future__ import annotations

from pathlib import Path

import tomllib
from typer.testing import CliRunner

from repo_to_skill.cli import app
from repo_to_skill.evals import runner as eval_runner


runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_eval_tiny_python_case_runs_full_local_flow() -> None:
    result = runner.invoke(app, ["eval", "--case", "tiny-python"])

    assert result.exit_code == 0, result.stdout
    assert "Eval case: tiny-python" in result.stdout
    assert "analyze artifacts: PASS" in result.stdout
    assert "generated skill shape: PASS" in result.stdout
    assert "validation: PASS" in result.stdout
    assert "python signals: PASS" in result.stdout
    assert "machine path leaks: PASS" in result.stdout
    assert "Eval result: PASS" in result.stdout


def test_eval_unknown_case_fails_with_readable_message() -> None:
    result = runner.invoke(app, ["eval", "--case", "missing-case"])

    assert result.exit_code != 0
    assert "unknown eval case: missing-case" in result.stdout
    assert "tiny-python" in result.stdout


def test_available_cases_uses_packaged_resources_when_source_cases_are_missing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(eval_runner, "repository_root", lambda: tmp_path)

    assert "tiny-python" in eval_runner.available_cases()


def test_eval_uses_packaged_fixture_when_source_examples_are_missing(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(eval_runner, "repository_root", lambda: tmp_path)

    result = runner.invoke(app, ["eval", "--case", "tiny-python"])

    assert result.exit_code == 0, result.stdout
    assert "Eval result: PASS" in result.stdout


def test_packaged_resources_are_included_in_wheel_build_config() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    package_data = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["artifacts"]

    assert "repo_to_skill/resources/**" in package_data


def test_eval_malformed_case_missing_fixture_fails_readably(monkeypatch) -> None:
    monkeypatch.setattr(eval_runner, "_read_case_text", lambda case_name: "expect: {}\n")

    result = runner.invoke(app, ["eval", "--case", "broken-case"])

    assert result.exit_code != 0
    assert "invalid eval case: broken-case: missing required field fixture" in result.stdout
    assert "Traceback" not in result.stdout
    assert "KeyError" not in result.stdout


def test_eval_workspace_inside_fixture_fails_without_creating_directory(tmp_path: Path) -> None:
    fixture_root = REPO_ROOT / "examples" / "tiny-python-app"
    workspace = fixture_root / "eval-workspace-inside"

    assert not workspace.exists()
    result = runner.invoke(app, ["eval", "--case", "tiny-python", "--workspace", str(workspace)])

    assert result.exit_code != 0
    assert "workspace must be outside eval fixture repository" in result.stdout
    assert not workspace.exists()
