import asyncio
import json
import sys
import requests
import functools
import os
from pathlib import Path
from pydantic import ValidationError
from dotenv import load_dotenv
import numpy as np
from datetime import datetime, timezone

src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_server_weather.schema import WeatherRequest, AHPRequest, WeatherDataResponse, AHPResultResponse, RankDaysRequest, RankDaysResponse

load_dotenv()
# Read and normalize the OpenWeather key: treat missing or whitespace-only as empty
OPENWEATHER_API_KEY = (os.getenv("OPENWEATHER_API_KEY") or "").strip()

app = Server("mcp-server-weather")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_weather_forecast",
            description="Отримання прогнозу погоди на кілька днів для заданої локації через OpenWeatherMap.",
            inputSchema=WeatherRequest.model_json_schema()
        ),
        Tool(
            name="calculate_ahp_weights",
            description="Розрахунок ваг критеріїв за методом AHP (Analytic Hierarchy Process) на основі важливості факторів погоди.",
            inputSchema=AHPRequest.model_json_schema()
        ),
        Tool(
            name="rank_days_ahp",
            description="Ранжування днів прогнозу за допомогою ваг AHP.",
            inputSchema=RankDaysRequest.model_json_schema()
        )
    ]

def format_date(dt_unix: int) -> str:
    return datetime.fromtimestamp(dt_unix, tz=timezone.utc).strftime('%Y-%m-%d')

def aggregate_forecast_by_day(forecast_list, max_days):
    days = {}
    for item in forecast_list:
        date = format_date(item["dt"])
        if date not in days:
            days[date] = {
                "temps": [],
                "rain": 0.0,
                "wind": [],
                "descriptions": {}
            }

        main = item.get("main", {})
        wind = item.get("wind", {})
        weather = item.get("weather", [])

        if "temp" in main:
            days[date]["temps"].append(main["temp"])

        if "rain" in item and "3h" in item["rain"]:
            days[date]["rain"] += item["rain"]["3h"]

        if "speed" in wind:
            days[date]["wind"].append(wind["speed"])

        if weather:
            desc = weather[0].get("description")
            if desc:
                days[date]["descriptions"][desc] = (
                    days[date]["descriptions"].get(desc, 0) + 1
                )

        if len(days) >= max_days:
            break

    result = []
    for date, v in days.items():
        result.append({
            "date": date,
            "temperature": round(sum(v["temps"]) / len(v["temps"]), 2) if v["temps"] else None,
            "rain_mm": round(v["rain"], 2),
            "wind_m_s": max(v["wind"]) if v["wind"] else None,
            "description": max(v["descriptions"], key=v["descriptions"].get) if v["descriptions"] else None
        })

    return result


ALLOWED_FACTORS = {"rain", "wind", "temperature", "sun", "fog", "snow"}
ratio_map = {"high": 5, "medium": 3, "low": 1}

def build_pairwise_matrix(criteria: list[dict]) -> np.ndarray:
    n = len(criteria)
    M = np.ones((n, n), dtype=float)
    imp = [ratio_map.get(c["importance"], 3) for c in criteria]
    for i in range(n):
        for j in range(n):
            if i != j:
                M[i, j] = imp[i] / imp[j]
    return M

