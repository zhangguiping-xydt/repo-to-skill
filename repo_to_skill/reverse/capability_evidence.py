from __future__ import annotations

from pathlib import Path

from repo_to_skill.models import CapabilityEvidence, Claim, Evidence, ProjectProfile, ScanResult

_SOURCE_LIMIT = 8
_ARCHITECTURE_MODULE_SIGNALS = {
    "application-source",
    "aspnet-web",
    "database-scripts",
    "server-service",
    "client-app",
    "shared-library",
    "business-module",
    "release-automation",
    "pipeline-config",
}


def _matching_sources(paths: list[str], suffixes: set[str] | None = None, prefixes: set[str] | None = None) -> list[str]:
    values: list[str] = []
    for path in paths:
        suffix = Path(path).suffix.lower()
        top = path.split("/", 1)[0]
        if suffixes is not None and suffix not in suffixes:
            continue
        if prefixes is not None and top not in prefixes and not any(top.startswith(prefix) for prefix in prefixes if prefix.endswith("*")):
            continue
        values.append(path)
    return values[:_SOURCE_LIMIT]


def build_capability_evidence(profile: ProjectProfile, scan: ScanResult) -> CapabilityEvidence:
    evidence: list[Evidence] = []

    if profile.entrypoints:
        evidence.append(
            Evidence(
                name="cli",
                kind="interface",
                summary="Project exposes command-line entrypoints.",
                sources=profile.entrypoints,
                confidence=0.9,
            )
        )
        evidence.append(
            Evidence(
                name="entrypoint",
                kind="runtime",
                summary="Entrypoint declarations identify runnable commands.",
                sources=profile.entrypoints,
                confidence=0.9,
            )
        )

    if profile.test_commands or profile.test_files:
        evidence.append(
            Evidence(
                name="test",
                kind="quality",
                summary="Project contains tests or test commands.",
                sources=profile.test_commands + profile.test_files[:_SOURCE_LIMIT],
                confidence=0.85,
            )
        )

    if profile.package_managers:
        evidence.append(
            Evidence(
                name="package_manager",
                kind="build",
                summary="Package manager or build metadata is present.",
                sources=profile.package_managers,
                confidence=0.85,
            )
        )

    dotnet_sources = _matching_sources(profile.configuration_files, {".sln", ".csproj"})
    if dotnet_sources or "msbuild" in profile.package_managers:
        evidence.append(
            Evidence(
                name="dotnet_project",
                kind="build",
                summary=".NET solution or project metadata is available for build and module orientation.",
                sources=dotnet_sources or ["msbuild"],
                confidence=0.88,
            )
        )

    web_sources = _matching_sources(profile.source_files, {".aspx", ".ascx", ".asmx", ".ashx"})
    if web_sources or any(path.startswith("Web/") for path in profile.source_files):
        evidence.append(
            Evidence(
                name="web_app",
                kind="interface",
                summary="Web application surfaces are present in ASP.NET or web-oriented paths.",
                sources=web_sources or _matching_sources(profile.source_files, prefixes={"Web"}),
                confidence=0.84,
            )
        )

    database_sources = _matching_sources(profile.source_files, {".sql"})
    if database_sources or any(path.startswith("DB/") for path in profile.source_files):
        evidence.append(
            Evidence(
                name="database",
                kind="data",
                summary="Database scripts or schema-oriented files are part of the repository knowledge.",
                sources=database_sources or _matching_sources(profile.source_files, prefixes={"DB"}),
                confidence=0.82,
            )
        )

    release_sources = [path for path in profile.source_files if Path(path).suffix.lower() in {".bat", ".cmd"} or Path(path).name.lower().startswith("release_")][:_SOURCE_LIMIT]
    if release_sources:
        evidence.append(
            Evidence(
                name="release_scripts",
                kind="build",
                summary="Release or operational scripts are present and should be treated as repository knowledge.",
                sources=release_sources,
                confidence=0.78,
            )
        )

    architecture_modules = [
        module.name.rstrip("/")
        for module in profile.module_summaries
        if any(signal in _ARCHITECTURE_MODULE_SIGNALS for signal in module.signals)
    ][:_SOURCE_LIMIT]
    if architecture_modules:
        evidence.append(
            Evidence(
                name="architecture_modules",
                kind="architecture",
                summary="Multiple top-level source, application, or operational modules are visible in the repository layout.",
                sources=architecture_modules,
                confidence=0.8,
            )
        )

    if profile.configuration_files:
        evidence.append(
            Evidence(
                name="configuration",
                kind="configuration",
                summary="Configuration files are available for static analysis.",
                sources=profile.configuration_files[:_SOURCE_LIMIT],
                confidence=0.75,
            )
        )

    if profile.documentation_files:
        evidence.append(
            Evidence(
                name="documentation",
                kind="documentation",
                summary="Documentation files are available.",
                sources=profile.documentation_files[:_SOURCE_LIMIT],
                confidence=0.7,
            )
        )

    evidence = sorted(evidence, key=lambda item: item.name)
    claims = [
        Claim(
            name=item.name,
            description=item.summary,
            evidence=item.sources,
            confidence=item.confidence,
        )
        for item in evidence
    ]
    return CapabilityEvidence(project=profile.name, evidence=evidence, claims=claims)
