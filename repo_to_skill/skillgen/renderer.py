from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from repo_to_skill.skillgen.planner import SkillPlan


_ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"/media/[^\s)\]}>\"']*"),
    re.compile(r"/home/[^\s)\]}>\"']*"),
    re.compile(r"/tmp/[^\s)\]}>\"']*"),
    re.compile(r"/Users/[^\s)\]}>\"']*"),
    re.compile(r"[A-Za-z]:\\[^\s)\]}>\"']*"),
)
_CAPABILITY_BULLET_PATTERN = re.compile(r"(?m)^- ([a-z][a-z0-9_]*):")
_CAPABILITY_LABELS = {
    "cli": "CLI",
    "configuration": "configuration",
    "database": "database scripts",
    "documentation": "documentation",
    "dotnet_project": ".NET project",
    "enterprise_modules": "enterprise modules",
    "entrypoint": "entrypoints",
    "package_manager": "package manager",
    "release_scripts": "release scripts",
    "test": "tests",
    "web_app": "web application",
}


def _template_env() -> Environment:
    template_root = Path(__file__).resolve().parent / "templates"
    return Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(enabled_extensions=()),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower()).strip("-._")
    return cleaned or "local-repository"


def _strip_machine_paths(value: str) -> str:
    sanitized = value
    for pattern in _ABSOLUTE_PATH_PATTERNS:
        sanitized = pattern.sub("[local-path]", sanitized)
    return sanitized


def _inline_text(value: str, fallback: str = "") -> str:
    sanitized = _strip_machine_paths(str(value)).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized or fallback


def _inline_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_inline_text(str(value)) for value in values if _inline_text(str(value))]


def _sanitized_skill_spec(skill_spec: dict[str, Any], description: str) -> dict[str, Any]:
    sanitized = dict(skill_spec)
    sanitized["name"] = _inline_text(str(sanitized.get("name") or ""), "local-repository")
    sanitized["description"] = _inline_text(str(sanitized.get("description") or ""), description)
    sanitized["capabilities"] = _inline_list(sanitized.get("capabilities"))
    sanitized["safety_boundaries"] = _inline_list(sanitized.get("safety_boundaries"))
    sanitized["commands"] = _inline_list(sanitized.get("commands"))
    return sanitized


def _normalize_capability_labels(value: str) -> str:
    return _CAPABILITY_BULLET_PATTERN.sub(
        lambda match: f"- {_CAPABILITY_LABELS.get(match.group(1), match.group(1).replace('_', ' '))}:",
        value,
    )


def _list_items(profile: dict[str, Any], key: str) -> list[str]:
    return [str(item) for item in profile.get(key, [])]


def _summarize_list(values: list[str], limit: int = 40) -> dict[str, Any]:
    items = values[:limit]
    return {"paths": items, "total": len(values), "omitted": max(len(values) - len(items), 0)}


_FALLBACK_SIGNAL_PRIORITY = [
    "aspnet-web",
    "database-scripts",
    "dotnet-project",
    "release-automation",
    "pipeline-config",
    "server-service",
    "client-app",
    "business-module",
]


def _fallback_module_signals(name: str, paths: list[str]) -> list[str]:
    lowered_name = name.rstrip("/").lower()
    lowered_paths = [path.lower() for path in paths]
    suffixes = {Path(path).suffix.lower() for path in paths}
    raw: set[str] = set()
    if lowered_name == "web" or suffixes & {".aspx", ".asmx", ".ashx", ".ascx"}:
        raw.add("aspnet-web")
    if lowered_name in {"db", "database", "sql"} or suffixes & {".sql", ".prc", ".vw", ".pck", ".seq"}:
        raw.add("database-scripts")
    if suffixes & {".sln", ".csproj"}:
        raw.add("dotnet-project")
    if lowered_name in {"build", "deploy", "release"} or suffixes & {".bat", ".cmd"}:
        raw.add("release-automation")
    if "pipeline" in lowered_name or any("pipeline" in path for path in lowered_paths):
        raw.add("pipeline-config")
    if "server" in lowered_name or "service" in lowered_name:
        raw.add("server-service")
    if "client" in lowered_name or "ui" in lowered_name:
        raw.add("client-app")
    segmented_name = "_" in lowered_name and any(character.isdigit() for character in lowered_name)
    if segmented_name or "business" in lowered_name or "biz" in lowered_name or "manage" in lowered_name:
        raw.add("business-module")
    return [signal for signal in _FALLBACK_SIGNAL_PRIORITY if signal in raw]


