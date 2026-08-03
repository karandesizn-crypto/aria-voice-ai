from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.interfaces.memory import MemoryKind


class MemoryWriteBody(BaseModel):
    kind: MemoryKind
    content: str = Field(min_length=1, max_length=4000)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = Field(
        default=None,
        description="Required when calling with agent service token.",
    )


class MemorySearchBody(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=8, ge=1, le=32)
    user_id: str | None = None


class MemoryRecordResponse(BaseModel):
    id: UUID
    user_id: str
    kind: MemoryKind
    content: str
    importance: float
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class MemoryBundleResponse(BaseModel):
    preferences: list[MemoryRecordResponse]
    semantic: list[MemoryRecordResponse]
    episodic: list[MemoryRecordResponse]
    recent_turns: list[str] = Field(default_factory=list)


class StartConversationBody(BaseModel):
    room_name: str
    user_id: str | None = None


class AppendTurnBody(BaseModel):
    conversation_id: UUID
    room_name: str
    role: str
    content: str
    user_id: str | None = None
    extract: bool = True


class ToolInvokeBody(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None


class ToolSpecResponse(BaseModel):
    name: str
    description: str
    capabilities: list[str]
    required_permissions: list[str]
    parameters: dict[str, Any]


class ToolInvokeResponse(BaseModel):
    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
