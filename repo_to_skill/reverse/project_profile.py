from __future__ import annotations

from collections import Counter, defaultdict
import re
import tomllib
from pathlib import Path

from repo_to_skill.models import ModuleRelationship, ModuleSummary, ProjectProfile, ScanResult, TaskGuideItem, ValidationGuideItem


def _pyproject_metadata(root: Path) -> tuple[str | None, str | None]:
    path = root / "pyproject.toml"
    if not path.exists():
        return None, None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return None, None
    project = data.get("project", {})
    if not isinstance(project, dict):
        return None, None
    return project.get("name"), project.get("description")


def _source_language_counts(scan: ScanResult) -> Counter[str]:
    return Counter(record.language for record in scan.files if record.role == "source" and record.language != "Unknown")


def _primary_language(scan: ScanResult) -> str:
    source_counts = _source_language_counts(scan)
    if source_counts:
        return sorted(source_counts.items(), key=lambda item: (-item[1], _LANGUAGE_PRIORITY.get(item[0], 99), item[0]))[0][0]
    content_counts = Counter(record.language for record in scan.files if record.language != "Unknown")
    if content_counts:
        return sorted(content_counts.items(), key=lambda item: (-item[1], _LANGUAGE_PRIORITY.get(item[0], 99), item[0]))[0][0]
    return scan.languages[0] if scan.languages else "Unknown"


def _ordered_languages(scan: ScanResult, primary_language: str) -> list[str]:
    source_counts = _source_language_counts(scan)
    source_languages = [
        language
        for language, _ in sorted(
            source_counts.items(), key=lambda item: (-item[1], _LANGUAGE_PRIORITY.get(item[0], 99), item[0])
        )
    ]
    ordered = [primary_language] if primary_language != "Unknown" else []
    ordered.extend(language for language in source_languages if language not in ordered)
    ordered.extend(language for language in scan.languages if language not in ordered)
    return ordered


_LANGUAGE_PRIORITY = {
    "ASP.NET": 0,
    "SQL": 1,
    "C#": 2,
    "TypeScript": 3,
    "JavaScript": 4,
    "Python": 5,
    "Go": 6,
    "Rust": 7,
    "Java": 8,
    "Kotlin": 9,
    "Delphi/Pascal": 20,
    "Batch": 21,
}


_REPRESENTATIVE_SUFFIX_PRIORITY = {
    ".sln": 0,
    ".csproj": 1,
    ".aspx": 2,
    ".asmx": 2,
    ".ashx": 2,
    ".ascx": 2,
    ".sql": 3,
    ".prc": 3,
    ".vw": 3,
    ".pck": 3,
    ".seq": 3,
    ".bat": 4,
    ".cmd": 4,
    ".config": 5,
    ".xml": 5,
    ".yml": 5,
    ".yaml": 5,
    ".cs": 6,
    ".pas": 6,
    ".dfm": 6,
}
_SOURCE_MODULE_NAMES = {"app", "apps", "lib", "libs", "package", "packages", "source", "src"}
_DATABASE_MODULE_NAMES = {"data", "database", "databases", "db", "sql"}
_DATABASE_PATH_PARTS = {"database", "databases", "db", "migration", "migrations", "schema", "schemas", "sql"}
_AUTOMATION_MODULE_NAMES = {"build", "ci", "cd", "deploy", "pipeline", "pipelines", "release", "scripts"}
_AUTOMATION_PATH_PARTS = {"build", "ci", "cd", "deploy", "pipeline", "pipelines", "release", "scripts"}
_DATABASE_SUFFIXES = {".sql", ".prc", ".vw", ".pck", ".seq"}
_AUTOMATION_SUFFIXES = {".bat", ".cmd"}
_SIGNAL_PRIORITY = [
    "aspnet-web",
    "application-source",
    "database-scripts",
    "dotnet-project",
    "release-automation",
    "pipeline-config",
    "server-service",
    "client-app",
    "shared-library",
    "business-module",
    "configuration-heavy",
]


def _top_level_module(path: str) -> str | None:
    if "/" not in path:
        return None
    return path.split("/", 1)[0] + "/"


def _ordered_module_languages(records: list) -> list[str]:
    counts = Counter(record.language for record in records if record.language != "Unknown")
    return [
        language
        for language, _ in sorted(counts.items(), key=lambda item: (-item[1], _LANGUAGE_PRIORITY.get(item[0], 99), item[0]))
    ]


