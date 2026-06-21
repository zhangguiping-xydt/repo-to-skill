from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from repo_to_skill.skillgen.validator import REQUIRED_FILES, SkillValidationReport


@dataclass(frozen=True)
class EvalCheck:
    name: str
    passed: bool
    detail: str


def load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path.name}")
    return data


def load_yaml_object(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected YAML mapping: {path.name}")
    return data


def check_files(root: Path, expected_files: list[str], name: str) -> EvalCheck:
    missing = [relative for relative in expected_files if not (root / relative).is_file()]
    if missing:
        return EvalCheck(name, False, "missing: " + ", ".join(missing))
    return EvalCheck(name, True, f"found {len(expected_files)} files")


def check_validation(report: SkillValidationReport) -> EvalCheck:
    if report.status == "PASS":
        return EvalCheck("validation", True, "validator returned PASS")
    return EvalCheck("validation", False, "; ".join(report.findings) or "validator returned FAIL")


def check_profile_and_spec_signals(
    profile: dict[str, Any], skill_spec: dict[str, Any], case: dict[str, Any]
) -> EvalCheck:
    expected = case.get("expect", {})
    expected_languages = {str(value).lower() for value in expected.get("languages", [])}
    expected_capabilities = {str(value).lower() for value in expected.get("capabilities", [])}
    expected_project = str(expected.get("project_name", ""))

    languages = {str(value).lower() for value in profile.get("languages", [])}
    primary_language = str(profile.get("primary_language", "")).lower()
    capabilities = {str(value).lower() for value in skill_spec.get("capabilities", [])}
    spec_name = str(skill_spec.get("name", ""))
    profile_name = str(profile.get("name", ""))

    failures: list[str] = []
    if not expected_languages.intersection(languages | {primary_language}):
        failures.append("expected language not found")
    missing_capabilities = sorted(expected_capabilities - capabilities)
    if missing_capabilities:
        failures.append("missing capabilities: " + ", ".join(missing_capabilities))
    if expected_project and expected_project not in {profile_name, spec_name}:
        failures.append("expected project name not found")

    if failures:
        return EvalCheck("python signals", False, "; ".join(failures))
    return EvalCheck("python signals", True, "profile and skill spec include expected Python signals")


def check_no_forbidden_tokens(skill_root: Path, forbidden_tokens: list[str]) -> EvalCheck:
    checked_files = [skill_root / "SKILL.md"] + sorted((skill_root / "references").glob("**/*"))
    leaks: list[str] = []
    for path in checked_files:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in content:
                leaks.append(f"{path.relative_to(skill_root)} contains {token}")

    if leaks:
        return EvalCheck("machine path leaks", False, "; ".join(leaks))
    return EvalCheck("machine path leaks", True, "no forbidden machine path tokens in SKILL.md/references")


def check_callable_detection(callable_capabilities: dict[str, Any], case: dict[str, Any]) -> EvalCheck:
    expected = case.get("expect", {}).get("callable", {})
    interfaces = [item for item in callable_capabilities.get("interfaces", []) if isinstance(item, dict)]

    failures: list[str] = []
    minimum = expected.get("min_interfaces")
    if isinstance(minimum, int) and len(interfaces) < minimum:
        failures.append(f"expected at least {minimum} interfaces, found {len(interfaces)}")

    expected_stacks = {str(value).lower() for value in expected.get("stacks", [])}
    found_stacks = {str(item.get("stack", "")).lower() for item in interfaces}
    missing_stacks = sorted(expected_stacks - found_stacks)
    if missing_stacks:
        failures.append("missing stacks: " + ", ".join(missing_stacks))

    if failures:
        return EvalCheck("callable detection", False, "; ".join(failures))
    return EvalCheck(
        "callable detection",
        True,
        f"detected {len(interfaces)} interfaces across stacks {', '.join(sorted(found_stacks)) or 'none'}",
    )


def check_callable_packs(skill_roots: list[Path], case: dict[str, Any]) -> EvalCheck:
    if not skill_roots:
        return EvalCheck("callable packs", False, "no callable packs were rendered")

    pack_files = case.get("expect", {}).get("callable", {}).get(
        "pack_files", ["manifest.yaml", "SKILL.md", "references/capability-source.md"]
    )
    missing: list[str] = []
    for root in skill_roots:
        for relative in pack_files:
            if not (root / str(relative)).is_file():
                missing.append(f"{root.name}/{relative}")
        if not list(root.glob("tools/*.tool.yaml")):
            missing.append(f"{root.name}/tools/*.tool.yaml")
        if not list(root.glob("scripts/call_*.py")):
            missing.append(f"{root.name}/scripts/call_*.py")

    if missing:
        return EvalCheck("callable packs", False, "missing: " + ", ".join(missing))
    return EvalCheck("callable packs", True, f"{len(skill_roots)} packs include expected files")


def check_callable_bundle(skill_root: Path, case: dict[str, Any]) -> EvalCheck:
    bundle_files = case.get("expect", {}).get("callable", {}).get(
        "bundle_files",
        ["manifest.yaml", "SKILL.md", "references/capability-selection.md", "references/capability-source.md"],
    )
    missing: list[str] = []
    for relative in bundle_files:
        if not (skill_root / str(relative)).is_file():
            missing.append(str(relative))
    tools = sorted(skill_root.glob("tools/*.tool.yaml"))
    scripts = sorted(skill_root.glob("scripts/call_*.py"))
    if not tools:
        missing.append("tools/*.tool.yaml")
    if not scripts:
        missing.append("scripts/call_*.py")
    if tools and scripts and len(tools) != len(scripts):
        missing.append("tools/scripts count mismatch")
    minimum = case.get("expect", {}).get("callable", {}).get("min_bundle_interfaces")
    if isinstance(minimum, int) and len(tools) < minimum:
        missing.append(f"expected at least {minimum} bundle interfaces, found {len(tools)}")
    if missing:
        return EvalCheck("callable bundle", False, "missing: " + ", ".join(missing))
    return EvalCheck("callable bundle", True, f"bundle includes {len(tools)} callable tools")


def check_callable_validation(reports: list[tuple[str, SkillValidationReport]]) -> EvalCheck:
    if not reports:
        return EvalCheck("callable validation", False, "no callable packs were validated")
    failures: list[str] = []
    for name, report in reports:
        if report.status != "PASS":
            detail = "; ".join(report.findings) or "FAIL"
            failures.append(f"{name}: {detail}")
    if failures:
        return EvalCheck("callable validation", False, " | ".join(failures))
    return EvalCheck("callable validation", True, f"{len(reports)} packs returned PASS")


def check_callable_bundle_validation(report: SkillValidationReport) -> EvalCheck:
    if report.status == "PASS":
        return EvalCheck("callable bundle validation", True, "validator returned PASS")
    return EvalCheck("callable bundle validation", False, "; ".join(report.findings) or "validator returned FAIL")


def check_no_forbidden_tokens_in_packs(skill_roots: list[Path], forbidden_tokens: list[str]) -> EvalCheck:
    leaks: list[str] = []
    for root in skill_roots:
        for path in sorted(root.glob("**/*")):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for token in forbidden_tokens:
                if token in content:
                    leaks.append(f"{root.name}/{path.relative_to(root)} contains {token}")

    if leaks:
        return EvalCheck("machine path leaks", False, "; ".join(leaks))
    return EvalCheck("machine path leaks", True, "no forbidden machine path tokens in callable packs")


def default_skill_files() -> list[str]:
    return list(REQUIRED_FILES)
