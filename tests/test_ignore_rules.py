from pathlib import Path

from repo_to_skill.scanner.ignore_rules import is_sensitive_file


def test_bare_env_is_sensitive() -> None:
    assert is_sensitive_file(Path("/repo/.env"))


def test_dotted_env_variants_are_sensitive() -> None:
    assert is_sensitive_file(Path("/repo/.env.local"))
    assert is_sensitive_file(Path("/repo/config/.env.production"))
    assert is_sensitive_file(Path("/repo/.env.development"))


def test_pem_and_key_are_sensitive() -> None:
    assert is_sensitive_file(Path("/repo/server.pem"))
    assert is_sensitive_file(Path("/repo/id_rsa.key"))


def test_ordinary_source_is_not_sensitive() -> None:
    assert not is_sensitive_file(Path("/repo/main.py"))
    assert not is_sensitive_file(Path("/repo/environment.py"))
