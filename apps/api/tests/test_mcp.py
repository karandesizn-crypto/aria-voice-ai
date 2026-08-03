from __future__ import annotations

import pytest

from app.infrastructure.mcp.adapter import McpServerConfig, McpToolAdapter


@pytest.mark.asyncio
async def test_mcp_adapter_not_connected() -> None:
    tool = McpToolAdapter(
        server=McpServerConfig(name="notion"),
        tool_name="search",
        description="Search",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    result = await tool.invoke(user_id="user_1", arguments={"query": "roadmap"})
    assert not result.ok
    assert result.data["status"] == "not_connected"
