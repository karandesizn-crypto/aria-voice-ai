from __future__ import annotations

import json

from app.domain.interfaces.memory import MemoryBundle, MemoryKind, MemoryStore, MemoryWrite
from app.infrastructure.redis.client import SessionCache


class MemoryService:
    def __init__(self, store: MemoryStore, cache: SessionCache) -> None:
        self._store = store
        self._cache = cache

    async def start_conversation(self, user_id: str, room_name: str):
        return await self._store.start_conversation(user_id, room_name)

    async def remember(self, write: MemoryWrite):
        record = await self._store.upsert_memory(write)
        await self._cache.set_memory_bundle(write.user_id, "")  # invalidate
        return record

    async def search(self, *, user_id: str, query: str, limit: int = 8):
        return await self._store.search(clerk_user_id=user_id, query=query, limit=limit)

    async def build_bundle(self, *, user_id: str, room_name: str | None = None) -> MemoryBundle:
        preferences = await self._store.list_by_kind(
            clerk_user_id=user_id, kind=MemoryKind.PREFERENCE, limit=12
        )
        semantic = await self._store.list_by_kind(
            clerk_user_id=user_id, kind=MemoryKind.SEMANTIC, limit=12
        )
        episodic = await self._store.list_by_kind(
            clerk_user_id=user_id, kind=MemoryKind.EPISODIC, limit=12
        )
        recent_turns: list[str] = []
        if room_name:
            recent_turns = await self._cache.get_turns(user_id, room_name)

        bundle = MemoryBundle(
            preferences=preferences,
            semantic=semantic,
            episodic=episodic,
            recent_turns=recent_turns,
        )
        await self._cache.set_memory_bundle(
            user_id,
            json.dumps(
                {
                    "preferences": [m.content for m in preferences],
                    "semantic": [m.content for m in semantic],
                    "episodic": [m.content for m in episodic],
                }
            ),
        )
        return bundle

    async def record_turn(
        self,
        *,
        user_id: str,
        room_name: str,
        conversation_id,
        role: str,
        content: str,
    ) -> None:
        await self._store.append_turn(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        await self._cache.append_turn(user_id, room_name, role, content)

    async def extract_simple_memories(self, *, user_id: str, utterance: str) -> list:
        """Lightweight heuristic extractor (LLM extraction can replace later)."""
        writes: list[MemoryWrite] = []
        lower = utterance.lower()
        if "my name is" in lower:
            name = utterance.split("my name is", 1)[-1].strip(" .")
            if name:
                writes.append(
                    MemoryWrite(
                        user_id=user_id,
                        kind=MemoryKind.SEMANTIC,
                        content=f"User's name is {name}",
                        importance=0.9,
                    )
                )
        if "i prefer" in lower or "please remember" in lower:
            writes.append(
                MemoryWrite(
                    user_id=user_id,
                    kind=MemoryKind.PREFERENCE,
                    content=utterance.strip(),
                    importance=0.8,
                )
            )
        if any(token in lower for token in ("tomorrow", "next week", "on monday", "deadline")):
            writes.append(
                MemoryWrite(
                    user_id=user_id,
                    kind=MemoryKind.EPISODIC,
                    content=utterance.strip(),
                    importance=0.7,
                )
            )
        saved = []
        for write in writes:
            saved.append(await self.remember(write))
        return saved
