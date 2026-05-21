import asyncio
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import os
import requests
import logging
from dotenv import load_dotenv
import aiohttp

from pydantic import BaseModel
from typing import List, Optional, Literal

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_infra.mcp_server_map_geo.schema import GeoCoordinateRequest, ReverseGeocodeRequest



load_dotenv()
MAPY_API_KEY = os.getenv("MAPY_API_KEY")

if not MAPY_API_KEY:
    print("!!!: MAPY_API_KEY не знайдено в .env!", file=sys.stderr)

app = Server("mcp-server-mapy-geocode")

logger = logging.getLogger("geo_logger")
logging.basicConfig(level=logging.DEBUG)

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Повертає список інструментів, які може використовувати LLM-агент"""
    return [
        Tool(
            name="geocode_location",
            description=(
                "Пряме геокодування: з текстового запиту знаходить координати. "
                "Добре працює для гір, вершин, перевалів, притулків, сіл у Карпатах."
            ),
            inputSchema=GeoCoordinateRequest.model_json_schema()
        ),
        Tool(
            name="reverse_geocode",
            description=(
                "Зворотнє геокодування: за координатами повертає назви найближчих об’єктів. "
                "Корисно, коли є тільки широта/довгота — наприклад, з GPS-треку."
            ),
            inputSchema=ReverseGeocodeRequest.model_json_schema()
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    logger.debug(f"Вхідні дані: {arguments}")

    if name == "geocode_location":
        req = GeoCoordinateRequest(**arguments)

        url = "https://api.mapy.com/v1/geocode"
        headers = {"X-Mapy-Api-Key": MAPY_API_KEY}

        params = {
            "query": req.query,
            "lang": req.lang or "uk",
            "limit": req.limit or 5
        }

        if req.type:
            params["type"] = ",".join(req.type)
        if req.locality:
            params["locality"] = ",".join(req.locality)  
        if req.preferBBox:
            params["preferBBox"] = ",".join(map(str, req.preferBBox))
        if req.preferNear:
            params["preferNear"] = ",".join(map(str, req.preferNear))
        if req.preferNearPosition is not None:
            params["preferNearPosition"] = str(req.preferNearPosition)

        logger.debug(f"Параметри API-запиту: {params}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                result = await response.json()
                logger.debug(f"Відповідь API: {result}")

        items = result.get("items", [])
        results = []

        for item in items:
            pos = item.get("position", {})
            lat = pos.get("lat")
            lon = pos.get("lon")
            if lat is None or lon is None:
                continue

            label = item.get("label", "").lower()
            item_type = item.get("type", "").lower()
            
            is_valid = True 
            
            if not is_valid:
                continue

            country_iso = next(
                (r.get("isoCode") for r in item.get("regionalStructure", []) if r.get("isoCode")),
                None
            )

            results.append({
                "name": item.get("name", ""),
                "label": item.get("label", ""),
                "type": item.get("type", ""),
                "lat": lat,
                "lon": lon,
                "countryIso": country_iso,
            })

        output = {
            "query": req.query,
            "found": len(results),
            "results": results
        }

        return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False))]

    elif name == "reverse_geocode":
        req = ReverseGeocodeRequest(**arguments)

        url = "https://api.mapy.com/v1/rgeocode"
        headers = {"X-Mapy-Api-Key": MAPY_API_KEY}

        params = {
            "lat": str(req.lat),
            "lon": str(req.lon),
            "lang": req.lang or "uk",
            "limit": req.limit or 5,
            "radius": req.radius or 800,
        }

        if req.type:
            params["type"] = ",".join(req.type)

        logger.debug(f"Параметри API-запиту: {params}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                content_type = response.headers.get("Content-Type", "")
                if response.status >= 400:
                    body = await response.text()
                    error = {
                        "error": "Mapy reverse geocoding request failed",
                        "status": response.status,
                        "content_type": content_type,
                        "url": str(response.url),
                        "response_preview": body[:500],
                    }
                    return [TextContent(type="text", text=json.dumps(error, ensure_ascii=False))]

                if "application/json" not in content_type.lower():
                    body = await response.text()
                    error = {
                        "error": "Mapy reverse geocoding returned non-JSON response",
                        "status": response.status,
                        "content_type": content_type,
                        "url": str(response.url),
                        "response_preview": body[:500],
                    }
                    return [TextContent(type="text", text=json.dumps(error, ensure_ascii=False))]

                result = await response.json()
                logger.debug(f"Відповідь API: {result}")

        items = result.get("items", [])
        results = []

        for item in items:
            pos = item.get("position", {})
            distance = item.get("distance")

            country_iso = next(
                (r.get("isoCode") for r in item.get("regionalStructure", []) if r.get("isoCode")),
                None
            )

            results.append({
                "name": item.get("name", ""),
                "label": item.get("label", ""),
                "type": item.get("type", ""),
                "distance_m": distance,
                "lat": pos.get("lat"),
                "lon": pos.get("lon"),
                "countryIso": country_iso,
            })

        output = {
            "coordinates": [req.lon, req.lat],
            "radius_m": req.radius,
            "found": len(results),
            "results": results
        }

        return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False))]

    else:
        return [TextContent(type="text", text=f"Невідомий інструмент: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())