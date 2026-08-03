from __future__ import annotations

from voice_agent.orchestration import AgentRouter


def test_agent_router_scheduling() -> None:
    assert AgentRouter().route("schedule a meeting tomorrow").agent == "scheduling"
