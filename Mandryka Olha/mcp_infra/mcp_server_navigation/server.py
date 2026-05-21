import asyncio
import json
import sys
import requests
import functools
import os
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv
from math import sqrt  

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_server_navigation.schema import RoutingRequest

load_dotenv()
MAPY_API_KEY = os.getenv("MAPY_API_KEY")

app = Server("mcp-server-navigation")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="plan_route",
            description="Планування маршруту з Mapy.cz Routing API. Повертає геометрію та базові параметри.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                    "end": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                    "routeType": {
                        "type": "string",
                        "enum": ["car_fast", "car_fast_traffic", "car_short", "foot_fast", "foot_hiking", "bike_road", "bike_mountain"],
                        "default": "foot_hiking"
                    },
                    "lang": {"type": "string", "enum": ["en", "uk"], "default": "uk"},
                    "avoidHighways": {"type": "boolean", "default": False},
                    "waypoints": {"type": ["array", "null"], "items": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}, "maxItems": 15}
                },
                "required": ["start", "end"]
            }
        ),
        Tool(
            name="visualize_route_html",
            description="Інтерактивна карта маршруту на Leaflet.",
            inputSchema={"type": "object", "properties": {"route_data": {"type": "object"}}, "required": ["route_data"]}
        ),
        Tool(
            name="get_route_statistics",
            description="Базова статистика маршруту.",
            inputSchema={"type": "object", "properties": {"route_data": {"type": "object"}}, "required": ["route_data"]}
        ),
        Tool(
            name="calculate_route_difficulty",
            description="Аналіз складності маршруту з математичною корекцією похибки висоти методом IDW-інтерполяції за даними karpaty.rocks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "route_data": {"type": "object"},
                    "difficulty_scale": {"type": "string", "enum": ["easy", "medium", "hard", "custom"], "default": "medium"},
                    "custom_thresholds": {"type": ["array", "null"], "items": {"type": "number"}, "minItems": 2, "maxItems": 2}
                },
                "required": ["route_data"]
            }
        ),
        Tool(
            name="render_route_map",
            description="Генерація HTML-карти з маршрутом та маркерними точками.",
            inputSchema={
                "type": "object",
                "properties": {
                    "route_geometry": {"type": "object"},
                    "output_path": {"type": "string"},
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "lat": {"type": "number"},
                                "lon": {"type": "number"},
                                "label": {"type": "string"}
                            }
                        }
                    }
                },
                "required": ["route_geometry", "output_path"]
            }
        )
    ]

def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}г {minutes}хв" if hours > 0 else f"{minutes}хв"

def format_distance(meters: float) -> str:
    return f"{meters/1000:.2f} км" if meters >= 1000 else f"{meters:.0f} м"

def reverse_coords(coords):
    if not coords: return []
    if isinstance(coords[0], (int, float)): return [coords[1], coords[0]]
    return [reverse_coords(c) for c in coords]

def _js_escape(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", " ")
        .replace("\r", " ")
    )

def clean_geometry(geometry_raw):
    if not isinstance(geometry_raw, dict):
        return {}
    
    if geometry_raw.get("type") == "FeatureCollection" and "features" in geometry_raw:
        features = geometry_raw["features"]
        if features:
            return features[0].get("geometry", {})
            
    if geometry_raw.get("type") == "Feature" and "geometry" in geometry_raw:
        return geometry_raw["geometry"]
    
    return geometry_raw

