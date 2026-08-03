from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.interfaces.tools import RetryPolicy, ToolResult, ToolSchema, ToolSpec


@dataclass(frozen=True, slots=True)
class McpServerConfig:
    name: str
    command: str | None = None
    url: str | None = None
    allowed_tools: tuple[str, ...] = ()


class McpToolAdapter:
    """Adapts an MCP-exposed tool into the platform Tool protocol.

    Phase 3 ships a deterministic adapter that can call HTTP MCP gateways when
    configured, and returns a clear not-configured error otherwise. This keeps
    permission/retry/telemetry paths identical to native tools.
    """

    def __init__(
        self,
        *,
        server: McpServerConfig,
        tool_name: str,
        description: str,
        parameters: dict[str, Any],
        http_client: Any | None = None,
    ) -> None:
        self._server = server
        self._http = http_client
        permission = f"tools.mcp.{server.name}"
        self.spec = ToolSpec(
            name=f"mcp.{server.name}.{tool_name}",
            description=description,
            capabilities=[f"mcp.{server.name}", tool_name],
            required_permissions=[permission],
            schema=ToolSchema(
                name=f"mcp.{server.name}.{tool_name}",
                description=description,
                parameters=parameters,
            ),
            retry=RetryPolicy(max_attempts=2, backoff_seconds=0.5),
        )
        self._remote_name = tool_name

    async def invoke(self, *, user_id: str, arguments: dict[str, Any]) -> ToolResult:
        if self._server.url and self._http is not None:
            response = await self._http.post(
                f"{self._server.url.rstrip('/')}/tools/call",
                json={
                    "name": self._remote_name,
                    "arguments": arguments,
                    "user_id": user_id,
                },
            )
            if response.status_code >= 400:
                return ToolResult(ok=False, error=f"MCP call failed: {response.status_code}")
            payload = response.json()
            return ToolResult(ok=True, data=payload if isinstance(payload, dict) else {"result": payload})

        return ToolResult(
            ok=False,
            error=(
                f"MCP server '{self._server.name}' is registered but not connected. "
                "Set MCP URL/command to enable remote tool execution."
            ),
            data={"server": self._server.name, "tool": self._remote_name, "status": "not_connected"},
        )


def build_default_mcp_tools(http_client: Any | None = None) -> list[McpToolAdapter]:
    """Register a sample MCP Notion-like server mapping for integration wiring."""
    server = McpServerConfig(name="notion", url=None, allowed_tools=("search",))
    return [
        McpToolAdapter(
            server=server,
            tool_name="search",
            description="Search Notion via MCP bridge",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            http_client=http_client,
        )
    ]
