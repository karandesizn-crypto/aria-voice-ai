from __future__ import annotations

import httpx

from app.core.config import Settings
from app.infrastructure.mcp.adapter import build_default_mcp_tools
from app.infrastructure.tools.maps import MapsTool
from app.infrastructure.tools.scaffolds import SCAFFOLD_TOOLS
from app.infrastructure.tools.weather import WeatherTool


def build_tools(settings: Settings, http_client: httpx.AsyncClient) -> list:
    return [
        WeatherTool(http_client, settings.openweather_api_key),
        MapsTool(http_client, settings.google_maps_api_key),
        *SCAFFOLD_TOOLS,
        *build_default_mcp_tools(http_client),
    ]
