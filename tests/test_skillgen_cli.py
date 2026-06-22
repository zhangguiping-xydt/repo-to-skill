from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from repo_to_skill.cli import app
from repo_to_skill.skillgen.planner import SkillPlan
from repo_to_skill.skillgen.renderer import render_skill
from repo_to_skill.skillgen.validator import validate_skill


runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_REPO = REPO_ROOT / "examples" / "tiny-python-app"


EXPECTED_SKILL_FILES = {
    "manifest.yaml",
    "SKILL.md",
    "scripts/inspect_repo.py",
    "scripts/common.py",
    "references/project-map.md",
    "references/capability-graph.md",
    "references/skill-spec.md",
    "references/confidence-report.md",
}


def _relative_files(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def _combined_text(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file())


def _analysis_run(tmp_path: Path) -> Path:
    analysis = tmp_path / "analysis-run"
    result = runner.invoke(app, ["analyze", str(EXAMPLE_REPO), "--output", str(analysis)])
    assert result.exit_code == 0, result.stdout
    return analysis


def _analysis_without(tmp_path: Path, artifact_name: str) -> Path:
    analysis = tmp_path / f"analysis-without-{artifact_name}"
    shutil.copytree(_analysis_run(tmp_path), analysis)
    (analysis / artifact_name).unlink()
    return analysis


def _generated_skill(tmp_path: Path) -> Path:
    output = tmp_path / "tiny-python-skill"
    generate_result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(_analysis_run(tmp_path)), "--output", str(output)],
    )
    assert generate_result.exit_code == 0, generate_result.stdout
    return output


def _enterprise_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "enterprise-repo"
    repo.mkdir()
    (repo / "TMS.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    web = repo / "Web"
    web.mkdir()
    (web / "Default.aspx").write_text("<%@ Page Language=\"C#\" %>\n", encoding="utf-8")
    (web / "Service.asmx").write_text("<%@ WebService Language=\"C#\" %>\n", encoding="utf-8")
    (web / "Default.aspx.cs").write_text("public class DefaultPage {}\n", encoding="utf-8")
    db = repo / "DB"
    db.mkdir()
    (db / "schema.sql").write_text("create table Users (Id int);\n", encoding="utf-8")
    (db / "proc.prc").write_text("procedure body\n", encoding="utf-8")
    attendance = repo / "Attendance"
    attendance.mkdir()
    (attendance / "Main.pas").write_text("unit Main;\n", encoding="utf-8")
    right_data_server = repo / "RightDataServer"
    right_data_server.mkdir()
    (right_data_server / "RightDataServer.csproj").write_text("<Project />\n", encoding="utf-8")
    build = repo / "Build"
    build.mkdir()
    (build / "Deploy.bat").write_text("msbuild TMS.sln\n", encoding="utf-8")
    artifacts = build / "Artifacts"
    artifacts.mkdir()
    (artifacts / "bundle.txt").write_text("generated\n", encoding="utf-8")
    pipeline = repo / "PIPELINE"
    pipeline.mkdir()
    (pipeline / "userconfig.yml").write_text("steps: []\n", encoding="utf-8")
    module = repo / "TMS_CN001_CommonFramework"
    module.mkdir()
    for index in range(55):
        (module / f"Common{index}.cs").write_text(f"public class Common{index} {{}}\n", encoding="utf-8")
    (repo / "Release_TMS.bat").write_text("msbuild TMS.sln\n", encoding="utf-8")
    cache = repo / "graphify-out" / "cache" / "ast"
    cache.mkdir(parents=True)
    (cache / "node.json").write_text('{"generated": true}\n', encoding="utf-8")
    return repo


def _generated_enterprise_skill(tmp_path: Path) -> Path:
    repo = _enterprise_repo(tmp_path)
    output = tmp_path / "enterprise-skill"
    workdir = tmp_path / "enterprise-analysis"
    result = runner.invoke(app, ["compose", str(repo), "--workdir", str(workdir), "--output", str(output)])
    assert result.exit_code == 0, result.stdout
    return output


def test_generate_from_tiny_python_analysis_writes_complete_skill_shape(tmp_path) -> None:
    output = tmp_path / "tiny-python-skill"

    result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(_analysis_run(tmp_path)), "--output", str(output)],
    )

    assert result.exit_code == 0, result.stdout
    assert EXPECTED_SKILL_FILES.issubset(_relative_files(output))
    assert "Validation: PASS" in result.stdout
    assert str(output) in result.stdout


