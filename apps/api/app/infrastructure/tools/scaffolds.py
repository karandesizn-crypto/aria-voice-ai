from __future__ import annotations

from typing import Any

from app.domain.interfaces.tools import RetryPolicy, ToolResult, ToolSchema, ToolSpec


def _scaffold(
    *,
    name: str,
    description: str,
    capabilities: list[str],
    permission: str,
    parameters: dict[str, Any],
) -> ToolSpec:
    return ToolSpec(
        name=name,
        description=description,
        capabilities=capabilities,
        required_permissions=[permission],
        schema=ToolSchema(name=name, description=description, parameters=parameters),
        retry=RetryPolicy(max_attempts=2, backoff_seconds=0.5),
    )


class ScaffoldTool:
    """OAuth-backed integrations stubbed until credentials are connected."""

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    async def invoke(self, *, user_id: str, arguments: dict[str, Any]) -> ToolResult:
        return ToolResult(
            ok=False,
            error=(
                f"{self.spec.name} is scaffolded in Phase 2. "
                "Connect OAuth credentials / MCP in Phase 3 to enable it."
            ),
            data={"arguments": arguments, "status": "not_configured"},
        )


SCAFFOLD_TOOLS = [
    ScaffoldTool(
        _scaffold(
            name="calendar",
            description="Read or create calendar events.",
            capabilities=["calendar.read", "calendar.write"],
            permission="tools.calendar.access",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["list", "create"]},
                    "query": {"type": "string"},
                },
                "required": ["action"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="email",
            description="Search or draft email.",
            capabilities=["email.read", "email.draft"],
            permission="tools.email.access",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "draft"]},
                    "query": {"type": "string"},
                },
                "required": ["action"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="github",
            description="Read GitHub issues, PRs, or repository metadata.",
            capabilities=["github.read"],
            permission="tools.github.access",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "repo": {"type": "string"},
                },
                "required": ["action"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="figma",
            description="Fetch Figma file metadata.",
            capabilities=["figma.read"],
            permission="tools.figma.access",
            parameters={
                "type": "object",
                "properties": {"file_key": {"type": "string"}},
                "required": ["file_key"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="notion",
            description="Search Notion pages.",
            capabilities=["notion.read"],
            permission="tools.notion.access",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="google_drive",
            description="Search Google Drive files.",
            capabilities=["drive.read"],
            permission="tools.drive.access",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="slack",
            description="Search Slack messages or post a message.",
            capabilities=["slack.read", "slack.write"],
            permission="tools.slack.access",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["search", "post"]},
                    "query": {"type": "string"},
                },
                "required": ["action"],
            },
        )
    ),
    ScaffoldTool(
        _scaffold(
            name="home_assistant",
            description="Control Home Assistant entities.",
            capabilities=["home.read", "home.control"],
            permission="tools.home.access",
            parameters={
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["entity_id", "action"],
            },
        )
    ),
]
