from __future__ import annotations

import shutil
from pathlib import Path

# Standard cross-agent skill install locations. Claude Code discovers skills in
# ~/.claude/skills; pi and other agents use ~/.agents/skills. Installing into
# both makes one generated skill usable by either runtime without manual copying.
AGENT_SKILL_DIRS: dict[str, Path] = {
    "claude-code": Path(".claude") / "skills",
    "agents": Path(".agents") / "skills",
}


def agent_skill_root(agent: str, home: Path | None = None) -> Path:
    """Return the skills directory for one agent under the given home."""
    if agent not in AGENT_SKILL_DIRS:
        raise ValueError(f"unknown agent target: {agent}")
    base = (home or Path.home()).expanduser()
    return base / AGENT_SKILL_DIRS[agent]


def install_skill(
    skill_root: Path,
    *,
    agents: list[str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    """Copy a generated skill directory into agent skill locations.

    Returns the installed destination directories. An existing skill with the
    same slug is replaced. The source skill directory is never modified.
    """
    skill_root = skill_root.expanduser().resolve()
    if not skill_root.is_dir():
        raise ValueError(f"skill directory does not exist: {skill_root}")

    selected = agents or list(AGENT_SKILL_DIRS)
    unknown = [agent for agent in selected if agent not in AGENT_SKILL_DIRS]
    if unknown:
        raise ValueError(f"unknown agent target(s): {', '.join(sorted(unknown))}")

    slug = skill_root.name
    installed: list[Path] = []
    for agent in selected:
        destination = agent_skill_root(agent, home) / slug
        if destination.resolve() == skill_root:
            raise ValueError("cannot install a skill onto itself")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(skill_root, destination)
        installed.append(destination)
    return installed
