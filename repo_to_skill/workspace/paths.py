from __future__ import annotations

from pathlib import Path


def resolve_target_and_output(target: Path, output: Path) -> tuple[Path, Path]:
    target_root = target.expanduser().resolve()
    output_root = output.expanduser().resolve()
    if not target_root.exists() or not target_root.is_dir():
        raise ValueError("target repository must be an existing directory")
    if output_root == target_root or target_root in output_root.parents:
        raise ValueError("output must be outside target repository")
    return target_root, output_root
