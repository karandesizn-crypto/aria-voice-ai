from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.services.reminder_service import InProcessJobScheduler, ReminderService


@pytest.mark.asyncio
async def test_reminder_fires_in_process() -> None:
    scheduler = InProcessJobScheduler()
    service = ReminderService(session_factory=None, scheduler=scheduler)
    due = datetime.now(UTC) + timedelta(milliseconds=50)
    reminder = await service.schedule(
        clerk_user_id="user_1",
        title="Standup",
        body="Join the call",
        due_at=due,
    )
    assert reminder.status == "scheduled"
    assert reminder.workflow_id

    # Wait for the in-process task.
    import asyncio

    await asyncio.sleep(0.2)
    assert any(item["reminder_id"] == str(reminder.id) for item in scheduler.fired)
    listed = await service.list_for_user("user_1")
    assert listed[0].status == "fired"
