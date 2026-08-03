from __future__ import annotations

from typing import Any

import httpx

from app.domain.interfaces.tools import RetryPolicy, ToolResult, ToolSchema, ToolSpec


class WeatherTool:
    def __init__(self, http_client: httpx.AsyncClient, api_key: str | None) -> None:
        self._http = http_client
        self._api_key = api_key
        self.spec = ToolSpec(
            name="weather",
            description="Get current weather for a city or location.",
            capabilities=["weather.read", "location.lookup"],
            required_permissions=["tools.weather.read"],
            schema=ToolSchema(
                name="weather",
                description="Current weather lookup",
                parameters={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name, e.g. San Francisco",
                        }
                    },
                    "required": ["location"],
                },
            ),
            retry=RetryPolicy(max_attempts=3, backoff_seconds=0.3),
        )

    async def invoke(self, *, user_id: str, arguments: dict[str, Any]) -> ToolResult:
        location = str(arguments.get("location", "")).strip()
        if not location:
            return ToolResult(ok=False, error="location is required")

        if not self._api_key:
            return ToolResult(
                ok=True,
                data={
                    "location": location,
                    "summary": f"Mock weather for {location}: clear skies, 72F",
                    "source": "mock",
                },
            )

        response = await self._http.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": location, "appid": self._api_key, "units": "imperial"},
        )
        if response.status_code >= 400:
            return ToolResult(ok=False, error=f"Weather provider error: {response.status_code}")
        payload = response.json()
        weather = (payload.get("weather") or [{}])[0]
        main = payload.get("main") or {}
        return ToolResult(
            ok=True,
            data={
                "location": payload.get("name") or location,
                "summary": weather.get("description", "unknown"),
                "temperature_f": main.get("temp"),
                "humidity": main.get("humidity"),
                "source": "openweather",
            },
        )
