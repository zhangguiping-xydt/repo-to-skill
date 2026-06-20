from tiny_app.cli import greeting


def test_greeting_defaults_to_world() -> None:
    assert greeting() == "hello, world"


def test_greeting_uses_name() -> None:
    assert greeting("repo") == "hello, repo"
