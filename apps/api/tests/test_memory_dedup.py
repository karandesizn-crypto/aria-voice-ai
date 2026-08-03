from __future__ import annotations

from app.infrastructure.memory.dedup import content_hash, normalize_memory_text


def test_normalize_collapses_whitespace_and_case() -> None:
    assert normalize_memory_text("  Hello   World  ") == "hello world"


def test_content_hash_stable_for_equivalent_text() -> None:
    assert content_hash("Hello World") == content_hash("  hello   world ")
