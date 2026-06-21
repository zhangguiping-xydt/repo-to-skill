from __future__ import annotations

import pytest

from repo_to_skill.skillgen.callable_selector import select_callable_interfaces


def _interface(
    slug: str,
    *,
    route: str,
    handler: str,
    business: str = "",
    request_fields: list[str] | None = None,
    response_fields: list[str] | None = None,
) -> dict:
    return {
        "slug": slug,
        "stack": "java",
        "framework": "spring",
        "http_method": "POST",
        "route": route,
        "handler_symbol": handler,
        "handler_path": "src/main/java/example/Controller.java",
        "business_method": business,
        "endpoint_env": slug.replace("-", "_").upper() + "_ENDPOINT",
        "token_env": slug.replace("-", "_").upper() + "_TOKEN",
        "side_effects": "unknown",
        "request": {
            "model_name": handler.rsplit(".", 1)[-1] + "Request",
            "fields": [
                {"name": field, "type": "string", "required": False}
                for field in (request_fields or [])
            ],
        },
        "response": {
            "model_name": handler.rsplit(".", 1)[-1] + "Response",
            "fields": [
                {"name": field, "type": "string", "required": False}
                for field in (response_fields or [])
            ],
        },
    }


def test_select_callable_interfaces_ranks_need_matches_with_reasons() -> None:
    interfaces = [
        _interface(
            "calculate-work-load",
            route="/api/work/calculate",
            handler="WorkController.calculateWorkload",
            business="KQWorkDateBL.CalculateTimeLength",
            request_fields=["employeeInfo", "applyStartDateTime", "applyEndDateTime"],
            response_fields=["timeLengthUnitDay", "timeLengthUnitHour"],
        ),
        _interface(
            "query-dictionary",
            route="/api/dictionary/list",
            handler="DictionaryController.list",
            request_fields=["dicId", "langId"],
            response_fields=["items"],
        ),
    ]

    selection = select_callable_interfaces(
        interfaces,
        "calculate employee workload time length",
        max_interfaces=1,
    )

    assert selection.need_summary == "calculate employee workload time length"
    assert selection.selection_source == "deterministic"
    assert [item.interface["slug"] for item in selection.items] == ["calculate-work-load"]
    assert selection.items[0].score > 0
    assert any("slug" in reason or "handler" in reason or "field" in reason for reason in selection.items[0].reasons)


def test_select_callable_interfaces_honors_agent_slug_order() -> None:
    interfaces = [
        _interface("a-first", route="/a", handler="A.first"),
        _interface("b-second", route="/b", handler="B.second"),
        _interface("c-third", route="/c", handler="C.third"),
    ]

    selection = select_callable_interfaces(
        interfaces,
        "agent selected order",
        selected_slugs=["c-third", "a-first", "c-third"],
        max_interfaces=5,
        selection_source="agentic",
    )

    assert selection.selection_source == "agentic"
    assert [item.interface["slug"] for item in selection.items] == ["c-third", "a-first"]
    assert selection.items[0].score == pytest.approx(1.0)
    assert "selected by agent slug" in selection.items[0].reasons


def test_select_callable_interfaces_rejects_unknown_slug() -> None:
    with pytest.raises(ValueError, match="unknown callable interface slug: missing"):
        select_callable_interfaces(
            [_interface("known", route="/known", handler="Known.call")],
            "need",
            selected_slugs=["missing"],
        )


def test_select_callable_interfaces_caps_results() -> None:
    interfaces = [
        _interface("employee-entry", route="/employee/entry", handler="Employee.entry"),
        _interface("employee-transfer", route="/employee/transfer", handler="Employee.transfer"),
        _interface("employee-status", route="/employee/status", handler="Employee.status"),
    ]

    selection = select_callable_interfaces(interfaces, "employee", max_interfaces=2)

    assert len(selection.items) == 2
    assert all(item.score > 0 for item in selection.items)


def test_select_callable_interfaces_ignores_common_stopwords() -> None:
    interfaces = [
        _interface("job-transfer", route="/job/transfer", handler="Job.transfer"),
        _interface("post-type-and-seq", route="/post/type/and/seq", handler="PostTypeAndSeq.get"),
    ]

    selection = select_callable_interfaces(interfaces, "job and transfer", max_interfaces=2)

    assert [item.interface["slug"] for item in selection.items] == ["job-transfer"]
    assert all("matched: and" not in reason for item in selection.items for reason in item.reasons)


def test_select_callable_interfaces_requires_need_without_agent_slugs() -> None:
    with pytest.raises(ValueError, match="need must be provided"):
        select_callable_interfaces(
            [_interface("known", route="/known", handler="Known.call")],
            "",
        )
