from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CallableSelectionItem:
    interface: dict[str, Any]
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CallableBundleSelection:
    need_summary: str
    selection_source: str
    items: list[CallableSelectionItem]


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}
_FIELD_WEIGHTS = {
    "slug": 4.0,
    "handler_symbol": 3.5,
    "route": 3.0,
    "business_method": 3.0,
    "request_model": 2.0,
    "response_model": 2.0,
    "request_fields": 2.5,
    "response_fields": 2.0,
    "framework": 1.0,
    "stack": 1.0,
    "side_effects": 0.5,
}


def _split_identifier(value: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    return re.sub(r"[_\-/.:]+", " ", spaced)


def _tokens(value: str) -> list[str]:
    return [
        token.lower()
        for token in _TOKEN_RE.findall(_split_identifier(value))
        if token.lower() not in _STOPWORDS
    ]


def _field_tokens(interface: dict[str, Any]) -> dict[str, list[str]]:
    request = interface.get("request") if isinstance(interface.get("request"), dict) else {}
    response = interface.get("response") if isinstance(interface.get("response"), dict) else {}
    fields: dict[str, list[str]] = {
        "slug": _tokens(str(interface.get("slug") or "")),
        "handler_symbol": _tokens(str(interface.get("handler_symbol") or "")),
        "route": _tokens(str(interface.get("route") or "")),
        "business_method": _tokens(str(interface.get("business_method") or "")),
        "request_model": _tokens(str(request.get("model_name") or "")),
        "response_model": _tokens(str(response.get("model_name") or "")),
        "framework": _tokens(str(interface.get("framework") or "")),
        "stack": _tokens(str(interface.get("stack") or "")),
        "side_effects": _tokens(str(interface.get("side_effects") or "")),
    }
    fields["request_fields"] = _contract_field_tokens(request)
    fields["response_fields"] = _contract_field_tokens(response)
    return fields


def _contract_field_tokens(contract: dict[str, Any]) -> list[str]:
    tokens: list[str] = []
    for item in contract.get("fields") or []:
        if not isinstance(item, dict):
            continue
        tokens.extend(_tokens(str(item.get("name") or "")))
        tokens.extend(_tokens(str(item.get("type") or "")))
    return tokens


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _slug(interface: dict[str, Any]) -> str:
    return str(interface.get("slug") or "").strip()


def _idf(field_tokens: list[dict[str, list[str]]]) -> dict[str, float]:
    document_count = len(field_tokens)
    frequencies: dict[str, int] = {}
    for fields in field_tokens:
        unique = set(token for values in fields.values() for token in values)
        for token in unique:
            frequencies[token] = frequencies.get(token, 0) + 1
    return {
        token: math.log((1 + document_count) / (1 + count)) + 1.0
        for token, count in frequencies.items()
    }


def _score_interface(
    interface: dict[str, Any],
    fields: dict[str, list[str]],
    query_tokens: list[str],
    idf: dict[str, float],
) -> CallableSelectionItem:
    score = 0.0
    reasons: list[str] = []
    for field_name, values in fields.items():
        if not values:
            continue
        value_counts = {token: values.count(token) for token in set(values)}
        matches = [token for token in query_tokens if token in value_counts]
        if not matches:
            continue
        field_score = 0.0
        for token in matches:
            term_frequency = value_counts[token] / len(values)
            field_score += (1.0 + term_frequency) * idf.get(token, 1.0)
        weighted = field_score * _FIELD_WEIGHTS[field_name]
        score += weighted
        reasons.append(f"{field_name} matched: {', '.join(_dedupe(matches))}")
    return CallableSelectionItem(interface=interface, score=round(score, 6), reasons=reasons)


def select_callable_interfaces(
    interfaces: list[dict[str, Any]],
    need: str,
    *,
    selected_slugs: list[str] | None = None,
    max_interfaces: int = 12,
    selection_source: str = "deterministic",
) -> CallableBundleSelection:
    if max_interfaces < 1:
        raise ValueError("max_interfaces must be at least 1")

    need_summary = " ".join(str(need or "").split())
    by_slug = {_slug(interface): interface for interface in interfaces if _slug(interface)}

    if selected_slugs:
        items: list[CallableSelectionItem] = []
        for slug in _dedupe([str(value).strip() for value in selected_slugs if str(value).strip()]):
            interface = by_slug.get(slug)
            if interface is None:
                raise ValueError(f"unknown callable interface slug: {slug}")
            items.append(
                CallableSelectionItem(
                    interface=interface,
                    score=1.0,
                    reasons=["selected by agent slug"],
                )
            )
        return CallableBundleSelection(
            need_summary=need_summary or "Selected callable interfaces.",
            selection_source=selection_source,
            items=items[:max_interfaces],
        )

    if not need_summary:
        raise ValueError("need must be provided when selected_slugs is empty")

    query_tokens = _dedupe(_tokens(need_summary))
    if not query_tokens:
        raise ValueError("need must include searchable words")

    fields_by_interface = [_field_tokens(interface) for interface in interfaces]
    idf = _idf(fields_by_interface)
    scored = [
        _score_interface(interface, fields, query_tokens, idf)
        for interface, fields in zip(interfaces, fields_by_interface, strict=True)
    ]
    ranked = [item for item in scored if item.score > 0]
    ranked.sort(
        key=lambda item: (
            -item.score,
            str(item.interface.get("slug") or ""),
        )
    )
    return CallableBundleSelection(
        need_summary=need_summary,
        selection_source=selection_source,
        items=ranked[:max_interfaces],
    )
