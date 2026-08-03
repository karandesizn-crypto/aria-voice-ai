from __future__ import annotations

import pytest

from app.domain.graph import EdgeType, NodeLabel
from app.infrastructure.graph.memory_graph import InMemoryKnowledgeGraph


@pytest.mark.asyncio
async def test_in_memory_graph_neighborhood() -> None:
    graph = InMemoryKnowledgeGraph()
    project = await graph.upsert_node(
        clerk_user_id="user_1",
        label=NodeLabel.PROJECT,
        name="Voice Platform",
    )
    task = await graph.upsert_node(
        clerk_user_id="user_1",
        label=NodeLabel.TASK,
        name="Ship Phase 4",
    )
    await graph.link(
        clerk_user_id="user_1",
        source_id=project.id,
        target_id=task.id,
        edge_type=EdgeType.OWNS,
    )
    neighborhood = await graph.neighborhood(clerk_user_id="user_1", node_id=project.id)
    assert len(neighborhood.nodes) == 2
    assert len(neighborhood.edges) == 1
