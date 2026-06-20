from __future__ import annotations

from repo_to_skill.models import CapabilityEvidence, ProjectProfile, VerificationReport


_CAPABILITY_LABELS = {
    "architecture_modules": "architecture modules",
    "cli": "CLI",
    "configuration": "configuration",
    "database": "database scripts",
    "documentation": "documentation",
    "dotnet_project": ".NET project",
    "enterprise_modules": "architecture modules",
    "entrypoint": "entrypoints",
    "package_manager": "package manager",
    "release_scripts": "release scripts",
    "test": "tests",
    "web_app": "web application",
}


def _capability_label(name: str) -> str:
    return _CAPABILITY_LABELS.get(name, name.replace("_", " "))


def build_confidence_report(profile: ProjectProfile, evidence: CapabilityEvidence, report: VerificationReport) -> str:
    lines = [
        f"# Confidence Report: {profile.name}",
        "",
        f"Status: {report.status}",
        f"Primary language: {profile.primary_language}",
        "",
        "## Capabilities",
    ]
    for item in evidence.evidence:
        lines.append(f"- {_capability_label(item.name)}: {item.summary} (confidence {item.confidence:.2f})")
    lines.extend(["", "## Verification"])
    for finding in report.findings:
        lines.append(f"- {finding}")
    lines.append("")
    return "\n".join(lines)
