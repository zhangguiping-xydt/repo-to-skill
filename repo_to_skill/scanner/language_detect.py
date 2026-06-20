from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from repo_to_skill.scanner.ignore_rules import should_skip_dir

LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".aspx": "ASP.NET",
    ".ascx": "ASP.NET",
    ".asmx": "ASP.NET",
    ".ashx": "ASP.NET",
    ".sql": "SQL",
    ".pas": "Delphi/Pascal",
    ".dpr": "Delphi/Pascal",
    ".dfm": "Delphi/Pascal",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".xml": "XML",
    ".config": "XML",
    ".resx": "XML",
    ".csproj": ".NET project",
    ".sln": ".NET project",
    ".bat": "Batch",
    ".cmd": "Batch",
}

CONFIG_NAMES = {
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "package.json",
    "go.mod",
    "Cargo.toml",
}
CONFIG_SUFFIXES = {
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
    ".config",
    ".resx",
    ".csproj",
    ".sln",
}
DOC_NAMES = {"README.md", "README.rst", "CHANGELOG.md", "CONTRIBUTING.md"}
DOTNET_SUFFIXES = {".sln", ".csproj"}


def detect_file_language(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    language = LANGUAGE_BY_SUFFIX.get(suffix, "Unknown")
    parts = set(path.parts)
    name = path.name
    if name in DOC_NAMES or suffix in {".md", ".rst"}:
        role = "documentation"
    elif "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
        role = "test"
    elif name in CONFIG_NAMES or suffix in CONFIG_SUFFIXES:
        role = "configuration"
    else:
        role = "source"
    return language, role


def _read_pyproject(root: Path) -> dict[str, Any]:
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return {}
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
        return {}


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(should_skip_dir(Path(part)) for part in relative.parts[:-1]):
            continue
        yield path


def detect_project_signals(root: Path) -> dict[str, list[str]]:
    languages: set[str] = set()
    ecosystems: set[str] = set()
    package_managers: set[str] = set()
    commands: set[str] = set()
    entrypoints: set[str] = set()

    pyproject_data = _read_pyproject(root)
    if pyproject_data:
        languages.add("Python")
        ecosystems.add("python")
        package_managers.add("python-build")
        project = pyproject_data.get("project", {})
        scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
        for name, target in scripts.items():
            entrypoints.add(f"{name} = {target}")
        tool = pyproject_data.get("tool", {})
        if isinstance(tool, dict) and "pytest" in tool:
            commands.add("python -m pytest")

    if (root / "requirements.txt").exists() or (root / "setup.py").exists():
        languages.add("Python")
        ecosystems.add("python")
        commands.add("python -m pytest")

    if (root / "package.json").exists():
        languages.add("JavaScript")
        ecosystems.add("node")
        package_managers.add("npm")
        commands.add("npm test")

    if (root / "go.mod").exists():
        languages.add("Go")
        ecosystems.add("go")
        package_managers.add("go")
        commands.add("go test ./...")

    if (root / "Cargo.toml").exists():
        languages.add("Rust")
        ecosystems.add("rust")
        package_managers.add("cargo")
        commands.add("cargo test")

    dotnet_files = sorted(path.relative_to(root).as_posix() for path in _iter_files(root) if path.suffix.lower() in DOTNET_SUFFIXES)
    if dotnet_files:
        languages.add("C#")
        ecosystems.add("dotnet")
        package_managers.add("msbuild")
        solution = next((path for path in dotnet_files if path.endswith(".sln")), "")
        if solution:
            commands.add(f"msbuild {solution}")
        else:
            commands.add(f"dotnet build {dotnet_files[0]}")

    return {
        "languages": sorted(languages),
        "ecosystems": sorted(ecosystems),
        "package_managers": sorted(package_managers),
        "candidate_commands": sorted(commands),
        "entrypoints": sorted(entrypoints),
    }