def _fallback_module_summary(name: str, signals: list[str]) -> str:
    lowered_name = name.rstrip("/").lower()
    if lowered_name in {"build", "deploy", "release", "pipeline", "pipelines"}:
        return "Build, release, or deployment automation module."
    if "server-service" in signals:
        return "Server-side service or backend runtime module."
    if "client-app" in signals:
        return "Client application module inferred from module naming and file-type signals."
    if "aspnet-web" in signals:
        return "ASP.NET web application surface with pages, handlers, services, and configuration."
    if "database-scripts" in signals:
        return "Database schema and script layer with SQL objects or migration-like assets."
    if "business-module" in signals:
        return "Enterprise application or business capability module inferred from module naming."
    return ""


def _module_summary(profile: dict[str, Any]) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for item in profile.get("module_summaries") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        modules.append(
            {
                "name": name,
                "total": int(item.get("total") or 0),
                "source": int(item.get("source") or 0),
                "configuration": int(item.get("configuration") or 0),
                "documentation": int(item.get("documentation") or 0),
                "test": int(item.get("test") or 0),
                "languages": [str(value) for value in item.get("languages") or []],
                "signals": [str(value) for value in item.get("signals") or []],
                "summary": str(item.get("summary") or ""),
                "representative_paths": [str(value) for value in item.get("representative_paths") or []],
            }
        )
    if modules:
        return sorted(modules, key=lambda item: (-item["total"], item["name"]))[:12]

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"source": 0, "configuration": 0, "documentation": 0, "test": 0})
    module_paths: dict[str, list[str]] = defaultdict(list)
    key_roles = {
        "source_files": "source",
        "configuration_files": "configuration",
        "documentation_files": "documentation",
        "test_files": "test",
    }
    for key, role in key_roles.items():
        for path in _list_items(profile, key):
            if "/" not in path:
                continue
            module = path.split("/", 1)[0] + "/"
            counts[module][role] += 1
            module_paths[module].append(path)
    for name, role_counts in counts.items():
        total = sum(role_counts.values())
        representative_paths = sorted(dict.fromkeys(module_paths[name]))[:6]
        signals = _fallback_module_signals(name, representative_paths)
        modules.append(
            {
                "name": name,
                "total": total,
                "summary": _fallback_module_summary(name, signals),
                "signals": signals,
                "languages": [],
                "representative_paths": representative_paths,
                **role_counts,
            }
        )
    return sorted(modules, key=lambda item: (-item["total"], item["name"]))[:12]


def _module_relationships(profile: dict[str, Any]) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    for item in profile.get("module_relationships") or []:
        if not isinstance(item, dict):
            continue
        source = _inline_text(str(item.get("source") or ""))
        target = _inline_text(str(item.get("target") or ""))
        relation = _inline_text(str(item.get("relation") or ""))
        if not source or not target or not relation:
            continue
        relationships.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "reason": _inline_text(str(item.get("reason") or "")),
                "evidence": _inline_list(item.get("evidence")),
            }
        )
    return sorted(relationships, key=lambda item: (item["source"], item["target"], item["relation"]))


def _task_entry_guide(profile: dict[str, Any]) -> list[dict[str, Any]]:
    guides: list[dict[str, Any]] = []
    for item in profile.get("task_entry_guide") or []:
        if not isinstance(item, dict):
            continue
        task = _inline_text(str(item.get("task") or ""))
        if not task:
            continue
        guides.append(
            {
                "task": task,
                "start_with": _inline_list(item.get("start_with")),
                "then_check": _inline_list(item.get("then_check")),
                "rationale": _inline_text(str(item.get("rationale") or "")),
            }
        )
    return sorted(guides, key=lambda item: item["task"])


def _validation_guide(profile: dict[str, Any]) -> list[dict[str, Any]]:
    guides: list[dict[str, Any]] = []
    for item in profile.get("validation_guide") or []:
        if not isinstance(item, dict):
            continue
        scope = _inline_text(str(item.get("scope") or ""))
        if not scope:
            continue
        guides.append(
            {
                "scope": scope,
                "commands": _inline_list(item.get("commands")),
                "paths": _inline_list(item.get("paths")),
                "notes": _inline_list(item.get("notes")),
            }
        )
    return sorted(guides, key=lambda item: item["scope"])


