from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import Principal, get_principal, resolve_user_id
from app.api.schemas_phase34 import (
    GraphEdgeBody,
    GraphEdgeResponse,
    GraphNeighborhoodResponse,
    GraphNodeBody,
    GraphNodeResponse,
)
from app.domain.graph import NodeLabel
from app.services.graph_service import KnowledgeGraphService

router = APIRouter(prefix="/v1/graph", tags=["graph"])


def get_graph_service(request: Request) -> KnowledgeGraphService:
    service = getattr(request.app.state, "graph_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Graph service unavailable")
    return service


@router.post("/nodes", response_model=GraphNodeResponse, status_code=201)
async def create_node(
    body: GraphNodeBody,
    principal: Annotated[Principal, Depends(get_principal)],
    graph: Annotated[KnowledgeGraphService, Depends(get_graph_service)],
) -> GraphNodeResponse:
    user_id = resolve_user_id(principal, body.user_id)
    node = await graph.upsert_node(
        clerk_user_id=user_id,
        label=body.label,
        name=body.name,
        properties=body.properties,
    )
    return GraphNodeResponse(
        id=node.id,
        user_id=node.user_id,
        label=node.label,
        name=node.name,
        properties=node.properties,
    )


@router.get("/nodes", response_model=list[GraphNodeResponse])
async def list_nodes(
    principal: Annotated[Principal, Depends(get_principal)],
    graph: Annotated[KnowledgeGraphService, Depends(get_graph_service)],
    label: NodeLabel | None = None,
    user_id: str | None = Query(default=None),
) -> list[GraphNodeResponse]:
    resolved = resolve_user_id(principal, user_id)
    nodes = await graph.list_nodes(clerk_user_id=resolved, label=label)
    return [
        GraphNodeResponse(
            id=n.id,
            user_id=n.user_id,
            label=n.label,
            name=n.name,
            properties=n.properties,
        )
        for n in nodes
    ]


@router.post("/edges", response_model=GraphEdgeResponse, status_code=201)
async def create_edge(
    body: GraphEdgeBody,
    principal: Annotated[Principal, Depends(get_principal)],
    graph: Annotated[KnowledgeGraphService, Depends(get_graph_service)],
) -> GraphEdgeResponse:
    user_id = resolve_user_id(principal, body.user_id)
    try:
        edge = await graph.link(
            clerk_user_id=user_id,
            source_id=body.source_id,
            target_id=body.target_id,
            edge_type=body.edge_type,
            properties=body.properties,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GraphEdgeResponse(
        id=edge.id,
        source_id=edge.source_id,
        target_id=edge.target_id,
        edge_type=edge.edge_type,
        properties=edge.properties,
    )


@router.get("/nodes/{node_id}/neighborhood", response_model=GraphNeighborhoodResponse)
async def neighborhood(
    node_id: UUID,
    principal: Annotated[Principal, Depends(get_principal)],
    graph: Annotated[KnowledgeGraphService, Depends(get_graph_service)],
    user_id: str | None = Query(default=None),
) -> GraphNeighborhoodResponse:
    resolved = resolve_user_id(principal, user_id)
    try:
        neighborhood = await graph.neighborhood(clerk_user_id=resolved, node_id=node_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GraphNeighborhoodResponse(
        nodes=[
            GraphNodeResponse(
                id=n.id,
                user_id=n.user_id,
                label=n.label,
                name=n.name,
                properties=n.properties,
            )
            for n in neighborhood.nodes
        ],
        edges=[
            GraphEdgeResponse(
                id=e.id,
                source_id=e.source_id,
                target_id=e.target_id,
                edge_type=e.edge_type,
                properties=e.properties,
            )
            for e in neighborhood.edges
        ],
    )
