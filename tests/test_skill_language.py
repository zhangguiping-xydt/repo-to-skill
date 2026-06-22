from __future__ import annotations

from pathlib import Path

import pytest

from repo_to_skill.skillgen.language import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    detect_language,
    resolve_language,
)


def test_detect_pure_chinese_is_zh() -> None:
    assert detect_language("根据加班时长查询调休天数") == "zh-CN"


def test_detect_mixed_chinese_with_english_terms_is_still_zh() -> None:
    assert detect_language("根据 overtime hours 查询调休天数") == "zh-CN"


def test_detect_pure_english_is_en() -> None:
    assert detect_language("Generate a callable skill for employee onboarding.") == "en"


def test_detect_empty_defaults_to_en() -> None:
    assert detect_language("") == "en"
    assert detect_language("   \n  ") == "en"


def test_resolve_auto_uses_detection() -> None:
    assert resolve_language("auto", "查询调休") == "zh-CN"
    assert resolve_language("auto", "list employees") == "en"


def test_resolve_explicit_override_skips_detection() -> None:
    assert resolve_language("zh-CN", "list employees") == "zh-CN"
    assert resolve_language("en", "根据加班查询") == "en"


def test_resolve_rejects_unknown_language() -> None:
    with pytest.raises(ValueError, match="unsupported language"):
        resolve_language("fr", "")


def test_resolve_rejects_none_like_value() -> None:
    with pytest.raises(ValueError):
        resolve_language("auto-detect", "")


def test_default_language_is_auto() -> None:
    assert DEFAULT_LANGUAGE == "auto"
    assert "auto" in SUPPORTED_LANGUAGES
    assert "zh-CN" in SUPPORTED_LANGUAGES
    assert "en" in SUPPORTED_LANGUAGES


def test_plan_skill_carries_resolved_language(tmp_path: Path) -> None:
    from repo_to_skill.skillgen.planner import plan_skill

    target = tmp_path / "repo"
    target.mkdir()
    analysis_root = tmp_path / "analysis"
    analysis_root.mkdir()
    _write_minimal_analysis(analysis_root, target)

    plan_auto = plan_skill(target, analysis_root, language="auto")
    assert plan_auto.language == "en"  # no goal text → en

    plan_zh = plan_skill(target, analysis_root, language="zh-CN")
    assert plan_zh.language == "zh-CN"

    plan_en = plan_skill(target, analysis_root, language="en")
    assert plan_en.language == "en"


def test_plan_callable_bundle_auto_detects_from_need(tmp_path: Path) -> None:
    from repo_to_skill.skillgen.planner import plan_callable_bundle

    target = tmp_path / "repo"
    target.mkdir()
    analysis_root = tmp_path / "analysis"
    analysis_root.mkdir()
    _write_minimal_callable_analysis(analysis_root, target)

    plan_zh = plan_callable_bundle(
        target,
        analysis_root,
        need="根据加班时长查询调休天数",
        selected_slugs=["calculate-work-load"],
        selection_json=None,
        max_interfaces=5,
    )
    assert plan_zh.language == "zh-CN"

    plan_en = plan_callable_bundle(
        target,
        analysis_root,
        need="calculate overtime compensatory leave",
        selected_slugs=["calculate-work-load"],
        selection_json=None,
        max_interfaces=5,
    )
    assert plan_en.language == "en"


def _write_minimal_analysis(analysis_root: Path, target: Path) -> None:
    (analysis_root / "scan.json").write_text("{}", encoding="utf-8")
    (analysis_root / "profile.json").write_text(
        '{"name": "demo", "description": "demo project"}', encoding="utf-8"
    )
    (analysis_root / "capability_evidence.json").write_text("{}", encoding="utf-8")
    (analysis_root / "capability_graph.json").write_text('{"nodes": [], "edges": []}', encoding="utf-8")
    (analysis_root / "skill_spec.yaml").write_text(
        "name: demo\ndescription: demo project\n", encoding="utf-8"
    )
    (analysis_root / "verification_report.json").write_text(
        '{"status": "PASS", "findings": []}', encoding="utf-8"
    )
    (analysis_root / "confidence-report.md").write_text("# Confidence\n\nok", encoding="utf-8")


def _write_minimal_callable_analysis(analysis_root: Path, target: Path) -> None:
    _write_minimal_analysis(analysis_root, target)
    (analysis_root / "callable_capabilities.json").write_text(
        '{"project": "demo", "interfaces": ['
        '{"slug": "calculate-work-load", "http_method": "POST", "route": "/calc", '
        '"handler_symbol": "CalculateWorkLoad", "handler_path": "", '
        '"business_method": "", "framework": "aspnet", "stack": "aspnet", '
        '"request": {"fields": [{"name": "EmployeeInfo", "type": "string", "required": true}]}, '
        '"response": {"fields": [{"name": "TimeLenthUintHour", "type": "number"}]}}'
        "], \"notes\": []}",
        encoding="utf-8",
    )


def test_render_skill_in_zh_CN_produces_chinese_section(tmp_path: Path) -> None:
    from repo_to_skill.skillgen.planner import plan_skill
    from repo_to_skill.skillgen.renderer import render_skill

    target = tmp_path / "repo"
    target.mkdir()
    analysis_root = tmp_path / "analysis"
    analysis_root.mkdir()
    _write_minimal_analysis(analysis_root, target)

    plan = plan_skill(target, analysis_root, language="zh-CN")
    skill_root = render_skill(plan, tmp_path / "skill")

    skill_md = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "仓库 skill" in skill_md
    assert "概览" in skill_md
    assert "安全边界" in skill_md


def test_render_skill_in_en_keeps_english_sections(tmp_path: Path) -> None:
    from repo_to_skill.skillgen.planner import plan_skill
    from repo_to_skill.skillgen.renderer import render_skill

    target = tmp_path / "repo"
    target.mkdir()
    analysis_root = tmp_path / "analysis"
    analysis_root.mkdir()
    _write_minimal_analysis(analysis_root, target)

    plan = plan_skill(target, analysis_root, language="en")
    skill_root = render_skill(plan, tmp_path / "skill")

    skill_md = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    assert "repository skill" in skill_md
    assert "Safety boundaries" in skill_md
    assert "仓库 skill" not in skill_md


def test_render_callable_bundle_in_zh_CN_produces_chinese(tmp_path: Path) -> None:
    from repo_to_skill.skillgen.planner import plan_callable_bundle
    from repo_to_skill.skillgen.renderer import render_callable_bundle

    target = tmp_path / "repo"
    target.mkdir()
    analysis_root = tmp_path / "analysis"
    analysis_root.mkdir()
    _write_minimal_callable_analysis(analysis_root, target)

    plan = plan_callable_bundle(
        target,
        analysis_root,
        need="根据加班时长查询调休天数",
        selected_slugs=["calculate-work-load"],
        selection_json=None,
        max_interfaces=5,
        language="zh-CN",
    )
    assert plan.language == "zh-CN"
    bundle = render_callable_bundle(plan, tmp_path / "skill")
    skill_md = (bundle / "SKILL.md").read_text(encoding="utf-8")
    assert "callable API bundle" in skill_md or "何时使用" in skill_md
    assert "---\n\n# demo" in skill_md
    assert "需要通过 demo 系统" in skill_md
    assert "\\u9700\\u8981" not in skill_md
    assert "using the demo system" not in skill_md
    assert "何时使用" in skill_md
    assert "## 安全" in skill_md

    selection_md = (bundle / "references" / "capability-selection.md").read_text(encoding="utf-8")
    assert "能力选择" in selection_md
    assert "审阅本选择" in selection_md
