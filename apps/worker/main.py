"""Temporal-compatible worker entrypoint for proactive reminders.

Uses the in-process scheduler by default. When TEMPORAL_HOST is set, this module
documents the production wiring point for a Temporal worker process.
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta

from app.services.reminder_service import InProcessJobScheduler, ReminderService


async def demo() -> None:
    scheduler = InProcessJobScheduler()
    service = ReminderService(session_factory=None, scheduler=scheduler)
    await service.schedule(
        clerk_user_id="demo-user",
        title="Phase 3 proactive ping",
        body="Temporal/local scheduler heartbeat",
        due_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    await asyncio.sleep(1.2)
    print({"fired": scheduler.fired, "temporal_host": os.getenv("TEMPORAL_HOST")})


if __name__ == "__main__":
    asyncio.run(demo())