def _representative_path_penalty(path: str) -> int:
    lowered = path.lower()
    if "/examples/" in lowered or "/samples/" in lowered:
        return 40
    if "/tools/" in lowered or "/vendor/" in lowered:
        return 30
    return 0


def _representative_category(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".aspx", ".asmx", ".ashx", ".ascx"}:
        return "aspnet"
    if suffix in {".sql", ".prc", ".vw", ".pck", ".seq"}:
        return "database"
    if suffix in {".bat", ".cmd"}:
        return "automation"
    if suffix in {".config", ".xml", ".yml", ".yaml"}:
        return "configuration"
    if suffix in {".cs", ".pas", ".dfm"}:
        return "source"
    return suffix or "other"


def _representative_paths(records: list) -> list[str]:
    def sort_key(record) -> tuple[int, int, str]:
        suffix = Path(record.path).suffix.lower()
        return (_representative_path_penalty(record.path), _REPRESENTATIVE_SUFFIX_PRIORITY.get(suffix, 99), record.path)

    ordered = sorted(records, key=sort_key)
    selected: list[str] = []
    used_categories: set[str] = set()
    for record in ordered:
        category = _representative_category(record.path)
        if category in used_categories:
            continue
        selected.append(record.path)
        used_categories.add(category)
        if len(selected) == 6:
            return selected
    for record in ordered:
        if record.path in selected:
            continue
        selected.append(record.path)
        if len(selected) == 6:
            return selected
    return selected


def _name_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _module_signals(name: str, records: list, role_counts: Counter[str]) -> list[str]:
    base_name = name.rstrip("/")
    lowered_name = base_name.lower()
    tokens = _name_tokens(lowered_name)
    path_parts = [set(Path(record.path.lower()).parts) for record in records]
    suffixes = {Path(record.path).suffix.lower() for record in records}
    languages = {record.language for record in records}
    source_count = role_counts["source"]
    non_source_count = role_counts["configuration"] + role_counts["documentation"] + role_counts["test"]
    source_dominant = (
        source_count > 0
        and lowered_name not in _DATABASE_MODULE_NAMES
        and lowered_name not in _AUTOMATION_MODULE_NAMES
        and (lowered_name in _SOURCE_MODULE_NAMES or source_count >= max(1, non_source_count))
    )
    database_file_count = sum(1 for record in records if Path(record.path).suffix.lower() in _DATABASE_SUFFIXES)
    database_path_count = sum(1 for parts in path_parts if parts & _DATABASE_PATH_PARTS)
    database_script_ratio = database_file_count / max(source_count, 1)
    database_script_dense = database_file_count >= 3 and database_script_ratio >= 0.05
    database_path_dense = database_file_count >= 1 and database_path_count >= 3 and database_script_ratio >= 0.05
    automation_file_count = sum(1 for record in records if Path(record.path).suffix.lower() in _AUTOMATION_SUFFIXES)
    raw: set[str] = set()

    if "ASP.NET" in languages or suffixes & {".aspx", ".asmx", ".ashx", ".ascx"} or lowered_name == "web":
        raw.add("aspnet-web")
    if source_dominant:
        raw.add("application-source")
    if lowered_name in _DATABASE_MODULE_NAMES or database_script_dense or database_path_dense:
        raw.add("database-scripts")
    if ".sln" in suffixes or ".csproj" in suffixes or ".NET project" in languages:
        raw.add("dotnet-project")
    if lowered_name in _AUTOMATION_MODULE_NAMES or (tokens & _AUTOMATION_PATH_PARTS) or (automation_file_count >= 2 and not source_dominant):
        raw.add("release-automation")
    if lowered_name in {"pipeline", "pipelines", "ci", "cd"} or tokens & {"pipeline", "pipelines", "ci", "cd"}:
        raw.add("pipeline-config")
    if {"server", "service", "gateway"} & tokens or lowered_name.endswith("server"):
        raw.add("server-service")
    if {"client", "ui", "desktop"} & tokens or lowered_name == "client":
        raw.add("client-app")
    if {"share", "shared", "common", "library"} & tokens or any(part in lowered_name for part in {"shared", "common", "library"}):
        raw.add("shared-library")
    segmented_enterprise_name = "_" in lowered_name and any(character.isdigit() for character in lowered_name)
    if segmented_enterprise_name or {"business", "biz", "manage"} & tokens or lowered_name.endswith("manage"):
        raw.add("business-module")
    if role_counts["configuration"] > role_counts["source"] and role_counts["configuration"] > 0:
        raw.add("configuration-heavy")

    return [signal for signal in _SIGNAL_PRIORITY if signal in raw]


