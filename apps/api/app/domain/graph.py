from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class NodeLabel(str, Enum):
    USER = "user"
    PROJECT = "project"
    GOAL = "goal"
    TASK = "task"
    MEETING = "meeting"
    DOCUMENT = "document"
    PREFERENCE = "preference"
    PERSON = "person"


class EdgeType(str, Enum):
    OWNS = "owns"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    ATTENDS = "attends"
    REFERENCES = "references"
    PREFERS = "prefers"
    ASSIGNED_TO = "assigned_to"


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: UUID
    user_id: str
    label: NodeLabel
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GraphEdge:
    id: UUID
    user_id: str
    source_id: UUID
    target_id: UUID
    edge_type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GraphNeighborhood:
    nodes: list[GraphNode]
    edges: list[GraphEdge]
