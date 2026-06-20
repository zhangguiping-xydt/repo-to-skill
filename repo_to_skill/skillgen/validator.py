from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


REQUIRED_FILES = (
    "manifest.yaml",
    "SKILL.md",
    "scripts/inspect_repo.py",
    "scripts/common.py",
    "references/project-map.md",
    "references/capability-graph.md",
    "references/skill-spec.md",
    "references/confidence-report.md",
)

DANGEROUS_SCRIPT_TOKENS = (
    "subprocess",
    "os.system",
    "os.popen",
    "shutil.rmtree",
    "shutil.move",
    "shutil.copy",
    "requests",
    "urllib",
    "socket",
    "http.client",
    "ftplib",
    "open(",
    "write_text",
    "write_bytes",
    "unlink",
    "os.remove",
    "os.unlink",
    "rename",
    "replace",
    "pip",
    "npm",
    "exec(",
    "eval(",
    "pty",
)

MANIFEST_BANNED_TOKENS = (
    "CapabilityRegistry",
    "FastAPI",
    "runtime hot registration",
    "hot registration",
    "multi-agent-dev",
    "vector database",
    "remote database",
)

REQUIRED_MANIFEST_SAFETY = {
    "read_only": True,
    "network": "disabled",
    "dependency_install": "disabled",
    "target_repository_writes": "disabled",
}

MACHINE_PATH_PATTERNS = (
    re.compile(r"/media/"),
    re.compile(r"/home/"),
    re.compile(r"/tmp(?:/|\b)"),
)


@dataclass(frozen=True)
class SkillValidationReport:
    status: str
    findings: list[str] = field(default_factory=list)


_SCRIPT_WRITE_MODE_RE = re.compile(r"open\s*\([^\n]*[\"'](?:w|a|x|\+)[\"']")


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _check_required_files(root: Path, findings: list[str]) -> None:
    for relative in REQUIRED_FILES:
        path = root / relative
        if not path.is_file():
            findings.append(f"missing required file: {relative}")


def _check_scripts(root: Path, findings: list[str]) -> None:
    for relative in ("scripts/inspect_repo.py", "scripts/common.py"):
        path = root / relative
        if not path.is_file():
            continue
        content = _text(path)
        for token in DANGEROUS_SCRIPT_TOKENS:
            if token in content:
                findings.append(f"dangerous token in {relative}: {token}")
        if _SCRIPT_WRITE_MODE_RE.search(content):
            findings.append(f"dangerous token in {relative}: writable open mode")


def _check_manifest(root: Path, findings: list[str]) -> None:
    path = root / "manifest.yaml"
    if not path.is_file():
        return
    content = _text(path)
    try:
        manifest = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        findings.append(f"invalid manifest.yaml: {exc}")
        return
    if not isinstance(manifest, dict):
        findings.append("invalid manifest.yaml: root must be a mapping")
        return
    for key in ("name", "description", "version", "source_project", "capabilities", "generated_by"):
        if key not in manifest:
            findings.append(f"manifest.yaml missing field: {key}")
    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        findings.append("manifest.yaml missing safety boundary: safety")
    else:
        for key, expected in REQUIRED_MANIFEST_SAFETY.items():
            actual = safety.get(key)
            if actual != expected:
                findings.append(f"manifest.yaml safety.{key} must be {expected!r}")
    for token in MANIFEST_BANNED_TOKENS:
        if token in content:
            findings.append(f"manifest.yaml contains runtime registration or remote dependency token: {token}")


def _check_machine_paths(root: Path, findings: list[str]) -> None:
    checked = [root / "SKILL.md"] + sorted((root / "references").glob("**/*"))
    for path in checked:
        if not path.is_file():
            continue
        content = _text(path)
        for pattern in MACHINE_PATH_PATTERNS:
            if pattern.search(content):
                findings.append(f"machine absolute path found in {path.relative_to(root)}: {pattern.pattern}")


def validate_skill(skill_path: Path) -> SkillValidationReport:
    root = skill_path.expanduser().resolve()
    findings: list[str] = []
    if not root.exists() or not root.is_dir():
        return SkillValidationReport(status="FAIL", findings=["skill path must be an existing directory"])

    _check_required_files(root, findings)
    _check_scripts(root, findings)
    _check_manifest(root, findings)
    _check_machine_paths(root, findings)

    return SkillValidationReport(status="PASS" if not findings else "FAIL", findings=findings)