def _module_summary_text(name: str, signals: list[str]) -> str:
    lowered_name = name.rstrip("/").lower()
    if lowered_name in {"build", "deploy", "release", "pipeline", "pipelines", "ci", "cd"}:
        return "Build, release, or deployment automation module."
    if "server-service" in signals:
        return "Server-side service or backend runtime module."
    if "client-app" in signals:
        return "Client application module inferred from module naming and file-type signals."
    if "shared-library" in signals:
        return "Shared library or common framework module used across repository capabilities."
    if "aspnet-web" in signals:
        return "ASP.NET web application surface with pages, handlers, services, and configuration."
    if "application-source" in signals:
        return "Application source module inferred from dominant source files."
    if "database-scripts" in signals:
        return "Database schema and script layer with SQL objects or migration-like assets."
    if "release-automation" in signals or "pipeline-config" in signals:
        return "Build, release, or deployment automation module."
    if "business-module" in signals:
        return "Application or business capability module inferred from module naming."
    if lowered_name in {"center", "core"}:
        return "Core coordination module inferred from top-level layout and project files."
    return "Repository module inferred from top-level layout and file-type signals."


def _build_module_summaries(scan: ScanResult) -> list[ModuleSummary]:
    grouped = defaultdict(list)
    for record in scan.files:
        module = _top_level_module(record.path)
        if module is not None:
            grouped[module].append(record)

    modules: list[ModuleSummary] = []
    for name, records in grouped.items():
        role_counts = Counter(record.role for record in records)
        signals = _module_signals(name, records, role_counts)
        modules.append(
            ModuleSummary(
                name=name,
                total=len(records),
                source=role_counts["source"],
                configuration=role_counts["configuration"],
                documentation=role_counts["documentation"],
                test=role_counts["test"],
                languages=_ordered_module_languages(records),
                signals=signals,
                summary=_module_summary_text(name, signals),
                representative_paths=_representative_paths(records),
            )
        )

    return sorted(modules, key=lambda module: (-module.total, module.name))[:12]


def _has_any_signal(module: ModuleSummary, signals: set[str]) -> bool:
    return any(signal in module.signals for signal in signals)


def _relationship_evidence(source: ModuleSummary, target: ModuleSummary) -> list[str]:
    evidence = []
    evidence.extend(source.representative_paths[:2])
    evidence.extend(target.representative_paths[:2])
    return list(dict.fromkeys(evidence))[:4]


def _is_automation_owner(module: ModuleSummary) -> bool:
    lowered_name = module.name.rstrip("/").lower()
    tokens = _name_tokens(lowered_name)
    return bool(
        "pipeline-config" in module.signals
        or lowered_name in {"build", "deploy", "release", "pipeline", "pipelines", "ci", "cd"}
        or {"build", "deploy", "release", "pipeline", "pipelines"} & tokens
    )


_TEST_MODULE_TOKENS = {"spec", "specs", "test", "tests"}


def _relationship_name_tokens(module: ModuleSummary) -> set[str]:
    return _name_tokens(module.name.rstrip("/")) - _TEST_MODULE_TOKENS