def compute_ahp_weights(criteria: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    M = build_pairwise_matrix(criteria)
    vals, vecs = np.linalg.eig(M)
    k = int(np.argmax(vals.real))
    w = np.abs(vecs[:, k].real)
    w = w / w.sum()
    return M, w

def compute_consistency_ratio(M: np.ndarray, w: np.ndarray) -> dict:
    n = M.shape[0]
    RI = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}.get(n, 1.49)
    Aw = M @ w
    lam = float(np.mean(Aw / w))
    CI = (lam - n) / (n - 1) if n > 1 else 0.0
    CR = CI / RI if RI != 0 else 0.0
    return {
        "lambda_max": round(lam, 4),
        "CI": round(CI, 4),
        "CR": round(CR, 4),
        "is_consistent": CR < 0.1
    }

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_weather_forecast":
        try:
            request = WeatherRequest(**arguments)
        except ValidationError as e:
            return [TextContent(type="text", text=f"Помилка валідації: {str(e)}")]

        if request.lon is None or request.lat is None:
            location = request.location or "(невідома локація)"
            response_text = (
                f"Немає координат для {location}.\n"
                "Щоб отримати реальний прогноз, передай поля `lon` і `lat` або інтегруй цей тул з `mcp_server_map`."
            )
            return [TextContent(type="text", text=response_text)]

        if not OPENWEATHER_API_KEY:
            return [TextContent(type="text", text="OPENWEATHER_API_KEY не знайдено або порожній у середовищі (.env). Неможливо зробити запит до OpenWeatherMap.")]

        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": request.lat,
            "lon": request.lon,
            "units": request.units or "metric",
            "appid": OPENWEATHER_API_KEY,
            "lang": "uk",
        }

        try:
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None,
                functools.partial(requests.get, url, params=params, timeout=10)
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            return [TextContent(type="text", text=f"Помилка при запиті до OpenWeatherMap: {e}")]    
        forecast_list = data.get("list", [])
        result_points = aggregate_forecast_by_day(forecast_list, request.days)

        result_obj = {
            "location": request.location or f"{request.lat},{request.lon}",
            "days": len(result_points),
            "data": result_points,
            "source": "OpenWeatherMap (forecast)",
        }
        return [TextContent(type="text", text=json.dumps(result_obj, ensure_ascii=False, indent=2))]

      
    elif name == "calculate_ahp_weights":
        try:
            request = AHPRequest(**arguments)
        except ValidationError as e:
            return [TextContent(type="text", text=f"Помилка валідації: {str(e)}")]

        criteria = request.criteria
        if not criteria:
            return [TextContent(type="text", text="Немає критеріїв для AHP")]

        canon = []
        seen = set()
        for c in criteria:
            f = str(c.factor).lower().strip()
            if f not in ALLOWED_FACTORS or f in seen:
                continue
            seen.add(f)
            r = str(c.relation).lower().strip()
            if r not in {"prefer", "avoid", "neutral"}:
                r = "neutral"
            imp = str(c.importance).lower().strip()
            if imp not in ratio_map:
                imp = "medium"
            canon.append({"factor": f, "relation": r, "importance": imp})

        if not canon:
            return [TextContent(type="text", text="Не вдалося отримати валідні критерії")]

        M, w_vec = compute_ahp_weights(canon)
        consistency = compute_consistency_ratio(M, w_vec)
        labels = [c["factor"] for c in canon]
        weights = {labels[i]: round(float(w_vec[i]), 4) for i in range(len(labels))}

        response_text = f"""# Розрахунок ваг AHP

## Критерії
"""
        for c in canon:
            response_text += f"- {c['factor']} ({c['relation']}, важливість: {c['importance']})\n"

        response_text += f"\n## Ваги факторів\n"
        for f, wg in weights.items():
            response_text += f"- {f}: {wg:.4f}\n"

        response_text += f"\n## Консистентність\n"
        response_text += f"- λ_max: {consistency['lambda_max']}\n"
        response_text += f"- CI: {consistency['CI']}\n"
        response_text += f"- CR: {consistency['CR']}\n"
        response_text += f"- Консистентність: {'Так' if consistency['is_consistent'] else 'Ні (CR ≥ 0.1)'}\n"

        response_text += "\n---\n*Метод AHP (Analytic Hierarchy Process) для багатокритеріального вибору днів за погодою*"

        return [TextContent(type="text", text=response_text)]

    elif name == "rank_days_ahp":
        try:
            request = RankDaysRequest(**arguments)
        except ValidationError as e:
            return [TextContent(type="text", text=f"Помилка валідації: {str(e)}")]

        canon = []
        seen = set()
        for c in request.criteria:
            f = str(c.factor).lower().strip()
            if f not in ALLOWED_FACTORS or f in seen: continue
            seen.add(f)
            r = str(c.relation).lower().strip()
            imp = str(c.importance).lower().strip()
            canon.append({"factor": f, "relation": r, "importance": imp})

        if not canon:
            return [TextContent(type="text", text="Немає валідних критеріїв")]

        M, w_vec = compute_ahp_weights(canon)
        labels = [c["factor"] for c in canon]
        weights = {labels[i]: float(w_vec[i]) for i in range(len(labels))}

        scored_days = []
        for day_point in request.forecast_data:
            total_score = 0
            
            for c in canon:
                factor = c["factor"]
                weight = weights.get(factor, 0)
                
                val = None
                if factor == "rain": val = day_point.rain_mm
                elif factor == "wind": val = day_point.wind_m_s
                elif factor == "temperature": val = day_point.temperature
                
                if val is None: val = 0
                
                score = 0
                if factor == "rain":
                    score = max(0, 1 - (val / 10.0))
                elif factor == "wind":
                    score = max(0, 1 - (val / 25.0))
                elif factor == "temperature":
                    score = max(0, 1 - (abs(20 - val) / 30.0))
                
                total_score += score * weight
            
            scored_days.append({
                "score": round(total_score, 4),
                "day": day_point.model_dump()
            })
        
        scored_days.sort(key=lambda x: x["score"], reverse=True)
        
        result = {
            "best_day": scored_days[0]["day"],
            "scored_days": scored_days
        }
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())