from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from repo_to_skill.evals.checks import (
    EvalCheck,
    check_callable_detection,
    check_callable_packs,
    check_callable_validation,
    check_files,
    check_no_forbidden_tokens,
    check_no_forbidden_tokens_in_packs,
    check_profile_and_spec_signals,
    check_validation,
    default_skill_files,
    load_json_object,
    load_yaml_object,
)
from repo_to_skill.reverse.callable_capabilities import build_callable_capabilities
from repo_to_skill.reverse.capability_evidence import build_capability_evidence
from repo_to_skill.reverse.capability_graph import build_capability_graph
from repo_to_skill.reverse.confidence_report import build_confidence_report
from repo_to_skill.reverse.project_profile import build_project_profile
from repo_to_skill.reverse.skill_spec import build_skill_spec
from repo_to_skill.reverse.verification import verify_static_outputs
from repo_to_skill.scanner.filesystem import scan_repository
from repo_to_skill.skillgen.planner import plan_callable_skills, plan_skill
from repo_to_skill.skillgen.renderer import render_callable_skills, render_skill
from repo_to_skill.skillgen.validator import validate_skill
from repo_to_skill.workspace.store import ArtifactStore


@dataclass(frozen=True)
class EvalResult:
    case_name: str
    status: str
    workspace: Path
    analysis_root: Path | None
    skill_root: Path | None
    checks: list[EvalCheck]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


ANALYZE_ARTIFACTS = [
    "scan.json",
    "profile.json",
    "capability_evidence.json",
    "capability_graph.json",
    "skill_spec.yaml",
    "verification_report.json",
    "confidence-report.md",
    "callable_capabilities.json",
]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resource_root() -> resources.abc.Traversable:
    return resources.files("repo_to_skill.resources")


def _case_resources_root() -> resources.abc.Traversable:
    return _resource_root() / "eval_cases"


def _fixture_resources_root() -> resources.abc.Traversable:
    return _resource_root() / "examples"


def cases_root() -> Path:
    return repository_root() / "evals" / "cases"


def available_cases() -> list[str]:
    root = _case_resources_root()
    if not root.is_dir():
        return []
    return sorted(path.name.removesuffix(".yaml") for path in root.iterdir() if path.name.endswith(".yaml"))


def _invalid_case(case_name: str, detail: str) -> ValueError:
    return ValueError(f"invalid eval case: {case_name}: {detail}")


def _validate_string_list(case_name: str, value: Any, field: str) -> None:
    if not isinstance(value, list):
        raise _invalid_case(case_name, f"field {field} must be a list")
    if not all(isinstance(item, str) for item in value):
        raise _invalid_case(case_name, f"field {field} must contain only strings")


_VALID_MODES = ("repo-map", "callable")


def _validate_case_schema(case_name: str, data: dict[str, Any]) -> None:
    if "fixture" not in data:
        raise _invalid_case(case_name, "missing required field fixture")
    if not isinstance(data["fixture"], str) or not data["fixture"].strip():
        raise _invalid_case(case_name, "field fixture must be a non-empty string")

    mode = data.get("mode", "repo-map")
    if not isinstance(mode, str) or mode not in _VALID_MODES:
        raise _invalid_case(case_name, f"field mode must be one of {', '.join(_VALID_MODES)}")

    expected = data.get("expect", {})
    if not isinstance(expected, dict):
        raise _invalid_case(case_name, "field expect must be a mapping")

    for field in ("languages", "ecosystems", "capabilities"):
        if field in expected:
            _validate_string_list(case_name, expected[field], f"expect.{field}")

    files = expected.get("files", {})
    if not isinstance(files, dict):
        raise _invalid_case(case_name, "field expect.files must be a mapping")
    for field in ("analyze_artifacts", "skill_files"):
        if field in files:
            _validate_string_list(case_name, files[field], f"expect.files.{field}")

    callable_expect = expected.get("callable", {})
    if not isinstance(callable_expect, dict):
        raise _invalid_case(case_name, "field expect.callable must be a mapping")
    if "min_interfaces" in callable_expect and not isinstance(callable_expect["min_interfaces"], int):
        raise _invalid_case(case_name, "field expect.callable.min_interfaces must be an integer")
    for field in ("stacks", "pack_files"):
        if field in callable_expect:
            _validate_string_list(case_name, callable_expect[field], f"expect.callable.{field}")

    safety = expected.get("safety", {})
    if not isinstance(safety, dict):
        raise _invalid_case(case_name, "field expect.safety must be a mapping")
    if "forbidden_output_tokens" in safety:
        _validate_string_list(
            case_name,
            safety["forbidden_output_tokens"],
            "expect.safety.forbidden_output_tokens",
        )


def _case_resource(case_name: str) -> resources.abc.Traversable:
    return _case_resources_root() / f"{case_name}.yaml"


def _read_case_text(case_name: str) -> str:
    case_resource = _case_resource(case_name)
    if not case_resource.is_file():
        cases = ", ".join(available_cases()) or "none"
        raise ValueError(f"unknown eval case: {case_name}. Available cases: {cases}")
    return case_resource.read_text(encoding="utf-8")


def load_case(case_name: str) -> dict[str, Any]:
    data = yaml.safe_load(_read_case_text(case_name))
    if not isinstance(data, dict):
        raise ValueError(f"invalid eval case: {case_name}: case must be a mapping")
    _validate_case_schema(case_name, data)
    return data


