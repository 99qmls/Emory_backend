# app/services/mcp_client/__init__.py

from typing import Optional

from .client import MCPBaseClient

MCPWeatherClient = MCPBaseClient

_weather_client: Optional[MCPBaseClient] = None


def set_weather_client(client):

    global _weather_client

    _weather_client = client


def get_weather_client():

    return _weather_client