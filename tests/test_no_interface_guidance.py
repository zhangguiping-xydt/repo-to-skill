from repo_to_skill.cli import _no_interface_guidance


def test_guidance_lists_supported_frameworks() -> None:
    text = _no_interface_guidance(["TypeScript", "Go"])
    assert "No callable HTTP interfaces were detected." in text
    assert "Detected languages: TypeScript, Go" in text
    assert "FastAPI" in text
    assert "Spring" in text
    assert "IHttpHandler" in text


def test_guidance_unsupported_stack_invites_contribution() -> None:
    text = _no_interface_guidance(["TypeScript", "Go"])
    assert "not recognized yet" in text
    assert "contributions are welcome" in text


def test_guidance_supported_language_present_is_diagnostic() -> None:
    text = _no_interface_guidance(["Python"])
    assert "Supported languages are present (Python)" in text
    assert "not recognized yet" not in text


def test_guidance_handles_empty_languages() -> None:
    text = _no_interface_guidance([])
    assert "Detected languages" not in text
    assert "Callable detection currently supports" in text
