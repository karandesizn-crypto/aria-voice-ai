from __future__ import annotations

import pytest

from app.domain.interfaces.memory import MemoryKind, MemoryWrite
from app.services.memory_service import MemoryService


class FakeStore:
    def __init__(self) -> None:
        self.writes: list[MemoryWrite] = []

    async def upsert_memory(self, write: MemoryWrite):
        self.writes.append(write)

        class Rec:
            id = "00000000-0000-0000-0000-000000000001"
            user_id = write.user_id
            kind = write.kind
            content = write.content
            importance = write.importance
            score = 1.0
            metadata = write.metadata
            created_at = None

        return Rec()

    async def list_by_kind(self, **kwargs):
        return []

    async def search(self, **kwargs):
        return []

    async def start_conversation(self, clerk_user_id: str, room_name: str):
        return "00000000-0000-0000-0000-000000000099"

    async def append_turn(self, **kwargs) -> None:
        return None

    async def ensure_user(self, clerk_user_id: str):
        return "00000000-0000-0000-0000-000000000010"


class FakeCache:
    async def set_memory_bundle(self, user_id: str, bundle_json: str) -> None:
        return None

    async def get_memory_bundle(self, user_id: str):
        return None

    async def get_turns(self, user_id: str, room_name: str):
        return []

    async def append_turn(self, *args, **kwargs) -> None:
        return None


@pytest.mark.asyncio
async def test_extract_name_and_preference() -> None:
    store = FakeStore()
    service = MemoryService(store, FakeCache())  # type: ignore[arg-type]
    saved = await service.extract_simple_memories(
        user_id="user_1",
        utterance="My name is Sam and I prefer short answers.",
    )
    kinds = {item.kind for item in store.writes}
    assert MemoryKind.SEMANTIC in kinds
    assert MemoryKind.PREFERENCE in kinds
    assert len(saved) == 2
