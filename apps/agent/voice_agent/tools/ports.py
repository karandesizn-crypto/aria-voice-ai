"""Phase 2 stubs — tool ports."""

from __future__ import annotations

from typing import Any, Protocol


class Tool(Protocol):
    name: str
    capabilities: list[str]

    def schema(self) -> dict[str, Any]: ...

    async def invoke(self, user_id: str, arguments: dict[str, Any]) -> dict[str, Any]: ...
