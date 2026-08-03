from __future__ import annotations

import pytest

from app.infrastructure.tools.registry import ToolRegistry
from app.infrastructure.tools.weather import WeatherTool


class FakeCache:
    async def check_rate_limit(self, user_id: str, tool_name: str, **kwargs) -> bool:
        return True


class AllowAllPermissions:
    async def has_permissions(self, user_id: str, permissions: list[str]) -> bool:
        return True


class DenyPermissions:
    async def has_permissions(self, user_id: str, permissions: list[str]) -> bool:
        return False


@pytest.mark.asyncio
async def test_weather_tool_mock_mode() -> None:
    import httpx

    tool = WeatherTool(httpx.AsyncClient(), api_key=None)
    result = await tool.invoke(user_id="user_1", arguments={"location": "Austin"})
    assert result.ok
    assert result.data["source"] == "mock"


@pytest.mark.asyncio
async def test_registry_allows_public_weather() -> None:
    import httpx

    registry = ToolRegistry(
        tools=[WeatherTool(httpx.AsyncClient(), api_key=None)],
        permissions=DenyPermissions(),
        cache=FakeCache(),  # type: ignore[arg-type]
        session_factory=None,
    )
    result = await registry.invoke(
        user_id="user_1",
        tool_name="weather",
        arguments={"location": "Paris"},
    )
    assert result.ok


@pytest.mark.asyncio
async def test_registry_unknown_tool() -> None:
    registry = ToolRegistry(
        tools=[],
        permissions=AllowAllPermissions(),
        cache=FakeCache(),  # type: ignore[arg-type]
        session_factory=None,
    )
    result = await registry.invoke(user_id="user_1", tool_name="nope", arguments={})
    assert not result.ok
    assert "Unknown tool" in (result.error or "")
