from pathlib import Path

from repo_to_skill.reverse.capability_evidence import build_capability_evidence
from repo_to_skill.reverse.capability_graph import build_capability_graph
from repo_to_skill.reverse.project_profile import build_project_profile
from repo_to_skill.scanner.filesystem import scan_repository


def test_build_project_profile_for_tiny_python_app() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-app"
    scan = scan_repository(root)

    profile = build_project_profile(scan)

    assert profile.name == "tiny-python-app"
    assert profile.primary_language == "Python"
    assert "python" in profile.ecosystems
    assert "python-build" in profile.package_managers
    assert "python -m pytest" in profile.test_commands
    assert "tiny-app = tiny_app.cli:main" in profile.entrypoints


def test_build_project_profile_infers_pytest_from_python_test_files(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "pyproject.toml").write_text(
        """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sample-app"
version = "0.1.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_cli.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    scan = scan_repository(repo)
    profile = build_project_profile(scan, repo)

    assert "python -m pytest" in profile.test_commands


def test_build_project_profile_prefers_source_language_over_generated_json_cache(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "TMS.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    web = repo / "Web"
    web.mkdir()
    (web / "Default.aspx").write_text("<%@ Page Language=\"C#\" %>\n", encoding="utf-8")
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
    pipeline = repo / "PIPELINE"
    pipeline.mkdir()
    (pipeline / "userconfig.yml").write_text("steps: []\n", encoding="utf-8")
    module = repo / "TMS_CN001_CommonFramework"
    module.mkdir()
    (module / "Common.cs").write_text("public class Common {}\n", encoding="utf-8")
    cache = repo / "graphify-out" / "cache" / "ast"
    cache.mkdir(parents=True)
    for index in range(20):
        (cache / f"{index}.json").write_text('{"generated": true}\n', encoding="utf-8")

    scan = scan_repository(repo)
    profile = build_project_profile(scan, repo)
    evidence = build_capability_evidence(profile, scan)
    evidence_names = {item.name for item in evidence.evidence}

    modules = {module.name: module for module in profile.module_summaries}

    assert profile.primary_language == "C#"
    assert profile.languages[:3] == ["C#", "ASP.NET", "SQL"]
    assert not any(path.startswith("graphify-out/") for path in profile.configuration_files + profile.source_files)
    assert {"dotnet_project", "web_app", "database", "architecture_modules"}.issubset(evidence_names)
    assert "ASP.NET web application surface" in modules["Web/"].summary
    assert "aspnet-web" in modules["Web/"].signals
    assert "Database schema" in modules["DB/"].summary
    assert "database-scripts" in modules["DB/"].signals
    assert modules["Attendance/"].summary == "Application source module inferred from dominant source files."
    assert "application-source" in modules["Attendance/"].signals
    assert "attendance-domain" not in modules["Attendance/"].signals
    assert "server-service" in modules["RightDataServer/"].signals
    assert "release-automation" in modules["Build/"].signals
    assert "pipeline-config" in modules["PIPELINE/"].signals
    assert "business-module" in modules["TMS_CN001_CommonFramework/"].signals
    assert len(modules["Web/"].representative_paths) <= 6

    relationships = {(item.source, item.target, item.relation): item for item in profile.module_relationships}
    assert ("Build/", "Web/", "builds-or-deploys") in relationships
    assert ("PIPELINE/", "Web/", "builds-or-deploys") in relationships
    assert ("Web/", "DB/", "uses-data-assets") in relationships
    assert ("Web/", "TMS_CN001_CommonFramework/", "depends-on-shared-code") in relationships
    assert relationships[("Web/", "DB/", "uses-data-assets")].evidence

    guide_tasks = {item.task: item for item in profile.task_entry_guide}
    assert "Change application behavior" in guide_tasks
    assert "Change database or persistence assets" in guide_tasks
    assert "Web/" in guide_tasks["Change application behavior"].start_with
    assert "DB/" in guide_tasks["Change database or persistence assets"].start_with

    validation_scopes = {item.scope: item for item in profile.validation_guide}
    assert "Repository commands" in validation_scopes
    assert "Module static review" in validation_scopes
    validation_text = "\n".join(
        validation_scopes[scope].commands[0] if validation_scopes[scope].commands else ""
        for scope in validation_scopes
    )
    assert "install" not in validation_text.lower()
    assert "http" not in validation_text.lower()


def test_build_project_profile_uses_dominant_content_language_without_source_files(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    docs = repo / "docs"
    docs.mkdir()
    for index in range(3):
        (docs / f"topic-{index}.md").write_text("# Topic\n", encoding="utf-8")
    (repo / "metadata.json").write_text("{}\n", encoding="utf-8")

    scan = scan_repository(repo)
    profile = build_project_profile(scan, repo)

    assert profile.primary_language == "Markdown"
    assert profile.languages[0] == "Markdown"


def test_build_project_profile_keeps_source_dominant_modules_actionable(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "App.ts").write_text("export const app = true;\n", encoding="utf-8")
    state = src / "state"
    state.mkdir()
    (state / "schema.sql").write_text("create table sessions (id int);\n", encoding="utf-8")
    static = src / "static"
    static.mkdir()
    (static / "legacy.bat").write_text("echo legacy\n", encoding="utf-8")
    pipeline = src / "pipeline"
    pipeline.mkdir()
    (pipeline / "workflow.ts").write_text("export const workflow = true;\n", encoding="utf-8")

    scan = scan_repository(repo)
    profile = build_project_profile(scan, repo)

    modules = {module.name: module for module in profile.module_summaries}
    assert modules["src/"].summary == "Application source module inferred from dominant source files."
    assert "application-source" in modules["src/"].signals
    assert "database-scripts" not in modules["src/"].signals
    assert "release-automation" not in modules["src/"].signals
    assert "pipeline-config" not in modules["src/"].signals
    guide_tasks = {item.task: item for item in profile.task_entry_guide}
    assert "Change application behavior" in guide_tasks
    assert "src/" in guide_tasks["Change application behavior"].start_with


def test_build_project_profile_links_test_module_names_to_source_modules(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    api = repo / "api"
    api.mkdir()
    (api / "handler.py").write_text("def handle():\n    return True\n", encoding="utf-8")
    api_tests = repo / "api_tests"
    api_tests.mkdir()
    (api_tests / "test_handler.py").write_text("def test_handle():\n    assert True\n", encoding="utf-8")

    scan = scan_repository(repo)
    profile = build_project_profile(scan, repo)

    relationships = {(item.source, item.target, item.relation): item for item in profile.module_relationships}
    assert ("api_tests/", "api/", "validates") in relationships
    assert relationships[("api_tests/", "api/", "validates")].evidence


def test_build_project_profile_filters_dependency_and_network_validation_commands(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    src = repo / "src"
    src.mkdir()
    (src / "app.py").write_text("def main():\n    return True\n", encoding="utf-8")
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text("def test_main():\n    assert True\n", encoding="utf-8")

    scan = scan_repository(repo)
    scan.candidate_commands = [
        "npm ci && npm test",
        "uv sync && pytest",
        "dotnet restore",
        "go mod download",
        "curl https://example.invalid/script.sh",
        "yarn add left-pad && yarn test",
        "npm add x && npm test",
        "pnpm add x && pnpm test",
        "npx jest",
        "npm exec jest",
        "bunx jest",
        "dotnet test --no-restore",
        "python -m pytest",
        "python -m pytest tests/download",
        "msbuild App.sln",
    ]
    profile = build_project_profile(scan, repo)

    profile_commands = profile.test_commands + profile.run_commands
    commands = [command for guide in profile.validation_guide for command in guide.commands]
    assert commands == profile_commands
    assert "python -m pytest" in commands
    assert "python -m pytest tests/download" in commands
    assert "dotnet test --no-restore" in commands
    assert "msbuild App.sln" in commands
    blocked_text = "\n".join(commands).lower()
    assert "npm ci" not in blocked_text
    assert "uv sync" not in blocked_text
    assert "dotnet restore" not in blocked_text
    assert "go mod download" not in blocked_text
    assert "yarn add" not in blocked_text
    assert "npm add" not in blocked_text
    assert "pnpm add" not in blocked_text
    assert "npx" not in blocked_text
    assert "npm exec" not in blocked_text
    assert "bunx" not in blocked_text
    assert "http" not in blocked_text
    assert "curl" not in blocked_text


def test_capability_evidence_and_graph_are_deterministic() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-app"
    scan = scan_repository(root)
    profile = build_project_profile(scan)

    evidence = build_capability_evidence(profile, scan)
    graph = build_capability_graph(evidence)

    evidence_names = [item.name for item in evidence.evidence]
    assert evidence_names == sorted(evidence_names)
    assert {"cli", "test", "package_manager", "entrypoint", "configuration"}.issubset(evidence_names)
    assert graph.nodes
    assert graph.edges
    assert [node.id for node in graph.nodes] == sorted(node.id for node in graph.nodes)
