from __future__ import annotations

from app.services.orchestration import AgentRole, AgentRouter


def test_routes_scheduling_intent() -> None:
    decision = AgentRouter().route("Remind me about the meeting tomorrow")
    assert decision.agent == AgentRole.SCHEDULING
    assert decision.confidence > 0.7


def test_routes_research_intent() -> None:
    decision = AgentRouter().route("Can you research and compare these vendors?")
    assert decision.agent == AgentRole.RESEARCH


def test_routes_general_default() -> None:
    decision = AgentRouter().route("How are you today?")
    assert decision.agent == AgentRole.GENERAL
