from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from repo_to_skill.skillgen.callable_selector import CallableBundleSelection, select_callable_interfaces


@dataclass(frozen=True)
class SkillPlan:
    target: Path
    analysis_root: Path
    scan: dict[str, Any]
    profile: dict[str, Any]
    capability_evidence: dict[str, Any]
    capability_graph: dict[str, Any]
    skill_spec: dict[str, Any]
    verification_report: dict[str, Any]
    confidence_report: str

    @property
    def project_name(self) -> str:
        return str(self.profile.get("name") or self.skill_spec.get("name") or "local-repository")

    @property
    def description(self) -> str:
        return str(
            self.skill_spec.get("description")
            or self.profile.get("description")
            or "Local-first repository skill generated from static analysis."
        )

    @property
    def capabilities(self) -> list[str]:
        values = self.skill_spec.get("capabilities") or []
        return [str(value) for value in values]


@dataclass(frozen=True)
class CallableSkillPlan:
    target: Path
    analysis_root: Path
    scan: dict[str, Any]
    profile: dict[str, Any]
    callable_capabilities: dict[str, Any]

    @property
    def project_name(self) -> str:
        return str(
            self.callable_capabilities.get("project")
            or self.profile.get("name")
            or "local-repository"
        )

    @property
    def interfaces(self) -> list[dict[str, Any]]:
        values = self.callable_capabilities.get("interfaces") or []
        return [value for value in values if isinstance(value, dict)]

    @property
    def notes(self) -> list[str]:
        return [str(value) for value in self.callable_capabilities.get("notes") or []]


@dataclass(frozen=True)
class CallableBundlePlan:
    target: Path
    analysis_root: Path
    scan: dict[str, Any]
    profile: dict[str, Any]
    callable_capabilities: dict[str, Any]
    selection: CallableBundleSelection

    @property
    def project_name(self) -> str:
        return str(
            self.callable_capabilities.get("project")
            or self.profile.get("name")
            or "local-repository"
        )

    @property
    def bundle_slug(self) -> str:
        value = self.selection.need_summary or self.project_name
        cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower()).strip("-._")
        return cleaned or "callable-bundle"



def _analysis_root(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.is_dir():
        return resolved
    if resolved.name == "profile.json" and resolved.parent.exists():
        return resolved.parent.resolve()
    raise ValueError("analysis must be an analysis run directory or profile.json path")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"missing analysis artifact: {path.name}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid analysis artifact: {path.name}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"analysis artifact must be an object: {path.name}")
    return data


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"missing analysis artifact: {path.name}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid analysis artifact: {path.name}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"analysis artifact must be a mapping: {path.name}")
    return data


def plan_skill(target: Path, analysis: Path) -> SkillPlan:
    """Build a render plan from existing analyze artifacts without rescanning target."""
    target_root = target.expanduser().resolve()
    if not target_root.exists() or not target_root.is_dir():
        raise ValueError("target repository must be an existing directory")

    root = _analysis_root(analysis)
    scan = _read_json(root / "scan.json")
    profile = _read_json(root / "profile.json")
    capability_evidence = _read_json(root / "capability_evidence.json")
    capability_graph = _read_json(root / "capability_graph.json")
    skill_spec = _read_yaml(root / "skill_spec.yaml")
    verification_report = _read_json(root / "verification_report.json")
    confidence_path = root / "confidence-report.md"
    if not confidence_path.exists():
        raise ValueError("missing analysis artifact: confidence-report.md")
    confidence_report = confidence_path.read_text(encoding="utf-8")

    return SkillPlan(
        target=target_root,
        analysis_root=root,
        scan=scan,
        profile=profile,
        capability_evidence=capability_evidence,
        capability_graph=capability_graph,
        skill_spec=skill_spec,
        verification_report=verification_report,
        confidence_report=confidence_report,
    )


def plan_callable_skills(target: Path, analysis: Path) -> CallableSkillPlan:
    """Build a callable-skill render plan from existing analyze artifacts."""
    target_root = target.expanduser().resolve()
    if not target_root.exists() or not target_root.is_dir():
        raise ValueError("target repository must be an existing directory")

    root = _analysis_root(analysis)
    scan = _read_json(root / "scan.json")
    profile = _read_json(root / "profile.json")
    callable_capabilities = _read_json(root / "callable_capabilities.json")

    return CallableSkillPlan(
        target=target_root,
        analysis_root=root,
        scan=scan,
        profile=profile,
        callable_capabilities=callable_capabilities,
    )


def _load_selection_json(path: Path) -> dict[str, Any]:
    data = _read_json(path.expanduser().resolve())
    slugs = data.get("selected_slugs")
    if slugs is not None and not isinstance(slugs, list):
        raise ValueError("selection_json selected_slugs must be a list")
    if slugs is not None and not all(isinstance(value, str) for value in slugs):
        raise ValueError("selection_json selected_slugs must contain only strings")
    return data


def plan_callable_bundle(
    target: Path,
    analysis: Path,
    *,
    need: str,
    selected_slugs: list[str] | None,
    selection_json: Path | None,
    max_interfaces: int,
) -> CallableBundlePlan:
    """Build a render plan for one goal-oriented callable-bundle skill."""
    base = plan_callable_skills(target, analysis)
    selection_source = "deterministic"
    need_summary = need
    slugs = selected_slugs

    if selection_json is not None:
        data = _load_selection_json(selection_json)
        need_summary = str(data.get("need_summary") or need_summary or "")
        slugs = [str(value) for value in data.get("selected_slugs") or []]
        selection_source = str(data.get("selection_source") or "agentic")
    elif selected_slugs:
        selection_source = "agentic"

    selection = select_callable_interfaces(
        base.interfaces,
        need_summary,
        selected_slugs=slugs,
        max_interfaces=max_interfaces,
        selection_source=selection_source,
    )
    if not selection.items:
        raise ValueError("no callable interfaces matched the requested need")

    return CallableBundlePlan(
        target=base.target,
        analysis_root=base.analysis_root,
        scan=base.scan,
        profile=base.profile,
        callable_capabilities=base.callable_capabilities,
        selection=selection,
    )
