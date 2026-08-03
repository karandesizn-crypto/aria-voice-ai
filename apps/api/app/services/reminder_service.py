from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.infrastructure.db.models import ReminderRow, UserRow

logger = get_logger(__name__)

FireCallback = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class Reminder:
    id: UUID
    user_id: str
    title: str
    body: str
    due_at: datetime
    status: str
    workflow_id: str | None = None


class InProcessJobScheduler:
    """Lightweight durable-enough scheduler for local/dev and tests.

    Production deployments should set TEMPORAL_HOST and run apps/worker.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self._fired: list[dict[str, Any]] = []

    async def schedule_reminder(
        self,
        *,
        reminder_id: str,
        user_id: str,
        title: str,
        body: str,
        due_at: datetime,
        on_fire: FireCallback | None = None,
    ) -> str:
        workflow_id = f"reminder-{reminder_id}"
        delay = max((due_at - datetime.now(UTC)).total_seconds(), 0)

        async def _run() -> None:
            await asyncio.sleep(delay)
            payload = {
                "reminder_id": reminder_id,
                "user_id": user_id,
                "title": title,
                "body": body,
                "fired_at": datetime.now(UTC).isoformat(),
            }
            self._fired.append(payload)
            logger.info("reminder_fired", **payload)
            if on_fire:
                await on_fire(payload)

        self._tasks[workflow_id] = asyncio.create_task(_run())
        return workflow_id

    @property
    def fired(self) -> list[dict[str, Any]]:
        return list(self._fired)


class ReminderService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None,
        scheduler: InProcessJobScheduler,
    ) -> None:
        self._sessions = session_factory
        self._scheduler = scheduler
        self._memory: dict[UUID, Reminder] = {}

    async def schedule(
        self,
        *,
        clerk_user_id: str,
        title: str,
        body: str,
        due_at: datetime,
    ) -> Reminder:
        reminder_id = uuid4()
        workflow_id = await self._scheduler.schedule_reminder(
            reminder_id=str(reminder_id),
            user_id=clerk_user_id,
            title=title,
            body=body,
            due_at=due_at,
            on_fire=self._mark_fired,
        )

        reminder = Reminder(
            id=reminder_id,
            user_id=clerk_user_id,
            title=title,
            body=body,
            due_at=due_at,
            status="scheduled",
            workflow_id=workflow_id,
        )

        if self._sessions is None:
            self._memory[reminder_id] = reminder
            return reminder

        async with self._sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == clerk_user_id))
            if not user:
                user = UserRow(clerk_user_id=clerk_user_id)
                session.add(user)
                await session.flush()
            session.add(
                ReminderRow(
                    id=reminder_id,
                    user_id=user.id,
                    title=title,
                    body=body,
                    due_at=due_at,
                    status="scheduled",
                    workflow_id=workflow_id,
                )
            )
            await session.commit()
        return reminder

    async def _mark_fired(self, payload: dict[str, Any]) -> None:
        reminder_id = UUID(payload["reminder_id"])
        if self._sessions is None:
            existing = self._memory.get(reminder_id)
            if existing:
                self._memory[reminder_id] = Reminder(
                    id=existing.id,
                    user_id=existing.user_id,
                    title=existing.title,
                    body=existing.body,
                    due_at=existing.due_at,
                    status="fired",
                    workflow_id=existing.workflow_id,
                )
            return

        async with self._sessions() as session:
            row = await session.get(ReminderRow, reminder_id)
            if row:
                row.status = "fired"
                row.fired_at = datetime.now(UTC)
                await session.commit()

    async def list_for_user(self, clerk_user_id: str) -> list[Reminder]:
        if self._sessions is None:
            return [r for r in self._memory.values() if r.user_id == clerk_user_id]

        async with self._sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == clerk_user_id))
            if not user:
                return []
            rows = (
                await session.scalars(
                    select(ReminderRow)
                    .where(ReminderRow.user_id == user.id)
                    .order_by(ReminderRow.due_at.asc())
                )
            ).all()
            return [
                Reminder(
                    id=r.id,
                    user_id=clerk_user_id,
                    title=r.title,
                    body=r.body,
                    due_at=r.due_at,
                    status=r.status,
                    workflow_id=r.workflow_id,
                )
                for r in rows
            ]
