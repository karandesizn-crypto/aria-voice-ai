from __future__ import annotations

from typing import Any

import httpx

from app.domain.interfaces.tools import RetryPolicy, ToolResult, ToolSchema, ToolSpec


class MapsTool:
    def __init__(self, http_client: httpx.AsyncClient, api_key: str | None) -> None:
        self._http = http_client
        self._api_key = api_key
        self.spec = ToolSpec(
            name="maps",
            description="Geocode a place or get basic location details.",
            capabilities=["maps.geocode", "location.lookup"],
            required_permissions=["tools.maps.read"],
            schema=ToolSchema(
                name="maps",
                description="Maps / geocoding lookup",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Place name or address",
                        }
                    },
                    "required": ["query"],
                },
            ),
            retry=RetryPolicy(max_attempts=3, backoff_seconds=0.3),
        )

    async def invoke(self, *, user_id: str, arguments: dict[str, Any]) -> ToolResult:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return ToolResult(ok=False, error="query is required")

        if not self._api_key:
            return ToolResult(
                ok=True,
                data={
                    "query": query,
                    "formatted_address": f"{query} (mock)",
                    "lat": 37.7749,
                    "lng": -122.4194,
                    "source": "mock",
                },
            )

        response = await self._http.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": query, "key": self._api_key},
        )
        if response.status_code >= 400:
            return ToolResult(ok=False, error=f"Maps provider error: {response.status_code}")
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            return ToolResult(ok=False, error="No results found")
        top = results[0]
        loc = ((top.get("geometry") or {}).get("location")) or {}
        return ToolResult(
            ok=True,
            data={
                "query": query,
                "formatted_address": top.get("formatted_address"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "source": "google_maps",
            },
        )
