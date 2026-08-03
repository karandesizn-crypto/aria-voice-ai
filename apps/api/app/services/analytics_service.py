from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.db.models import ConversationRow, MemoryRow, ToolInvocationRow, UserRow


@dataclass(frozen=True, slots=True)
class AnalyticsSnapshot:
    conversations: int
    memories: int
    tool_invocations: int
    tool_success_rate: float
    top_tools: list[dict[str, Any]]
    generated_at: str


class AnalyticsService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] | None = None) -> None:
        self._sessions = session_factory
        self._events: list[dict[str, Any]] = []

    def track(self, event: str, **properties: Any) -> None:
        self._events.append(
            {"event": event, "properties": properties, "at": datetime.now(UTC).isoformat()}
        )

    async def snapshot(self, *, clerk_user_id: str | None = None, days: int = 7) -> AnalyticsSnapshot:
        if self._sessions is None:
            return AnalyticsSnapshot(
                conversations=sum(1 for e in self._events if e["event"] == "conversation_started"),
                memories=sum(1 for e in self._events if e["event"] == "memory_written"),
                tool_invocations=sum(1 for e in self._events if e["event"] == "tool_invoked"),
                tool_success_rate=1.0,
                top_tools=[],
                generated_at=datetime.now(UTC).isoformat(),
            )

        since = datetime.now(UTC) - timedelta(days=days)
        async with self._sessions() as session:
            user_filter = None
            if clerk_user_id:
                user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == clerk_user_id))
                if not user:
                    return AnalyticsSnapshot(
                        conversations=0,
                        memories=0,
                        tool_invocations=0,
                        tool_success_rate=0.0,
                        top_tools=[],
                        generated_at=datetime.now(UTC).isoformat(),
                    )
                user_filter = user.id

            conv_stmt = select(func.count()).select_from(ConversationRow).where(
                ConversationRow.started_at >= since
            )
            mem_stmt = select(func.count()).select_from(MemoryRow).where(MemoryRow.created_at >= since)
            tool_stmt = select(func.count()).select_from(ToolInvocationRow).where(
                ToolInvocationRow.created_at >= since
            )
            success_stmt = select(func.count()).select_from(ToolInvocationRow).where(
                ToolInvocationRow.created_at >= since,
                ToolInvocationRow.success.is_(True),
            )
            if user_filter:
                conv_stmt = conv_stmt.where(ConversationRow.user_id == user_filter)
                mem_stmt = mem_stmt.where(MemoryRow.user_id == user_filter)
                tool_stmt = tool_stmt.where(ToolInvocationRow.user_id == user_filter)
                success_stmt = success_stmt.where(ToolInvocationRow.user_id == user_filter)

            conversations = int(await session.scalar(conv_stmt) or 0)
            memories = int(await session.scalar(mem_stmt) or 0)
            tools = int(await session.scalar(tool_stmt) or 0)
            successes = int(await session.scalar(success_stmt) or 0)
            rate = (successes / tools) if tools else 0.0

            top_q = (
                select(ToolInvocationRow.tool_name, func.count().label("count"))
                .where(ToolInvocationRow.created_at >= since)
                .group_by(ToolInvocationRow.tool_name)
                .order_by(func.count().desc())
                .limit(5)
            )
            if user_filter:
                top_q = top_q.where(ToolInvocationRow.user_id == user_filter)
            top_rows = (await session.execute(top_q)).all()

            return AnalyticsSnapshot(
                conversations=conversations,
                memories=memories,
                tool_invocations=tools,
                tool_success_rate=round(rate, 3),
                top_tools=[{"tool": name, "count": count} for name, count in top_rows],
                generated_at=datetime.now(UTC).isoformat(),
            )
