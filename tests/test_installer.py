from pathlib import Path

import pytest

from repo_to_skill.skillgen.installer import AGENT_SKILL_DIRS, install_skill


def _make_skill(root: Path) -> Path:
    skill = root / "my-bundle"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: my-bundle\n---\n", encoding="utf-8")
    (skill / "scripts" / "call_x.py").write_text("print('hi')\n", encoding="utf-8")
    return skill


def test_install_skill_copies_into_all_agent_dirs(tmp_path) -> None:
    skill = _make_skill(tmp_path / "out")
    home = tmp_path / "home"

    installed = install_skill(skill, home=home)

    assert len(installed) == len(AGENT_SKILL_DIRS)
    for dest in installed:
        assert (dest / "SKILL.md").is_file()
        assert (dest / "scripts" / "call_x.py").is_file()
    assert (home / ".claude" / "skills" / "my-bundle" / "SKILL.md").is_file()
    assert (home / ".agents" / "skills" / "my-bundle" / "SKILL.md").is_file()


def test_install_skill_replaces_existing(tmp_path) -> None:
    skill = _make_skill(tmp_path / "out")
    home = tmp_path / "home"
    install_skill(skill, home=home)
    stale = home / ".claude" / "skills" / "my-bundle" / "stale.txt"
    stale.write_text("old", encoding="utf-8")

    install_skill(skill, home=home)

    assert not stale.exists()


def test_install_skill_selected_agent_only(tmp_path) -> None:
    skill = _make_skill(tmp_path / "out")
    home = tmp_path / "home"

    installed = install_skill(skill, agents=["claude-code"], home=home)

    assert len(installed) == 1
    assert (home / ".claude" / "skills" / "my-bundle").is_dir()
    assert not (home / ".agents" / "skills").exists()


def test_install_skill_rejects_missing_dir(tmp_path) -> None:
    with pytest.raises(ValueError):
        install_skill(tmp_path / "nope", home=tmp_path / "home")
