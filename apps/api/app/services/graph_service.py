from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.graph import EdgeType, GraphEdge, GraphNeighborhood, GraphNode, NodeLabel
from app.infrastructure.db.models import (
    EdgeType as DbEdgeType,
)
from app.infrastructure.db.models import (
    KnowledgeEdgeRow,
    KnowledgeNodeRow,
    UserRow,
)
from app.infrastructure.db.models import (
    NodeLabel as DbNodeLabel,
)


class KnowledgeGraphService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = session_factory

    async def _user_uuid(self, session: AsyncSession, clerk_user_id: str) -> UUID:
        user = await session.scalar(select(UserRow).where(UserRow.clerk_user_id == clerk_user_id))
        if user:
            return user.id
        user = UserRow(clerk_user_id=clerk_user_id)
        session.add(user)
        await session.flush()
        return user.id

    async def upsert_node(
        self,
        *,
        clerk_user_id: str,
        label: NodeLabel,
        name: str,
        properties: dict[str, Any] | None = None,
        node_id: UUID | None = None,
    ) -> GraphNode:
        async with self._sessions() as session:
            user_id = await self._user_uuid(session, clerk_user_id)
            if node_id:
                row = await session.get(KnowledgeNodeRow, node_id)
                if row is None or row.user_id != user_id:
                    raise ValueError("Node not found")
                row.name = name
                row.properties = properties or {}
                row.label = DbNodeLabel(label.value)
            else:
                row = KnowledgeNodeRow(
                    user_id=user_id,
                    label=DbNodeLabel(label.value),
                    name=name,
                    properties=properties or {},
                )
                session.add(row)
            await session.commit()
            await session.refresh(row)
            return GraphNode(
                id=row.id,
                user_id=clerk_user_id,
                label=NodeLabel(row.label.value),
                name=row.name,
                properties=row.properties or {},
                created_at=row.created_at,
            )

    async def link(
        self,
        *,
        clerk_user_id: str,
        source_id: UUID,
        target_id: UUID,
        edge_type: EdgeType,
        properties: dict[str, Any] | None = None,
    ) -> GraphEdge:
        async with self._sessions() as session:
            user_id = await self._user_uuid(session, clerk_user_id)
            for node_id in (source_id, target_id):
                node = await session.get(KnowledgeNodeRow, node_id)
                if node is None or node.user_id != user_id:
                    raise ValueError("Node not found for edge")
            row = KnowledgeEdgeRow(
                user_id=user_id,
                source_id=source_id,
                target_id=target_id,
                edge_type=DbEdgeType(edge_type.value),
                properties=properties or {},
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return GraphEdge(
                id=row.id,
                user_id=clerk_user_id,
                source_id=row.source_id,
                target_id=row.target_id,
                edge_type=EdgeType(row.edge_type.value),
                properties=row.properties or {},
            )

    async def neighborhood(
        self,
        *,
        clerk_user_id: str,
        node_id: UUID,
        limit: int = 50,
    ) -> GraphNeighborhood:
        async with self._sessions() as session:
            user_id = await self._user_uuid(session, clerk_user_id)
            center = await session.get(KnowledgeNodeRow, node_id)
            if center is None or center.user_id != user_id:
                raise ValueError("Node not found")

            edges = (
                await session.scalars(
                    select(KnowledgeEdgeRow)
                    .where(
                        KnowledgeEdgeRow.user_id == user_id,
                        or_(
                            KnowledgeEdgeRow.source_id == node_id,
                            KnowledgeEdgeRow.target_id == node_id,
                        ),
                    )
                    .limit(limit)
                )
            ).all()

            related_ids = {node_id}
            for edge in edges:
                related_ids.add(edge.source_id)
                related_ids.add(edge.target_id)

            nodes = (
                await session.scalars(
                    select(KnowledgeNodeRow).where(
                        KnowledgeNodeRow.user_id == user_id,
                        KnowledgeNodeRow.id.in_(related_ids),
                    )
                )
            ).all()

            return GraphNeighborhood(
                nodes=[
                    GraphNode(
                        id=n.id,
                        user_id=clerk_user_id,
                        label=NodeLabel(n.label.value),
                        name=n.name,
                        properties=n.properties or {},
                        created_at=n.created_at,
                    )
                    for n in nodes
                ],
                edges=[
                    GraphEdge(
                        id=e.id,
                        user_id=clerk_user_id,
                        source_id=e.source_id,
                        target_id=e.target_id,
                        edge_type=EdgeType(e.edge_type.value),
                        properties=e.properties or {},
                    )
                    for e in edges
                ],
            )

    async def list_nodes(
        self,
        *,
        clerk_user_id: str,
        label: NodeLabel | None = None,
        limit: int = 50,
    ) -> list[GraphNode]:
        async with self._sessions() as session:
            user_id = await self._user_uuid(session, clerk_user_id)
            stmt = select(KnowledgeNodeRow).where(KnowledgeNodeRow.user_id == user_id)
            if label:
                stmt = stmt.where(KnowledgeNodeRow.label == DbNodeLabel(label.value))
            rows = (await session.scalars(stmt.order_by(KnowledgeNodeRow.updated_at.desc()).limit(limit))).all()
            return [
                GraphNode(
                    id=n.id,
                    user_id=clerk_user_id,
                    label=NodeLabel(n.label.value),
                    name=n.name,
                    properties=n.properties or {},
                    created_at=n.created_at,
                )
                for n in rows
            ]
