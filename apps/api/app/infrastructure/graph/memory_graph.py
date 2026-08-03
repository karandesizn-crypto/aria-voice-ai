from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.domain.graph import EdgeType, GraphEdge, GraphNeighborhood, GraphNode, NodeLabel


class InMemoryKnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: dict[UUID, GraphNode] = {}
        self.edges: dict[UUID, GraphEdge] = {}

    async def upsert_node(
        self,
        *,
        clerk_user_id: str,
        label: NodeLabel,
        name: str,
        properties: dict[str, Any] | None = None,
        node_id: UUID | None = None,
    ) -> GraphNode:
        node_id = node_id or uuid4()
        node = GraphNode(
            id=node_id,
            user_id=clerk_user_id,
            label=label,
            name=name,
            properties=properties or {},
            created_at=datetime.now(UTC),
        )
        self.nodes[node_id] = node
        return node

    async def link(
        self,
        *,
        clerk_user_id: str,
        source_id: UUID,
        target_id: UUID,
        edge_type: EdgeType,
        properties: dict[str, Any] | None = None,
    ) -> GraphEdge:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Node not found for edge")
        edge = GraphEdge(
            id=uuid4(),
            user_id=clerk_user_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {},
        )
        self.edges[edge.id] = edge
        return edge

    async def neighborhood(
        self,
        *,
        clerk_user_id: str,
        node_id: UUID,
        limit: int = 50,
    ) -> GraphNeighborhood:
        if node_id not in self.nodes:
            raise ValueError("Node not found")
        edges = [
            e
            for e in self.edges.values()
            if e.user_id == clerk_user_id and (e.source_id == node_id or e.target_id == node_id)
        ][:limit]
        ids = {node_id}
        for edge in edges:
            ids.add(edge.source_id)
            ids.add(edge.target_id)
        nodes = [self.nodes[i] for i in ids if i in self.nodes]
        return GraphNeighborhood(nodes=nodes, edges=edges)
