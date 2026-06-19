from app.services.agent.mcp_tools import (
    get_weather_service
)

_weather_service = None


async def startup_mcp():

    global _weather_service

    _weather_service = (
        await get_weather_service()
    )

    await _weather_service.initialize()


async def shutdown_mcp():

    global _weather_service

    if _weather_service:

        await _weather_service.close()