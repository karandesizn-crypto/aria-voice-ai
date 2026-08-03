from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RouteDecision:
    agent: str
    reason: str
    confidence: float


class AgentRouter:
    def route(self, utterance: str) -> RouteDecision:
        text = utterance.lower()
        if any(token in text for token in ("remind", "calendar", "schedule", "meeting", "tomorrow")):
            return RouteDecision("scheduling", "time/calendar intent", 0.86)
        if any(token in text for token in ("research", "compare", "analyze", "look up")):
            return RouteDecision("research", "investigation intent", 0.8)
        return RouteDecision("general", "default", 0.55)


SPECIALIST_INSTRUCTIONS = {
    "general": "You are Aria, a helpful general voice agent.",
    "research": "You are Aria Research. Prioritize accurate synthesis and cite uncertainty.",
    "scheduling": "You are Aria Scheduling. Focus on times, reminders, and calendar actions.",
}
