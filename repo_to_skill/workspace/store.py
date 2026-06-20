from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from repo_to_skill.workspace.paths import resolve_target_and_output


def _dumpable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class ArtifactStore:
    def __init__(self, target_root: Path, output_root: Path) -> None:
        self.target_root, self.output_root = resolve_target_and_output(target_root, output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        path = (self.output_root / name).resolve()
        if self.output_root not in path.parents and path != self.output_root:
            raise ValueError("artifact path must stay inside output directory")
        return path

    def write_json(self, name: str, value: Any) -> Path:
        path = self._path(name)
        path.write_text(
            json.dumps(_dumpable(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def write_yaml(self, name: str, value: Any) -> Path:
        path = self._path(name)
        path.write_text(
            yaml.safe_dump(_dumpable(value), allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return path

    def write_markdown(self, name: str, content: str) -> Path:
        path = self._path(name)
        path.write_text(content, encoding="utf-8")
        return path
