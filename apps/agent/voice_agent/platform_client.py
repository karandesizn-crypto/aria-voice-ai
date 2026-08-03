from __future__ import annotations

from typing import Any

import httpx


class PlatformApiClient:
    """Agent → API client for memory and tools."""

    def __init__(
        self,
        *,
        base_url: str,
        service_token: str,
        user_id: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = service_token
        self._user_id = user_id
        self._http = http_client or httpx.AsyncClient(timeout=20.0)
        self._owns_client = http_client is None

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "X-User-Id": self._user_id,
            "Content-Type": "application/json",
        }

    async def get_memory_bundle(self, room_name: str | None = None) -> dict[str, Any]:
        params = {"user_id": self._user_id}
        if room_name:
            params["room_name"] = room_name
        response = await self._http.get(
            f"{self._base_url}/v1/memory/bundle",
            params=params,
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def start_conversation(self, room_name: str) -> str:
        response = await self._http.post(
            f"{self._base_url}/v1/memory/conversations",
            headers=self._headers(),
            json={"room_name": room_name, "user_id": self._user_id},
        )
        response.raise_for_status()
        return response.json()["conversation_id"]

    async def append_turn(
        self,
        *,
        conversation_id: str,
        room_name: str,
        role: str,
        content: str,
    ) -> None:
        response = await self._http.post(
            f"{self._base_url}/v1/memory/turns",
            headers=self._headers(),
            json={
                "conversation_id": conversation_id,
                "room_name": room_name,
                "role": role,
                "content": content,
                "user_id": self._user_id,
                "extract": True,
            },
        )
        response.raise_for_status()

    async def invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        response = await self._http.post(
            f"{self._base_url}/v1/tools/invoke",
            headers=self._headers(),
            json={
                "tool_name": tool_name,
                "arguments": arguments,
                "user_id": self._user_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> list[dict[str, Any]]:
        response = await self._http.get(
            f"{self._base_url}/v1/tools",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def write_memory(
        self,
        *,
        kind: str,
        content: str,
        importance: float = 0.75,
    ) -> dict[str, Any]:
        response = await self._http.post(
            f"{self._base_url}/v1/memory/items",
            headers=self._headers(),
            json={
                "kind": kind,
                "content": content,
                "importance": importance,
                "user_id": self._user_id,
            },
        )
        response.raise_for_status()
        return response.json()