def _run_analysis(target: Path, output: Path) -> tuple[Path, str]:
    store = ArtifactStore(target, output)
    scan = scan_repository(store.target_root)
    profile = build_project_profile(scan, store.target_root)
    evidence = build_capability_evidence(profile, scan)
    graph = build_capability_graph(evidence)
    spec = build_skill_spec(profile, graph)
    verification = verify_static_outputs(evidence, graph, spec)
    confidence_report = build_confidence_report(profile, evidence, verification)
    callable_capabilities = build_callable_capabilities(scan, store.target_root)

    store.write_json("scan.json", scan)
    store.write_json("profile.json", profile)
    store.write_json("capability_evidence.json", evidence)
    store.write_json("capability_graph.json", graph)
    store.write_yaml("skill_spec.yaml", spec)
    store.write_json("verification_report.json", verification)
    store.write_markdown("confidence-report.md", confidence_report)
    store.write_json("callable_capabilities.json", callable_capabilities)
    return store.output_root, verification.status


def _workspace_root(
    workspace: Path | None,
    source_fixture_root: Path | None,
) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if workspace is not None:
        root = workspace.expanduser().resolve()
        if source_fixture_root is not None and (
            root == source_fixture_root or root.is_relative_to(source_fixture_root)
        ):
            raise ValueError("workspace must be outside eval fixture repository")
        root.mkdir(parents=True, exist_ok=True)
        return root, None
    temporary = tempfile.TemporaryDirectory(prefix="repo-to-skill-eval-")
    return Path(temporary.name).resolve(), temporary


def _source_tree_fixture_root(case: dict[str, Any]) -> Path | None:
    fixture = (repository_root() / case["fixture"]).resolve()
    return fixture if fixture.exists() else None


def _copy_fixture_resource(case_name: str, case: dict[str, Any], destination: Path) -> Path:
    resource = _fixture_resources_root() / Path(case["fixture"]).name
    if not resource.is_dir():
        raise ValueError(f"invalid eval case: {case_name}: fixture resource not found")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with resources.as_file(resource) as fixture_path:
        shutil.copytree(fixture_path, destination)
    return destination


def run_eval(case_name: str, workspace: Path | None = None) -> EvalResult:
    case = load_case(case_name)
    root, temporary = _workspace_root(workspace, _source_tree_fixture_root(case))
    try:
        input_root = root / case_name / "input" / Path(case["fixture"]).name
        fixture = _copy_fixture_resource(case_name, case, input_root)
        analysis_root = root / case_name / "analysis"
        skill_root = root / case_name / "skill"
        checks: list[EvalCheck] = []

        analysis_root, analysis_status = _run_analysis(fixture, analysis_root)
        expected = case.get("expect", {})
        analyze_files = expected.get("files", {}).get("analyze_artifacts", ANALYZE_ARTIFACTS)
        checks.append(check_files(analysis_root, [str(value) for value in analyze_files], "analyze artifacts"))
        if analysis_status != "PASS":
            checks.append(EvalCheck("analysis status", False, f"analysis returned {analysis_status}"))

        mode = case.get("mode", "repo-map")
        if mode == "callable":
            rendered_root = _run_callable_eval(case, fixture, analysis_root, skill_root, checks)
            status = "PASS" if all(check.passed for check in checks) else "FAIL"
            return EvalResult(case_name, status, root, analysis_root, rendered_root, checks)

        plan = plan_skill(fixture, analysis_root)
        rendered_skill = render_skill(plan, skill_root)
        skill_files = expected.get("files", {}).get("skill_files", default_skill_files())
        checks.append(check_files(rendered_skill, [str(value) for value in skill_files], "generated skill shape"))

        validation_report = validate_skill(rendered_skill)
        checks.append(check_validation(validation_report))

        profile = load_json_object(analysis_root / "profile.json")
        skill_spec = load_yaml_object(analysis_root / "skill_spec.yaml")
        checks.append(check_profile_and_spec_signals(profile, skill_spec, case))

        forbidden_tokens = expected.get("safety", {}).get(
            "forbidden_output_tokens", ["/media/private", "/home/", "/tmp"]
        )
        checks.append(check_no_forbidden_tokens(rendered_skill, [str(value) for value in forbidden_tokens]))

        status = "PASS" if all(check.passed for check in checks) else "FAIL"
        return EvalResult(case_name, status, root, analysis_root, rendered_skill, checks)
    finally:
        if temporary is not None:
            temporary.cleanup()


def _run_callable_eval(
    case: dict[str, Any],
    fixture: Path,
    analysis_root: Path,
    skill_root: Path,
    checks: list[EvalCheck],
) -> Path:
    expected = case.get("expect", {})
    callable_capabilities = load_json_object(analysis_root / "callable_capabilities.json")
    checks.append(check_callable_detection(callable_capabilities, case))

    plan = plan_callable_skills(fixture, analysis_root)
    rendered_packs = render_callable_skills(plan, skill_root)
    checks.append(check_callable_packs(rendered_packs, case))

    reports = [(pack.name, validate_skill(pack)) for pack in rendered_packs]
    checks.append(check_callable_validation(reports))

    forbidden_tokens = expected.get("safety", {}).get(
        "forbidden_output_tokens", ["/media/private", "/home/", "/tmp"]
    )
    checks.append(check_no_forbidden_tokens_in_packs(rendered_packs, [str(value) for value in forbidden_tokens]))
    return skill_root