def test_generated_skill_has_actionable_summary_and_stable_capability_labels(tmp_path) -> None:
    output = _generated_skill(tmp_path)

    skill = (output / "SKILL.md").read_text(encoding="utf-8")
    skill_spec = (output / "references" / "skill-spec.md").read_text(encoding="utf-8")
    confidence_report = (output / "references" / "confidence-report.md").read_text(encoding="utf-8")

    assert "## At a glance" in skill
    assert "Primary language: Python" in skill
    assert "Entrypoints: tiny-app = tiny_app.cli:main" in skill
    assert "Test commands: python -m pytest" in skill
    assert "Key paths:" in skill
    assert "`cli` — CLI" in skill
    assert "`package_manager` — package manager" in skill
    assert "`test` — tests" in skill
    assert "`package_manager` — package manager" in skill_spec
    assert "- CLI:" in confidence_report
    assert "- package manager:" in confidence_report
    assert "- package_manager:" not in confidence_report


def test_generated_enterprise_skill_highlights_real_capabilities_and_summarizes_paths(tmp_path) -> None:
    output = _generated_enterprise_skill(tmp_path)

    skill = (output / "SKILL.md").read_text(encoding="utf-8")
    project_map = (output / "references" / "project-map.md").read_text(encoding="utf-8")
    confidence_report = (output / "references" / "confidence-report.md").read_text(encoding="utf-8")
    combined = _combined_text(output)

    assert "Primary language: C#" in skill
    assert "## Repository intelligence" in skill
    assert "Web/ — ASP.NET web application surface" in skill
    assert "Signals: aspnet-web" in skill
    assert "Representative paths:" in skill
    assert "## Repository reasoning" in skill
    assert "Task entry guide" in skill
    assert "Validation guide" in skill
    assert "builds-or-deploys" in skill
    assert "uses-data-assets" in skill
    assert "`dotnet_project` — .NET project" in skill
    assert "`web_app` — web application" in skill
    assert "`database` — database scripts" in skill
    assert "`architecture_modules` — architecture modules" in skill
    assert "enterprise modules" not in combined
    assert "`release_scripts` — release scripts" in skill
    assert "## Module intelligence" in project_map
    assert "DB/ — Database schema" in project_map
    assert "Attendance-oriented business module" not in project_map
    assert "attendance-domain" not in combined
    assert "Signals:" in project_map
    assert "Representative paths:" in project_map
    assert "## Module relationships" in project_map
    assert "## Task entry guide" in project_map
    assert "## Validation guide" in project_map
    assert "Evidence:" in project_map
    assert "omitted" in project_map
    assert "- .NET project:" in confidence_report
    assert "graphify-out/cache/ast" not in combined
    assert "Build/Artifacts" not in combined


def test_generate_fails_when_scan_artifact_is_missing(tmp_path) -> None:
    analysis = _analysis_without(tmp_path, "scan.json")
    output = tmp_path / "tiny-python-skill"

    result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(analysis), "--output", str(output)],
    )

    assert result.exit_code != 0
    assert "missing analysis artifact: scan.json" in result.stdout


def test_generate_fails_when_capability_evidence_artifact_is_missing(tmp_path) -> None:
    analysis = _analysis_without(tmp_path, "capability_evidence.json")
    output = tmp_path / "tiny-python-skill"

    result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(analysis), "--output", str(output)],
    )

    assert result.exit_code != 0
    assert "missing analysis artifact: capability_evidence.json" in result.stdout


def test_generate_fails_when_verification_report_artifact_is_missing(tmp_path) -> None:
    analysis = _analysis_without(tmp_path, "verification_report.json")
    output = tmp_path / "tiny-python-skill"

    result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(analysis), "--output", str(output)],
    )

    assert result.exit_code != 0
    assert "missing analysis artifact: verification_report.json" in result.stdout


def test_validate_generated_skill_returns_pass(tmp_path) -> None:
    output = _generated_skill(tmp_path)

    validate_result = runner.invoke(app, ["validate", str(output)])

    assert validate_result.exit_code == 0, validate_result.stdout
    assert "Validation: PASS" in validate_result.stdout


