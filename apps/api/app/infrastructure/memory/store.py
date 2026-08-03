from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.interfaces.memory import (
    EmbeddingProvider,
    MemoryKind,
    MemoryRecord,
    MemoryWrite,
)
from app.infrastructure.db.models import (
    ConversationRow,
    ConversationTurnRow,
    MemoryRow,
    UserRow,
)
from app.infrastructure.db.models import (
    MemoryKind as DbMemoryKind,
)
from app.infrastructure.memory.dedup import content_hash
from app.infrastructure.memory.scoring import combine_retrieval_score


class PostgresMemoryStore:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embeddings: EmbeddingProvider,
    ) -> None:
        self._sessions = session_factory
        self._embeddings = embeddings

    async def ensure_user(self, clerk_user_id: str) -> UUID:
        async with self._sessions() as session:
            existing = await session.scalar(
                select(UserRow).where(UserRow.clerk_user_id == clerk_user_id)
            )
            if existing:
                return existing.id
            user = UserRow(clerk_user_id=clerk_user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user.id

    async def upsert_memory(self, write: MemoryWrite) -> MemoryRecord:
        user_uuid = await self.ensure_user(write.user_id)
        digest = content_hash(write.content)
        vectors = await self._embeddings.embed([write.content])
        embedding = vectors[0] if vectors else None

        async with self._sessions() as session:
            stmt = (
                insert(MemoryRow)
                .values(
                    user_id=user_uuid,
                    kind=DbMemoryKind(write.kind.value),
                    content=write.content,
                    content_hash=digest,
                    importance=write.importance,
                    embedding=embedding,
                    metadata_json=write.metadata,
                )
                .on_conflict_do_update(
                    constraint="uq_memory_dedup",
                    set_={
                        "importance": write.importance,
                        "metadata_json": write.metadata,
                        "embedding": embedding,
                        "content": write.content,
                    },
                )
                .returning(MemoryRow)
            )
            row = (await session.execute(stmt)).scalar_one()
            await session.commit()
            return self._to_record(row, write.user_id, score=1.0)

    async def search(
        self,
        *,
        clerk_user_id: str,
        query: str,
        limit: int = 8,
        kinds: list[MemoryKind] | None = None,
    ) -> list[MemoryRecord]:
        user_uuid = await self.ensure_user(clerk_user_id)
        query_vec = (await self._embeddings.embed([query]))[0]

        async with self._sessions() as session:
            kind_filter = ""
            params: dict = {"user_id": str(user_uuid), "limit": limit * 3}
            if kinds:
                kind_filter = "AND kind = ANY(:kinds)"
                params["kinds"] = [k.value for k in kinds]

            # pgvector cosine distance; convert to similarity in Python.
            sql = text(
                f"""
                SELECT id, user_id, kind, content, importance, access_count,
                       metadata_json, created_at,
                       (1 - (embedding <=> CAST(:embedding AS vector))) AS similarity
                FROM memories
                WHERE user_id = :user_id
                  AND embedding IS NOT NULL
                  {kind_filter}
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            )
            params["embedding"] = "[" + ",".join(str(float(x)) for x in query_vec) + "]"
            result = await session.execute(sql, params)
            rows = result.mappings().all()

            scored: list[MemoryRecord] = []
            for row in rows:
                score = combine_retrieval_score(
                    similarity=float(row["similarity"] or 0.0),
                    importance=float(row["importance"]),
                    created_at=row["created_at"],
                    access_count=int(row["access_count"] or 0),
                )
                scored.append(
                    MemoryRecord(
                        id=row["id"],
                        user_id=clerk_user_id,
                        kind=MemoryKind(row["kind"] if isinstance(row["kind"], str) else row["kind"].value),
                        content=row["content"],
                        importance=float(row["importance"]),
                        score=score,
                        metadata=row["metadata_json"] or {},
                        created_at=row["created_at"],
                    )
                )

            scored.sort(key=lambda item: item.score, reverse=True)
            top = scored[:limit]

            if top:
                ids = [str(item.id) for item in top]
                await session.execute(
                    text(
                        """
                        UPDATE memories
                        SET access_count = access_count + 1,
                            last_accessed_at = NOW()
                        WHERE id = ANY(CAST(:ids AS uuid[]))
                        """
                    ),
                    {"ids": ids},
                )
                await session.commit()

            return top

    async def list_by_kind(
        self,
        *,
        clerk_user_id: str,
        kind: MemoryKind,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        user_uuid = await self.ensure_user(clerk_user_id)
        async with self._sessions() as session:
            result = await session.scalars(
                select(MemoryRow)
                .where(
                    MemoryRow.user_id == user_uuid,
                    MemoryRow.kind == DbMemoryKind(kind.value),
                )
                .order_by(MemoryRow.importance.desc(), MemoryRow.created_at.desc())
                .limit(limit)
            )
            return [self._to_record(row, clerk_user_id) for row in result.all()]

    async def start_conversation(self, clerk_user_id: str, room_name: str) -> UUID:
        user_uuid = await self.ensure_user(clerk_user_id)
        async with self._sessions() as session:
            conversation = ConversationRow(user_id=user_uuid, room_name=room_name)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation.id

    async def append_turn(
        self,
        *,
        conversation_id: UUID,
        role: str,
        content: str,
    ) -> None:
        async with self._sessions() as session:
            session.add(
                ConversationTurnRow(
                    conversation_id=conversation_id,
                    role=role,
                    content=content,
                )
            )
            await session.commit()

    def _to_record(self, row: MemoryRow, clerk_user_id: str, score: float = 0.0) -> MemoryRecord:
        kind_value = row.kind.value if hasattr(row.kind, "value") else str(row.kind)
        return MemoryRecord(
            id=row.id,
            user_id=clerk_user_id,
            kind=MemoryKind(kind_value),
            content=row.content,
            importance=row.importance,
            score=score,
            metadata=row.metadata_json or {},
            created_at=row.created_at or datetime.now(UTC),
        )
