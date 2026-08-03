from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: float = 0.4


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    capabilities: list[str]
    required_permissions: list[str]
    schema: ToolSchema
    retry: RetryPolicy = field(default_factory=RetryPolicy)


@dataclass(frozen=True, slots=True)
class ToolResult:
    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class Tool(Protocol):
    spec: ToolSpec

    async def invoke(self, *, user_id: str, arguments: dict[str, Any]) -> ToolResult: ...


class PermissionStore(Protocol):
    async def has_permissions(self, user_id: str, permissions: list[str]) -> bool: ...
