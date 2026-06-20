from __future__ import annotations

import hashlib
from pathlib import Path

from repo_to_skill.models import FileRecord, ScanResult
from repo_to_skill.scanner.git_metadata import get_git_metadata
from repo_to_skill.scanner.ignore_rules import is_sensitive_file, should_skip_dir
from repo_to_skill.scanner.language_detect import detect_file_language, detect_project_signals

MAX_FILE_SIZE = 1024 * 1024


def _is_binary(data: bytes) -> bool:
    return b"\x00" in data[:4096]


def _line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def scan_repository(root: Path) -> ScanResult:
    root = root.expanduser().resolve()
    signals = detect_project_signals(root)
    files: list[FileRecord] = []
    skipped: list[str] = []

    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            skipped.append(f"{rel}: symlink")
            continue
        if path.is_dir():
            continue
        if any(should_skip_dir(part) for part in path.relative_to(root).parents if part.name != "."):
            skipped.append(rel)
            continue
        if is_sensitive_file(path):
            skipped.append(rel)
            continue
        try:
            size = path.stat().st_size
        except OSError:
            skipped.append(rel)
            continue
        if size > MAX_FILE_SIZE:
            skipped.append(rel)
            continue
        try:
            data = path.read_bytes()
        except OSError:
            skipped.append(rel)
            continue
        if _is_binary(data):
            skipped.append(rel)
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(rel)
            continue
        language, role = detect_file_language(Path(rel))
        files.append(
            FileRecord(
                path=rel,
                size=size,
                line_count=_line_count(text),
                sha256=hashlib.sha256(data).hexdigest(),
                language=language,
                role=role,
            )
        )

    file_languages = {record.language for record in files if record.language != "Unknown"}
    languages = sorted(set(signals["languages"]) | file_languages)
    return ScanResult(
        root="<target>",
        files=files,
        skipped=sorted(set(skipped)),
        languages=languages,
        ecosystems=signals["ecosystems"],
        package_managers=signals["package_managers"],
        candidate_commands=signals["candidate_commands"],
        entrypoints=signals["entrypoints"],
        git=get_git_metadata(root),
    )
