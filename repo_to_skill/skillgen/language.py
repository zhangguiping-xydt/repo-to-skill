"""Language detection for generated skill output.

The tool stays deterministic: no LLM, no network. Language is resolved from
the user's goal text via a simple CJK-ratio heuristic, or from an explicit
``--language`` override. Source-derived identifiers (slugs, routes, handler
symbols, field names) are never translated — only template prose switches.
"""

from __future__ import annotations

import re

SUPPORTED_LANGUAGES: tuple[str, ...] = ("auto", "en", "zh-CN")
DEFAULT_LANGUAGE = "auto"


_CJK_RE = re.compile(
    "["
    "一-鿿"   # CJK Unified Ideographs
    "㐀-䶿"   # CJK Extension A
    "぀-ヿ"   # Hiragana + Katakana (Japanese)
    "가-힯"   # Hangul (Korean)
    "]"
)


def detect_language(text: str) -> str:
    """Map ``text`` to ``zh-CN`` if CJK characters dominate, else ``en``.

    Threshold is intentionally low (30%): a Chinese sentence that mixes in
    English API names or technical terms still classifies as Chinese, while
    pure-English text (even with stray CJK punctuation or names) stays English.
    """
    if not text:
        return "en"
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return "en"
    cjk_count = sum(1 for c in chars if _CJK_RE.match(c))
    return "zh-CN" if cjk_count / len(chars) >= 0.30 else "en"


def resolve_language(language: str, goal_text: str) -> str:
    """Resolve ``--language`` into a concrete code.

    ``auto`` triggers detection against ``goal_text``; any other value is
    returned as-is after validation.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"unsupported language: {language!r}. "
            f"Supported: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    if language == "auto":
        return detect_language(goal_text)
    return language
