from __future__ import annotations

import pytest

from app.services.analytics_service import AnalyticsService


@pytest.mark.asyncio
async def test_analytics_in_memory_snapshot() -> None:
    analytics = AnalyticsService(session_factory=None)
    analytics.track("conversation_started", user_id="u1")
    analytics.track("memory_written", user_id="u1")
    analytics.track("tool_invoked", tool="weather")
    snap = await analytics.snapshot(clerk_user_id="u1")
    assert snap.conversations == 1
    assert snap.memories == 1
    assert snap.tool_invocations == 1
