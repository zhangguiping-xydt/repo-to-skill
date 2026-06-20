from __future__ import annotations

from pathlib import Path

DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".runs",
    ".claude",
    ".vs",
    "graphify-out",
    "Artifacts",
    "node_modules",
    "bin",
    "obj",
    "target",
    "dist",
    "build",
    "out",
    "coverage",
    ".tmp",
    "tmp",
    "bundles",
    ".gradle",
    ".next",
    ".nuxt",
    ".svelte-kit",
    ".expo",
    ".idea",
    ".vscode",
}

SENSITIVE_FILENAMES = {
    ".env",
    ".npmrc",
    ".pypirc",
    "id_rsa",
    "credentials.json",
    "secrets.json",
}

SENSITIVE_SUFFIXES = {".pem", ".key"}


def should_skip_dir(path: Path) -> bool:
    return path.name in DEFAULT_SKIP_DIRS


def is_sensitive_file(path: Path) -> bool:
    name = path.name
    return name in SENSITIVE_FILENAMES or any(name.endswith(suffix) for suffix in SENSITIVE_SUFFIXES)