def _build_module_relationships(modules: list[ModuleSummary]) -> list[ModuleRelationship]:
    automation_modules = [module for module in modules if _is_automation_owner(module)]
    app_modules = [module for module in modules if _has_any_signal(module, {"application-source", "aspnet-web", "client-app", "server-service", "business-module"})]
    database_modules = [module for module in modules if "database-scripts" in module.signals]
    shared_modules = [module for module in modules if "shared-library" in module.signals]
    relationships: dict[tuple[str, str, str], ModuleRelationship] = {}

    for source in automation_modules:
        for target in app_modules[:4]:
            if source.name == target.name:
                continue
            key = (source.name, target.name, "builds-or-deploys")
            relationships[key] = ModuleRelationship(
                source=source.name,
                target=target.name,
                relation="builds-or-deploys",
                reason="Automation or pipeline module is likely to build, package, or deploy application-facing modules.",
                evidence=_relationship_evidence(source, target),
            )

    for source in app_modules:
        for target in database_modules[:3]:
            if source.name == target.name:
                continue
            key = (source.name, target.name, "uses-data-assets")
            relationships[key] = ModuleRelationship(
                source=source.name,
                target=target.name,
                relation="uses-data-assets",
                reason="Application-facing module and database-script module coexist, so data assets are likely part of behavior changes.",
                evidence=_relationship_evidence(source, target),
            )

    for source in app_modules:
        for target in shared_modules[:3]:
            if source.name == target.name:
                continue
            key = (source.name, target.name, "depends-on-shared-code")
            relationships[key] = ModuleRelationship(
                source=source.name,
                target=target.name,
                relation="depends-on-shared-code",
                reason="Application-facing module should be checked with shared or common library modules when changing cross-cutting behavior.",
                evidence=_relationship_evidence(source, target),
            )

    source_modules = [module for module in modules if module.source > 0]
    test_modules = [module for module in modules if module.test > module.source and module.test > 0]
    for source in test_modules:
        source_tokens = _relationship_name_tokens(source)
        if not source_tokens:
            continue
        for target in source_modules:
            target_tokens = _relationship_name_tokens(target)
            if source.name == target.name or not target_tokens or not source_tokens.intersection(target_tokens):
                continue
            key = (source.name, target.name, "validates")
            relationships[key] = ModuleRelationship(
                source=source.name,
                target=target.name,
                relation="validates",
                reason="Test-heavy module name overlaps a source module name.",
                evidence=_relationship_evidence(source, target),
            )

    return sorted(relationships.values(), key=lambda item: (item.source, item.target, item.relation))[:24]


def _module_names(modules: list[ModuleSummary], signals: set[str], limit: int = 6) -> list[str]:
    return [module.name for module in modules if _has_any_signal(module, signals)][:limit]


def _build_task_entry_guide(modules: list[ModuleSummary], relationships: list[ModuleRelationship]) -> list[TaskGuideItem]:
    app_modules = _module_names(modules, {"application-source", "aspnet-web", "client-app", "server-service", "business-module"})
    database_modules = sorted(
        _module_names(modules, {"database-scripts"}, 4), key=lambda name: (0 if name.rstrip("/").lower() in {"db", "database", "sql"} else 1, name)
    )
    automation_modules = [module.name for module in modules if _is_automation_owner(module)][:4]
    shared_modules = _module_names(modules, {"shared-library"}, 4)
    guides: list[TaskGuideItem] = []

    if app_modules:
        start_with = app_modules[:6]
        then_check = [name for name in list(dict.fromkeys(database_modules + shared_modules + automation_modules)) if name not in start_with][:8]
        guides.append(
            TaskGuideItem(
                task="Change application behavior",
                start_with=start_with,
                then_check=then_check,
                rationale="Start from application-facing modules, then review related data assets, shared code, and automation paths indicated by repository signals.",
            )
        )
    if database_modules:
        related_apps = sorted({relationship.source for relationship in relationships if relationship.relation == "uses-data-assets"})[:6]
        then_check = [name for name in list(dict.fromkeys(related_apps + automation_modules)) if name not in database_modules][:8]
        guides.append(
            TaskGuideItem(
                task="Change database or persistence assets",
                start_with=database_modules,
                then_check=then_check,
                rationale="Database-script modules should be reviewed with application modules that may depend on those data assets.",
            )
        )
    if automation_modules:
        guides.append(
            TaskGuideItem(
                task="Change build or release automation",
                start_with=automation_modules,
                then_check=app_modules[:8],
                rationale="Automation modules are inferred to build or deploy application-facing modules.",
            )
        )
    if shared_modules:
        related_apps = sorted({relationship.source for relationship in relationships if relationship.relation == "depends-on-shared-code"})[:6]
        guides.append(
            TaskGuideItem(
                task="Change shared code",
                start_with=shared_modules,
                then_check=[name for name in related_apps if name not in shared_modules],
                rationale="Shared or common modules may affect several application-facing modules.",
            )
        )

    return sorted(guides, key=lambda item: item.task)


def _module_paths(modules: list[ModuleSummary], signals: set[str], limit: int = 8) -> list[str]:
    paths: list[str] = []
    for module in modules:
        if not _has_any_signal(module, signals):
            continue
        paths.extend(module.representative_paths[:2])
    return list(dict.fromkeys(paths))[:limit]