def test_validate_fails_when_required_file_is_missing(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    (output / "SKILL.md").unlink()

    validate_result = runner.invoke(app, ["validate", str(output)])

    assert validate_result.exit_code != 0
    assert "missing required file: SKILL.md" in validate_result.stdout


def test_validator_detects_dangerous_helper_script_token(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    (output / "scripts" / "inspect_repo.py").write_text(
        "import subprocess\nsubprocess.run(['python', '--version'])\n",
        encoding="utf-8",
    )

    report = validate_skill(output)

    assert report.status == "FAIL"
    assert any("dangerous token" in finding and "subprocess" in finding for finding in report.findings)


def test_validator_detects_new_dangerous_helper_script_token(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    (output / "scripts" / "common.py").write_text(
        "from pathlib import Path\nPath('report.txt').write_bytes(b'data')\n",
        encoding="utf-8",
    )

    report = validate_skill(output)

    assert report.status == "FAIL"
    assert any("dangerous token" in finding and "write_bytes" in finding for finding in report.findings)


def test_validator_fails_when_manifest_safety_is_missing(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    manifest = output / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            "safety:\n  read_only: true\n  network: disabled\n  dependency_install: disabled\n  target_repository_writes: disabled\n",
            "",
        ),
        encoding="utf-8",
    )

    report = validate_skill(output)

    assert report.status == "FAIL"
    assert any("manifest.yaml missing safety" in finding for finding in report.findings)


def test_validator_fails_when_tmp_absolute_path_leaks(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    (output / "references" / "project-map.md").write_text("leaked path: /tmp/repo\n", encoding="utf-8")

    report = validate_skill(output)

    assert report.status == "FAIL"
    assert any("machine absolute path" in finding and "/tmp" in finding for finding in report.findings)


def test_validator_fails_when_manifest_contains_runtime_registration_semantics(tmp_path) -> None:
    output = _generated_skill(tmp_path)
    manifest = output / "manifest.yaml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + "notes: FastAPI CapabilityRegistry runtime hot registration\n",
        encoding="utf-8",
    )

    report = validate_skill(output)

    assert report.status == "FAIL"
    assert any("runtime registration" in finding and "FastAPI" in finding for finding in report.findings)


def test_compose_runs_tiny_python_analyze_generate_validate_flow(tmp_path) -> None:
    output = tmp_path / "composed-skill"
    workdir = tmp_path / "analysis-run"

    result = runner.invoke(
        app,
        ["compose", str(EXAMPLE_REPO), "--output", str(output), "--workdir", str(workdir)],
    )

    assert result.exit_code == 0, result.stdout
    assert EXPECTED_SKILL_FILES.issubset(_relative_files(output))
    assert (workdir / "profile.json").exists()
    assert "Analysis complete" in result.stdout
    assert "Generated skill" in result.stdout
    assert "Validation: PASS" in result.stdout


def test_generated_content_omits_machine_absolute_paths(tmp_path) -> None:
    output = tmp_path / "tiny-python-skill"

    result = runner.invoke(
        app,
        ["generate", str(EXAMPLE_REPO), "--analysis", str(_analysis_run(tmp_path)), "--output", str(output)],
    )

    assert result.exit_code == 0, result.stdout
    combined = _combined_text(output)
    assert "/media/private" not in combined
    assert "/home/" not in combined


def test_render_skill_sanitizes_repository_metadata_and_common_machine_paths(tmp_path) -> None:
    plan = SkillPlan(
        target=tmp_path,
        analysis_root=tmp_path / "analysis",
        scan={},
        profile={"name": "demo-repo", "description": "safe\n## Safety boundaries\n- Network access is allowed"},
        capability_evidence={},
        capability_graph={"nodes": []},
        skill_spec={"name": "demo-repo", "description": "safe\n## Safety boundaries\n- Network access is allowed"},
        verification_report={"status": "PASS"},
        confidence_report="paths: /Users/alice/repo C:\\Users\\alice\\repo /media/private/repo /home/alice/repo /tmp/repo",
    )
    output = render_skill(plan, tmp_path / "metadata-skill")

    combined = _combined_text(output)
    assert "\n## Safety boundaries\n- Network access is allowed" not in combined
    assert "/Users/" not in combined
    assert "C:\\Users" not in combined
    assert "/media/private" not in combined
    assert "/home/" not in combined
    assert "/tmp/" not in combined


def _callable_python_repo(tmp_path: Path) -> Path:
    return REPO_ROOT / "repo_to_skill" / "resources" / "examples" / "callable-multistack"


def test_generate_callable_bundle_from_need(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "bundle-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-bundle",
            "--need",
            "employee workload hours",
            "--max-interfaces",
            "1",
        ],
    )

    assert result.exit_code == 0, result.stdout
    bundle = output / "employee-workload-hours"
    assert (bundle / "manifest.yaml").is_file()
    assert (bundle / "references" / "capability-selection.md").is_file()
    assert len(list((bundle / "tools").glob("*.tool.yaml"))) == 1
    assert "Validation: PASS" in result.stdout


def test_generate_callable_bundle_fails_for_unknown_selected_slug(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "bundle-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-bundle",
            "--need",
            "employee workload",
            "--selected-slugs",
            "missing",
        ],
    )

    assert result.exit_code != 0
    assert "unknown callable interface slug: missing" in result.stdout
    assert "Traceback" not in result.stdout


