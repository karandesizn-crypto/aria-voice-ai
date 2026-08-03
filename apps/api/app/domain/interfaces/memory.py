from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol
from uuid import UUID


class MemoryKind(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    id: UUID
    user_id: str
    kind: MemoryKind
    content: str
    importance: float
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MemoryWrite:
    user_id: str
    kind: MemoryKind
    content: str
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryBundle:
    preferences: list[MemoryRecord]
    semantic: list[MemoryRecord]
    episodic: list[MemoryRecord]
    recent_turns: list[str] = field(default_factory=list)


class EmbeddingProvider(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class MemoryStore(Protocol):
    async def ensure_user(self, clerk_user_id: str) -> UUID: ...

    async def upsert_memory(self, write: MemoryWrite) -> MemoryRecord: ...

    async def search(
        self,
        *,
        clerk_user_id: str,
        query: str,
        limit: int = 8,
        kinds: list[MemoryKind] | None = None,
    ) -> list[MemoryRecord]: ...

    async def list_by_kind(
        self,
        *,
        clerk_user_id: str,
        kind: MemoryKind,
        limit: int = 20,
    ) -> list[MemoryRecord]: ...

    async def start_conversation(self, clerk_user_id: str, room_name: str) -> UUID: ...

    async def append_turn(
        self,
        *,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> None: ...
