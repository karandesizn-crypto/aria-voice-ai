from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import Principal, get_principal, get_tool_registry, resolve_user_id
from app.api.schemas_memory_tools import ToolInvokeBody, ToolInvokeResponse, ToolSpecResponse
from app.infrastructure.tools.registry import ToolRegistry

router = APIRouter(prefix="/v1/tools", tags=["tools"])


@router.get("", response_model=list[ToolSpecResponse])
async def list_tools(
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
) -> list[ToolSpecResponse]:
    return [
        ToolSpecResponse(
            name=spec.name,
            description=spec.description,
            capabilities=spec.capabilities,
            required_permissions=spec.required_permissions,
            parameters=spec.schema.parameters,
        )
        for spec in registry.list_specs()
    ]


@router.post("/invoke", response_model=ToolInvokeResponse)
async def invoke_tool(
    body: ToolInvokeBody,
    principal: Annotated[Principal, Depends(get_principal)],
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
) -> ToolInvokeResponse:
    user_id = resolve_user_id(principal, body.user_id)
    result = await registry.invoke(
        user_id=user_id,
        tool_name=body.tool_name,
        arguments=body.arguments,
    )
    return ToolInvokeResponse(ok=result.ok, data=result.data, error=result.error)