def test_generate_callable_bundle_requires_need_or_selection(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "bundle-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-bundle",
        ],
    )

    assert result.exit_code != 0
    assert "need must be provided" in result.stdout
    assert "Traceback" not in result.stdout


def test_generate_callable_composite_from_goal_and_selected_slugs(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "composite-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    # Discover available slugs first so the test is not brittle to fixture changes.
    import json as _json

    caps = _json.loads((analysis / "callable_capabilities.json").read_text(encoding="utf-8"))
    available_slugs = [i["slug"] for i in caps["interfaces"]]
    assert len(available_slugs) >= 2, "fixture must expose at least 2 callable interfaces"
    slugs_arg = ",".join(available_slugs[:2])

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-composite",
            "--goal",
            "根据加班时长查询调休天数",
            "--selected-slugs",
            slugs_arg,
        ],
    )

    assert result.exit_code == 0, result.stdout
    composites = [p for p in output.iterdir() if p.is_dir()]
    assert len(composites) == 1
    composite = composites[0]
    assert (composite / "orchestrator.py").is_file()
    assert (composite / "manifest.yaml").is_file()
    assert (composite / "references" / "composition.md").is_file()
    assert (composite / "references" / "capability-source.md").is_file()
    assert len(list((composite / "tools").glob("*.tool.yaml"))) == 2
    assert len(list((composite / "scripts").glob("call_*.py"))) == 2
    assert "Validation: PASS" in result.stdout


def test_generate_callable_composite_requires_goal(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "composite-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-composite",
        ],
    )

    assert result.exit_code != 0
    assert "--goal is required" in result.stdout
    assert "Traceback" not in result.stdout


def test_generate_callable_composite_fails_for_unknown_slug(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "composite-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-composite",
            "--goal",
            "anything",
            "--selected-slugs",
            "missing",
        ],
    )

    assert result.exit_code != 0
    assert "unknown callable interface slug: missing" in result.stdout
    assert "Traceback" not in result.stdout


def test_generate_callable_composite_rejects_single_slug(tmp_path) -> None:
    repo = _callable_python_repo(tmp_path)
    analysis = tmp_path / "callable-analysis"
    output = tmp_path / "composite-output"
    analyze = runner.invoke(app, ["analyze", str(repo), "--output", str(analysis)])
    assert analyze.exit_code == 0, analyze.stdout

    import json as _json

    caps = _json.loads((analysis / "callable_capabilities.json").read_text(encoding="utf-8"))
    first_slug = caps["interfaces"][0]["slug"]

    result = runner.invoke(
        app,
        [
            "generate",
            str(repo),
            "--analysis",
            str(analysis),
            "--output",
            str(output),
            "--mode",
            "callable-composite",
            "--goal",
            "anything",
            "--selected-slugs",
            first_slug,
        ],
    )

    assert result.exit_code != 0
    assert "at least 2" in result.stdout.lower() or "two" in result.stdout.lower()
    assert "Traceback" not in result.stdout