def _project_map(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "languages": _list_items(profile, "languages"),
        "ecosystems": _list_items(profile, "ecosystems"),
        "package_managers": _list_items(profile, "package_managers"),
        "entrypoints": _list_items(profile, "entrypoints"),
        "configuration_files": _summarize_list(_list_items(profile, "configuration_files")),
        "documentation_files": _summarize_list(_list_items(profile, "documentation_files")),
        "source_files": _summarize_list(_list_items(profile, "source_files")),
        "test_files": _summarize_list(_list_items(profile, "test_files")),
        "test_commands": _list_items(profile, "test_commands"),
        "run_commands": _list_items(profile, "run_commands"),
        "modules": _module_summary(profile),
        "module_relationships": _module_relationships(profile),
        "task_entry_guide": _task_entry_guide(profile),
        "validation_guide": _validation_guide(profile),
    }


def _capability_items(capability_graph: dict[str, Any], fallback_capabilities: list[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for node in capability_graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        raw_id = str(node.get("id") or "").removeprefix("capability:")
        label = _CAPABILITY_LABELS.get(raw_id, str(node.get("label") or raw_id.replace("_", " ")).strip())
        if raw_id or label:
            items.append({"id": raw_id or label.replace(" ", "_"), "label": label})
    if items:
        return sorted(items, key=lambda item: item["id"])
    return [
        {
            "id": capability.replace(" ", "_"),
            "label": _CAPABILITY_LABELS.get(capability.replace(" ", "_"), capability),
        }
        for capability in fallback_capabilities
    ]


def _key_paths(profile: dict[str, Any]) -> list[str]:
    modules = [module["name"] for module in _module_summary(profile)]
    if modules:
        return modules[:8]
    values: list[str] = []
    for key in ("configuration_files", "documentation_files", "source_files", "test_files"):
        for item in profile.get(key, []):
            path = str(item)
            values.append(path.split("/", 1)[0] + "/" if "/" in path else path)
    return sorted(dict.fromkeys(values))[:8]


def render_skill(plan: SkillPlan, output: Path) -> Path:
    """Render a reviewable AI coding agent skill pack directory from a SkillPlan."""
    output_root = output.expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "scripts").mkdir(exist_ok=True)
    (output_root / "references").mkdir(exist_ok=True)

    env = _template_env()
    capability_items = _capability_items(plan.capability_graph, plan.capabilities)
    display_project_name = _inline_text(plan.project_name, "local-repository")
    display_description = _inline_text(plan.description, "Local-first repository skill generated from static analysis.")
    sanitized_skill_spec = _sanitized_skill_spec(plan.skill_spec, display_description)
    context = {
        "skill_name": _safe_name(plan.project_name),
        "project_name": display_project_name,
        "description": display_description,
        "capabilities": plan.capabilities,
        "capability_items": capability_items,
        "scan": plan.scan,
        "profile": plan.profile,
        "capability_evidence": plan.capability_evidence,
        "capability_graph": plan.capability_graph,
        "skill_spec": sanitized_skill_spec,
        "verification_report": plan.verification_report,
        "confidence_report": _normalize_capability_labels(_strip_machine_paths(plan.confidence_report)),
        "project_map": _project_map(plan.profile),
        "key_paths": _key_paths(plan.profile),
        "generated_by": "repo-to-skill",
    }

    outputs = {
        "manifest.yaml": "manifest.yaml.j2",
        "SKILL.md": "SKILL.md.j2",
        "scripts/inspect_repo.py": "scripts/inspect_repo.py.j2",
        "scripts/common.py": "scripts/common.py.j2",
        "references/project-map.md": "references/project-map.md.j2",
        "references/capability-graph.md": "references/capability-graph.md.j2",
        "references/skill-spec.md": "references/skill-spec.md.j2",
        "references/confidence-report.md": "references/confidence-report.md.j2",
    }

    for relative_path, template_name in outputs.items():
        rendered = env.get_template(template_name).render(**context)
        rendered = _strip_machine_paths(rendered)
        destination = output_root / relative_path
        destination.write_text(rendered, encoding="utf-8")

    return output_root
