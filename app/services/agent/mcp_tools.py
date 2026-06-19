import os
import logging
from typing import Optional

from app.services.mcp_client.client import (
    MCPBaseClient
)

logger = logging.getLogger(__name__)


class MCPWeatherService:

    def __init__(self):

        self.client = MCPBaseClient(
            os.getenv(
                "MCP_WEATHER_URL",
                "http://127.0.0.1:7001/sse"
            )
        )

    async def initialize(self):

        await self.client.initialize()

    async def get_weather(
        self,
        latitude: float,
        longitude: float
    ) -> str:

        return await self.client.call_tool(
            "get_current_weather",
            {
                "latitude": latitude,
                "longitude": longitude
            }
        )

    async def close(self):

        await self.client.close()


weather_service: Optional[
    MCPWeatherService
] = None


async def get_weather_service():

    global weather_service

    if weather_service is None:

        weather_service = (
            MCPWeatherService()
        )

    return weather_service