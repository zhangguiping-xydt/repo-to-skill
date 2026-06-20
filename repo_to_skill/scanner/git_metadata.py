from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git(root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return completed.stdout.strip()


def get_git_metadata(root: Path) -> dict[str, Any]:
    branch = _git(root, "branch", "--show-current")
    head = _git(root, "rev-parse", "--short", "HEAD")
    status = _git(root, "status", "--porcelain")
    if branch is None and head is None and status is None:
        return {"available": False, "branch": None, "head": None, "dirty": None}
    return {
        "available": True,
        "branch": branch or None,
        "head": head or None,
        "dirty": bool(status),
    }
