from __future__ import annotations

import asyncio
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.logging import get_logger
from app.domain.interfaces.tools import PermissionStore, Tool, ToolResult, ToolSpec
from app.infrastructure.db.models import ToolGrantRow, ToolInvocationRow, UserRow
from app.infrastructure.redis.client import SessionCache

logger = get_logger(__name__)


class PostgresPermissionStore:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = session_factory

    async def has_permissions(self, user_id: str, permissions: list[str]) -> bool:
        if not permissions:
            return True
        async with self._sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == user_id))
            if not user:
                return False
            rows = await session.scalars(
                select(ToolGrantRow).where(
                    ToolGrantRow.user_id == user.id,
                    ToolGrantRow.permission.in_(permissions),
                    ToolGrantRow.granted.is_(True),
                )
            )
            granted = {row.permission for row in rows.all()}
            return all(permission in granted for permission in permissions)

    async def grant(self, user_id: str, permission: str) -> None:
        async with self._sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == user_id))
            if not user:
                user = UserRow(clerk_user_id=user_id)
                session.add(user)
                await session.flush()
            existing = await session.scalar(
                select(ToolGrantRow).where(
                    ToolGrantRow.user_id == user.id,
                    ToolGrantRow.permission == permission,
                )
            )
            if existing:
                existing.granted = True
            else:
                session.add(ToolGrantRow(user_id=user.id, permission=permission, granted=True))
            await session.commit()


class ToolRegistry:
    def __init__(
        self,
        *,
        tools: list[Tool],
        permissions: PermissionStore,
        cache: SessionCache,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        public_permissions: set[str] | None = None,
    ) -> None:
        self._tools = {tool.spec.name: tool for tool in tools}
        self._permissions = permissions
        self._cache = cache
        self._sessions = session_factory
        self._public_permissions = public_permissions or {
            "tools.weather.read",
            "tools.maps.read",
        }

    def list_specs(self) -> list[ToolSpec]:
        return [tool.spec for tool in self._tools.values()]

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    async def invoke(
        self,
        *,
        user_id: str,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(ok=False, error=f"Unknown tool: {tool_name}")

        required = tool.spec.required_permissions
        needs_grant = [p for p in required if p not in self._public_permissions]
        if needs_grant and not await self._permissions.has_permissions(user_id, needs_grant):
            logger.warning("tool_permission_denied", tool=tool_name, user_id=user_id)
            return ToolResult(ok=False, error="Permission denied")

        if not await self._cache.check_rate_limit(user_id, tool_name):
            return ToolResult(ok=False, error="Rate limit exceeded")

        attempts = tool.spec.retry.max_attempts
        backoff = tool.spec.retry.backoff_seconds
        last_error: str | None = None
        started = time.perf_counter()
        retries = 0

        for attempt in range(1, attempts + 1):
            try:
                result = await tool.invoke(user_id=user_id, arguments=arguments)
                latency_ms = (time.perf_counter() - started) * 1000
                await self._audit(
                    user_id=user_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    result=result,
                    latency_ms=latency_ms,
                    retries=retries,
                )
                logger.info(
                    "tool_invoked",
                    tool=tool_name,
                    user_id=user_id,
                    ok=result.ok,
                    latency_ms=round(latency_ms, 2),
                    retries=retries,
                )
                return result
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                retries = attempt
                logger.warning(
                    "tool_retry",
                    tool=tool_name,
                    attempt=attempt,
                    error=last_error,
                )
                if attempt < attempts:
                    await asyncio.sleep(backoff * attempt)

        latency_ms = (time.perf_counter() - started) * 1000
        failure = ToolResult(ok=False, error=last_error or "Tool failed")
        await self._audit(
            user_id=user_id,
            tool_name=tool_name,
            arguments=arguments,
            result=failure,
            latency_ms=latency_ms,
            retries=retries,
        )
        return failure

    async def _audit(
        self,
        *,
        user_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        result: ToolResult,
        latency_ms: float,
        retries: int,
    ) -> None:
        if self._sessions is None:
            return
        async with self._sessions() as session:
            user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == user_id))
            if not user:
                user = UserRow(clerk_user_id=user_id)
                session.add(user)
                await session.flush()
            session.add(
                ToolInvocationRow(
                    user_id=user.id,
                    tool_name=tool_name,
                    arguments_json=arguments,
                    result_json=result.data if result.ok else None,
                    success=result.ok,
                    error=result.error,
                    latency_ms=latency_ms,
                    retries=retries,
                )
            )
            await session.commit()
