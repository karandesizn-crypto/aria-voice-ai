from __future__ import annotations

from voice_agent.assistant import _format_bundle


def test_format_bundle_includes_preferences() -> None:
    text = _format_bundle(
        {
            "preferences": [{"content": "Prefers brief answers"}],
            "semantic": [{"content": "Name is Sam"}],
            "episodic": [],
        }
    )
    assert "Prefers brief answers" in text
    assert "Name is Sam" in text
