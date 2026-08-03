from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import Principal, get_memory_service, get_principal, resolve_user_id
from app.api.schemas_memory_tools import (
    AppendTurnBody,
    MemoryBundleResponse,
    MemoryRecordResponse,
    MemorySearchBody,
    MemoryWriteBody,
    StartConversationBody,
)
from app.domain.interfaces.memory import MemoryWrite
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/v1/memory", tags=["memory"])


def _record(m) -> MemoryRecordResponse:
    return MemoryRecordResponse(
        id=m.id,
        user_id=m.user_id,
        kind=m.kind,
        content=m.content,
        importance=m.importance,
        score=m.score,
        metadata=m.metadata,
        created_at=m.created_at,
    )


@router.post("/items", response_model=MemoryRecordResponse, status_code=status.HTTP_201_CREATED)
async def write_memory(
    body: MemoryWriteBody,
    principal: Annotated[Principal, Depends(get_principal)],
    memory: Annotated[MemoryService, Depends(get_memory_service)],
) -> MemoryRecordResponse:
    user_id = resolve_user_id(principal, body.user_id)
    record = await memory.remember(
        MemoryWrite(
            user_id=user_id,
            kind=body.kind,
            content=body.content,
            importance=body.importance,
            metadata=body.metadata,
        )
    )
    return _record(record)


@router.post("/search", response_model=list[MemoryRecordResponse])
async def search_memory(
    body: MemorySearchBody,
    principal: Annotated[Principal, Depends(get_principal)],
    memory: Annotated[MemoryService, Depends(get_memory_service)],
) -> list[MemoryRecordResponse]:
    user_id = resolve_user_id(principal, body.user_id)
    records = await memory.search(user_id=user_id, query=body.query, limit=body.limit)
    return [_record(item) for item in records]


@router.get("/bundle", response_model=MemoryBundleResponse)
async def memory_bundle(
    principal: Annotated[Principal, Depends(get_principal)],
    memory: Annotated[MemoryService, Depends(get_memory_service)],
    room_name: str | None = None,
    user_id: str | None = Query(default=None),
) -> MemoryBundleResponse:
    resolved = resolve_user_id(principal, user_id)
    bundle = await memory.build_bundle(user_id=resolved, room_name=room_name)
    return MemoryBundleResponse(
        preferences=[_record(m) for m in bundle.preferences],
        semantic=[_record(m) for m in bundle.semantic],
        episodic=[_record(m) for m in bundle.episodic],
        recent_turns=bundle.recent_turns,
    )


@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def start_conversation(
    body: StartConversationBody,
    principal: Annotated[Principal, Depends(get_principal)],
    memory: Annotated[MemoryService, Depends(get_memory_service)],
) -> dict[str, UUID]:
    user_id = resolve_user_id(principal, body.user_id)
    conversation_id = await memory.start_conversation(user_id, body.room_name)
    return {"conversation_id": conversation_id}


@router.post("/turns", status_code=status.HTTP_204_NO_CONTENT)
async def append_turn(
    body: AppendTurnBody,
    principal: Annotated[Principal, Depends(get_principal)],
    memory: Annotated[MemoryService, Depends(get_memory_service)],
) -> None:
    user_id = resolve_user_id(principal, body.user_id)
    await memory.record_turn(
        user_id=user_id,
        room_name=body.room_name,
        conversation_id=body.conversation_id,
        role=body.role,
        content=body.content,
    )
    if body.extract and body.role == "user":
        await memory.extract_simple_memories(user_id=user_id, utterance=body.content)