_BLOCKED_COMMAND_PATTERNS = (
    re.compile(r"https?://"),
    re.compile(r"\b(curl|wget)\b"),
    re.compile(r"\b(git\s+clone|gh\s+repo\s+clone)\b"),
    re.compile(r"\binstall\b"),
    re.compile(r"\b(npm|pnpm|yarn|bun)\s+(add|ci|dlx|exec|i)\b"),
    re.compile(r"\b(npx|bunx)\b"),
    re.compile(r"\buv\s+(pip\s+install|sync)\b"),
    re.compile(r"\b(dotnet|nuget)\s+(tool\s+)?restore\b"),
    re.compile(r"\bgo\s+(get|mod\s+download)\b"),
    re.compile(r"\b(cargo\s+fetch|pip\s+download)\b"),
)


def _safe_commands(commands: list[str]) -> list[str]:
    safe: list[str] = []
    for command in commands:
        lowered = command.lower()
        if any(pattern.search(lowered) for pattern in _BLOCKED_COMMAND_PATTERNS):
            continue
        safe.append(command)
    return safe


def _build_validation_guide(test_commands: list[str], run_commands: list[str], modules: list[ModuleSummary]) -> list[ValidationGuideItem]:
    guides: list[ValidationGuideItem] = []
    safe_test_commands = _safe_commands(test_commands)
    safe_run_commands = _safe_commands(run_commands)
    if safe_test_commands or safe_run_commands:
        guides.append(
            ValidationGuideItem(
                scope="Repository commands",
                commands=safe_test_commands + safe_run_commands,
                paths=[],
                notes=["Use existing detected commands only; do not install dependencies or call remote services from generated guidance."],
            )
        )

    review_paths = _module_paths(
        modules,
        {"application-source", "aspnet-web", "client-app", "server-service", "database-scripts", "release-automation", "pipeline-config", "shared-library"},
    )
    if review_paths:
        guides.append(
            ValidationGuideItem(
                scope="Module static review",
                commands=[],
                paths=review_paths,
                notes=["Review representative paths for affected modules when executable local validation is unavailable or incomplete."],
            )
        )

    database_paths = _module_paths(modules, {"database-scripts"}, 6)
    if database_paths:
        guides.append(
            ValidationGuideItem(
                scope="Database asset review",
                commands=[],
                paths=database_paths,
                notes=["Check schema or script changes together with application modules that use data assets."],
            )
        )

    automation_paths = _module_paths(modules, {"release-automation", "pipeline-config"}, 6)
    if automation_paths:
        guides.append(
            ValidationGuideItem(
                scope="Build and release review",
                commands=[],
                paths=automation_paths,
                notes=["Check build or release automation when changes touch deployed application modules."],
            )
        )

    return sorted(guides, key=lambda item: item.scope)


def build_project_profile(scan: ScanResult, root: Path | None = None) -> ProjectProfile:
    name = "local-repository"
    description = "Local-first repository skill generated from static analysis."
    if root is not None:
        metadata_name, metadata_description = _pyproject_metadata(root)
        name = metadata_name or root.name
        description = metadata_description or description
    elif any(record.path == "pyproject.toml" for record in scan.files):
        name = "tiny-python-app"
        description = "Python project detected from pyproject.toml."

    source_files = sorted(record.path for record in scan.files if record.role == "source")
    test_files = sorted(record.path for record in scan.files if record.role == "test")
    configuration_files = sorted(record.path for record in scan.files if record.role == "configuration")
    documentation_files = sorted(record.path for record in scan.files if record.role == "documentation")
    primary_language = _primary_language(scan)
    test_commands = [command for command in scan.candidate_commands if "test" in command or "pytest" in command]
    if primary_language == "Python" and test_files and "python -m pytest" not in test_commands:
        test_commands.append("python -m pytest")
    test_commands = sorted(_safe_commands(test_commands))
    run_commands = _safe_commands(
        [command for command in scan.candidate_commands if "test" not in command and "pytest" not in command]
    )
    module_summaries = _build_module_summaries(scan)
    module_relationships = _build_module_relationships(module_summaries)

    return ProjectProfile(
        name=name,
        description=description,
        primary_language=primary_language,
        languages=_ordered_languages(scan, primary_language),
        ecosystems=scan.ecosystems,
        package_managers=scan.package_managers,
        test_commands=test_commands,
        run_commands=run_commands,
        entrypoints=scan.entrypoints,
        configuration_files=configuration_files,
        documentation_files=documentation_files,
        source_files=source_files,
        test_files=test_files,
        module_summaries=module_summaries,
        module_relationships=module_relationships,
        task_entry_guide=_build_task_entry_guide(module_summaries, module_relationships),
        validation_guide=_build_validation_guide(test_commands, run_commands, module_summaries),
    )
