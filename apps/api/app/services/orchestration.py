from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentRole(str, Enum):
    GENERAL = "general"
    RESEARCH = "research"
    SCHEDULING = "scheduling"


@dataclass(frozen=True, slots=True)
class RouteDecision:
    agent: AgentRole
    reason: str
    confidence: float


class AgentRouter:
    """Deterministic multi-agent router (Phase 4).

    Keeps orchestration testable without requiring an LLM call on every turn.
    """

    def route(self, utterance: str) -> RouteDecision:
        text = utterance.lower()
        if any(token in text for token in ("remind", "calendar", "schedule", "meeting", "tomorrow")):
            return RouteDecision(
                agent=AgentRole.SCHEDULING,
                reason="utterance references time or calendar intent",
                confidence=0.86,
            )
        if any(token in text for token in ("research", "compare", "analyze", "look up", "find sources")):
            return RouteDecision(
                agent=AgentRole.RESEARCH,
                reason="utterance requests investigation",
                confidence=0.8,
            )
        return RouteDecision(
            agent=AgentRole.GENERAL,
            reason="default conversational path",
            confidence=0.55,
        )


SPECIALIST_INSTRUCTIONS = {
    AgentRole.GENERAL: "You are Aria, a helpful general voice agent.",
    AgentRole.RESEARCH: "You are Aria Research. Prioritize accurate synthesis and cite uncertainty.",
    AgentRole.SCHEDULING: "You are Aria Scheduling. Focus on times, reminders, and calendar actions.",
}
