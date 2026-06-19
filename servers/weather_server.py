import os
import httpx
import uvicorn
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_KEY = os.getenv(
    "GAODE_MAPS_API_KEY"
)

mcp = FastMCP("weather-server")


async def reverse_geocode(
    latitude: float,
    longitude: float
) -> str:

    url = (
        "https://restapi.amap.com"
        "/v3/geocode/regeo"
    )

    async with httpx.AsyncClient() as client:

        resp = await client.get(
            url,
            params={
                "key": API_KEY,
                "location":
                    f"{longitude},{latitude}",
                "extensions": "base"
            },
            timeout=10
        )

    data = resp.json()

    if data["status"] != "1":
        raise RuntimeError(data)

    address = data[
        "regeocode"
    ]["addressComponent"]

    city = address.get("city")

    if isinstance(city, list):
        city = city[0] if city else ""

    return city or address["province"]


async def query_weather(
    city: str
):

    url = (
        "https://restapi.amap.com"
        "/v3/weather/weatherInfo"
    )

    async with httpx.AsyncClient() as client:

        resp = await client.get(
            url,
            params={
                "key": API_KEY,
                "city": city,
                "extensions": "base"
            },
            timeout=10
        )

    data = resp.json()

    if data["status"] != "1":
        raise RuntimeError(data)

    return data["lives"][0]


@mcp.tool()
async def get_current_weather(
    latitude: float,
    longitude: float
) -> str:
    """
    根据经纬度获取天气
    """

    city = await reverse_geocode(
        latitude,
        longitude
    )

    weather = await query_weather(
        city
    )

    return (
        f"城市: {weather['city']}\n"
        f"天气: {weather['weather']}\n"
        f"温度: {weather['temperature']}℃\n"
        f"湿度: {weather['humidity']}%\n"
        f"风向: {weather['winddirection']}\n"
        f"风力: {weather['windpower']}级"
    )




if __name__ == "__main__":

    app = mcp.sse_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7001
    )