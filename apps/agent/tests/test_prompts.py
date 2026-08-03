from __future__ import annotations

from voice_agent.prompts import AGENT_INSTRUCTIONS


def test_agent_instructions_are_voice_safe() -> None:
    assert "markdown" in AGENT_INSTRUCTIONS.lower() or "Never use markdown" in AGENT_INSTRUCTIONS
    assert "Aria" in AGENT_INSTRUCTIONS
