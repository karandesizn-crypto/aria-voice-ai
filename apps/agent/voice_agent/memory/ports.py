"""Phase 2 stubs — memory ports.

These interfaces exist so Phase 1 call sites can depend on stable contracts
without implementing persistence yet.
"""

from __future__ import annotations

from typing import Any, Protocol


class MemoryStore(Protocol):
    async def write_episode(self, user_id: str, payload: dict[str, Any]) -> str: ...

    async def search_semantic(self, user_id: str, query: str, limit: int = 8) -> list[dict[str, Any]]: ...
