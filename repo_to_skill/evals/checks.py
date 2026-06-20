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


def default_skill_files() -> list[str]:
    return list(REQUIRED_FILES)
