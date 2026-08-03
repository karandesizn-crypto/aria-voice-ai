from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.graph import EdgeType, NodeLabel
from app.services.orchestration import AgentRole


class GraphNodeBody(BaseModel):
    label: NodeLabel
    name: str = Field(min_length=1, max_length=512)
    properties: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None


class GraphNodeResponse(BaseModel):
    id: UUID
    user_id: str
    label: NodeLabel
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeBody(BaseModel):
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    properties: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None


class GraphEdgeResponse(BaseModel):
    id: UUID
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphNeighborhoodResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class ReminderCreateBody(BaseModel):
    title: str
    body: str = ""
    due_at: datetime
    user_id: str | None = None


class ReminderResponse(BaseModel):
    id: UUID
    user_id: str
    title: str
    body: str
    due_at: datetime
    status: str
    workflow_id: str | None = None


class RouteBody(BaseModel):
    utterance: str
    user_id: str | None = None


class RouteResponse(BaseModel):
    agent: AgentRole
    reason: str
    confidence: float
    instructions: str


class AnalyticsResponse(BaseModel):
    conversations: int
    memories: int
    tool_invocations: int
    tool_success_rate: float
    top_tools: list[dict[str, Any]]
    generated_at: str
