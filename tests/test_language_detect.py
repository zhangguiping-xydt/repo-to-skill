from pathlib import Path

from repo_to_skill.scanner.language_detect import detect_project_signals, detect_file_language


def test_detect_python_project_signals_from_pyproject() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "tiny-python-app"

    signals = detect_project_signals(root)

    assert signals["languages"] == ["Python"]
    assert signals["ecosystems"] == ["python"]
    assert signals["package_managers"] == ["python-build"]
    assert "python -m pytest" in signals["candidate_commands"]
    assert signals["entrypoints"] == ["tiny-app = tiny_app.cli:main"]


def test_detect_file_language_by_extension_and_role() -> None:
    language, role = detect_file_language(Path("src/tiny_app/cli.py"))

    assert language == "Python"
    assert role == "source"

    language, role = detect_file_language(Path("tests/test_cli.py"))

    assert language == "Python"
    assert role == "test"


def test_detect_enterprise_legacy_file_languages_and_roles() -> None:
    cases = {
        "src/App.cs": ("C#", "source"),
        "Web/Default.aspx": ("ASP.NET", "source"),
        "Web/Service.asmx": ("ASP.NET", "source"),
        "DB/schema.sql": ("SQL", "source"),
        "App.config": ("XML", "configuration"),
        "Properties/Resources.resx": ("XML", "configuration"),
        "Release_TMS.bat": ("Batch", "source"),
        "Attendance/Main.pas": ("Delphi/Pascal", "source"),
        "Attendance/Main.dfm": ("Delphi/Pascal", "source"),
        "TMS_CN001_CommonFramework.csproj": (".NET project", "configuration"),
        "TMS.sln": (".NET project", "configuration"),
    }

    for path, expected in cases.items():
        assert detect_file_language(Path(path)) == expected


def test_detect_dotnet_project_signals(tmp_path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "TMS.sln").write_text("Microsoft Visual Studio Solution File\n", encoding="utf-8")
    (root / "Web").mkdir()
    (root / "Web" / "Web.csproj").write_text("<Project />\n", encoding="utf-8")

    signals = detect_project_signals(root)

    assert "C#" in signals["languages"]
    assert "dotnet" in signals["ecosystems"]
    assert "msbuild" in signals["package_managers"]
    assert "msbuild TMS.sln" in signals["candidate_commands"]