def get_elevations(coords_2d: list) -> list[float]:
    if not MAPY_API_KEY:
        raise ValueError("MAPY_API_KEY не знайдено в .env")

    elevations = []
    batch_size = 256
    for i in range(0, len(coords_2d), batch_size):
        batch = coords_2d[i:i + batch_size]
        positions_str = ";".join(f"{lon},{lat}" for lon, lat in batch)
        url = "https://api.mapy.cz/v1/elevation"
        params = {"positions": positions_str, "lang": "uk"}
        response = requests.get(url, headers={"X-Mapy-Api-Key": MAPY_API_KEY}, params=params, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Помилка Elevation API: {response.status_code} — {response.text}")
        data = response.json()
        batch_elev = [item.get("elevation") for item in data.get("items", [])]
        elevations.extend(batch_elev)
    return elevations

def find_peak_on_karpaty_rocks(center_lat: float, center_lon: float) -> dict | None:
    search_url = "https://karpaty.rocks/api/rocks"
    params = {
        "lat": round(center_lat, 6),
        "lon": round(center_lon, 6),
        "radius": 5000,
        "limit": 3
    }
    try:
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        data = response.json()
        candidates = data.get("data", [])
        if not candidates:
            return None
        peak = candidates[0]
        return {
            "name": peak.get("name", "Невідома вершина"),
            "altitude": peak.get("altitude"),
            "lat": peak.get("lat"),
            "lon": peak.get("lon"),
            "url": f"https://karpaty.rocks/rocks/{peak.get('slug', '')}"
        }
    except Exception:
        return None



@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    if name == "plan_route":
        try:
            request = RoutingRequest(**arguments)
        except ValidationError as e:
            return [TextContent(type="text", text=f"Помилка валідації: {str(e)}")]

        url = "https://api.mapy.cz/v1/routing/route"
        params = {
            "start": f"{request.start[0]},{request.start[1]}",
            "end": f"{request.end[0]},{request.end[1]}",
            "routeType": request.routeType,
            "lang": request.lang,
            "format": "geojson",
            "avoidHighways": str(request.avoidHighways).lower(),
        }
        if request.waypoints:
            params["waypoints"] = ";".join(f"{wp[0]},{wp[1]}" for wp in request.waypoints)

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            functools.partial(
                requests.get, url,
                headers={"X-Mapy-Api-Key": MAPY_API_KEY},
                params=params,
                timeout=20,
            )
        )
        if response.status_code != 200:
            return [TextContent(type="text", text=f"Помилка Routing API: {response.status_code} {response.text}")]

        data = response.json()
        
        total_length = data.get("length", 0)  
        
        import math
        start_lat, start_lon = request.start[1], request.start[0]
        end_lat, end_lon = request.end[1], request.end[0]
        
        dlat = math.radians(end_lat - start_lat)
        dlon = math.radians(end_lon - start_lon)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        linear_distance_km = 6371 * c  
        
        route_length_km = total_length / 1000.0
        
        if route_length_km > linear_distance_km * 5 and linear_distance_km > 2:
            warning_note = f"""
ПОПЕРЕДЖЕННЯ: Маршрут може бути нереально довгим!
Довжина маршруту: {route_length_km:.1f} км
Пряма відстань: {linear_distance_km:.1f} км  
Коефіцієнт: {route_length_km/linear_distance_km:.1f}x

Можливі причини: неправильні проміжні точки, обходи або помилки GPS.
"""
            data["validation_warning"] = warning_note.strip()
        
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
    
    elif name == "visualize_route_html":
        route_data = arguments.get("route_data")
        if not route_data: return [TextContent(type="text", text="Немає даних")]
        
        geometry = clean_geometry(route_data)
        if not geometry:
            geometry = clean_geometry(route_data.get("geometry", {}))

        coords = geometry.get("coordinates", [])
        if not coords:
             return [TextContent(type="text", text="Немає координат у геометрії")]

        center = [sum(c[1] for c in coords) / len(coords), sum(c[0] for c in coords) / len(coords)]
        
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>#map {{ height: 100vh; width: 100%; }}</style></head>
        <body><div id="map"></div><script>
        const map = L.map('map').setView([{center[0]}, {center[1]}], 13);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);
        L.geoJSON({json.dumps(geometry)}, {{style: {{color: "blue", weight: 5, opacity: 0.7}}}}).addTo(map);
        </script></body></html>"""
        return [TextContent(type="text", text=html)]

    elif name == "get_route_statistics":
        route_data = arguments.get("route_data")
        l = route_data.get("length")
        d = route_data.get("duration")
        
        if l is None and "features" in route_data:
            props = route_data["features"][0].get("properties", {})
            l = props.get("length")
            d = props.get("duration")

        l = l or 0
        d = d or 1 
        
        stats = {
            "distance_m": l,
            "formatted_distance": format_distance(l),
            "duration_s": d,
            "formatted_duration": format_duration(d),
            "avg_speed_kmh": round(l/d*3.6, 1),
            "summary": f"Відстань: {format_distance(l)}, Час: {format_duration(d)}"
        }
        return [TextContent(type="text", text=json.dumps(stats, ensure_ascii=False))]

    elif name == "render_route_map":
        try:
            raw_geom = arguments.get("route_geometry")
            geom = clean_geometry(raw_geom)
            
            if not geom or not geom.get("coordinates"):
                if isinstance(raw_geom, dict):
                    geom = clean_geometry(raw_geom.get("geometry", {}))

            path = arguments.get("output_path")
            points = arguments.get("points", [])
            
            if points:
                clat = sum(p["lat"] for p in points) / len(points)
                clon = sum(p["lon"] for p in points) / len(points)
            elif geom and geom.get("coordinates"):
                coords = geom["coordinates"]
                clat = sum(c[1] for c in coords) / len(coords)
                clon = sum(c[0] for c in coords) / len(coords)
            else:
                clat, clon = 48.16, 24.5

            markers_js = "\n".join([
                f"L.marker([{p['lat']}, {p['lon']}]).addTo(map).bindPopup('{_js_escape(p.get('label', 'Точка'))}');"
                for p in points
            ])

            mapy_tile_url = ""
            mapy_attribution = ""
            if MAPY_API_KEY:
                mapy_tile_url = f"https://api.mapy.cz/v1/maptiles/outdoor/256/{{z}}/{{x}}/{{y}}?apikey={MAPY_API_KEY}"
                mapy_attribution = "&copy; <a href='https://api.mapy.cz/'>Mapy.cz</a>"

            html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                #map {{ height: 90vh; width: 100%; }}
                .info-panel {{ padding: 10px; background: white; font-family: sans-serif; }}
            </style></head>
            <body>
            <div id="map"></div>
            <div class="info-panel">
                <b>Маршрут:</b> <span id="route-name">План походу</span> | 
                <a href="https://mapy.cz/turisticka?source=coor&x={clon}&y={clat}&z=13" target="_blank">Відкрити на Mapy.cz</a>
            </div>
            <script>
            const map = L.map('map').setView([{clat}, {clon}], 12);
            const mapyTileUrl = {json.dumps(mapy_tile_url)};
            if (mapyTileUrl) {{
                L.tileLayer(mapyTileUrl, {{
                    attribution: {json.dumps(mapy_attribution)}
                }}).addTo(map);
            }} else {{
                L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                    subdomains: 'abcd',
                    maxZoom: 19
                }}).addTo(map);
            }}
            
            const routeGeom = {json.dumps(geom)};
            if (routeGeom && routeGeom.coordinates && routeGeom.coordinates.length > 0) {{
                L.geoJSON(routeGeom, {{
                    style: {{ color: "#0078ff", weight: 6, opacity: 0.8 }}
                }}).addTo(map);
            }}
            
            {markers_js}
            </script></body></html>"""
            
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            
            return [TextContent(type="text", text=f"Карта успішно створена: {path}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Помилка рендерингу: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())