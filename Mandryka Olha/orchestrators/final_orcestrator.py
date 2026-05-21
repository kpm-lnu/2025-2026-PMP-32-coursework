import asyncio
import json
import logging
import sys
import re
import os
import subprocess
from datetime import date as date_cls
from pathlib import Path
from enum import Enum, auto
from typing import Any, Dict, List, Optional

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from llm.groq_client import GroqClient
from llm.config import CHAT_MODEL
from short_term_memory.short_term import ShortTermMemory
from mcp_infra.client_n import MCPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class FSMState(Enum):
    IDLE = auto()
    PARSE_INTENT = auto()
    VALIDATE_PARAMS = auto()
    EXECUTE_DAG = auto()
    FOLLOWUP_ANSWER = auto()
    SAVE_TURN = auto()
    FINALIZE = auto()


class HybridOrchestrator:
    def __init__(self, model_name: str = CHAT_MODEL):
        self.llm = GroqClient(model_name=model_name)
        self.memory = ShortTermMemory(capacity=10)
        self.mcp = MCPClient()
        self.state = FSMState.IDLE
        self.context: Dict[str, Any] = {
            "query": "",
            "intent": "general",
            "params": {},
            "missing_params": [],
            "results": {},
            "final_answer": ""
        }

    async def initialize(self):
        logger.info("[*] Initializing Hybrid Orchestrator — EAGER MCP connect...")
        await self.mcp.connect_all()

        connected = list(self.mcp.sessions.keys())
        failed = [s for s in self.mcp.server_configs if s not in self.mcp.sessions]

        logger.info(f"[*] Connected servers ({len(connected)}): {connected}")
        if failed:
            logger.warning(f"[!] Failed to connect ({len(failed)}): {failed}")

        if "mcp-server-rag" not in self.mcp.sessions:
            await self.mcp.disconnect_all()
            raise RuntimeError(
                "mcp-server-rag не підключено. Оркестратор не може працювати без бази знань.\n"
                "Перевірте конфігурацію в mcp_infra/client_n.py та наявність vector_store."
            )

    async def process_query(self, query: str) -> str:
        self.context["query"] = query
        self.context["final_answer"] = ""


        self.state = FSMState.PARSE_INTENT

        while self.state != FSMState.FINALIZE:
            logger.info(f"[FSM] Transitioning to state: {self.state.name}")

            if self.state == FSMState.PARSE_INTENT:
                await self._parse_intent()
            elif self.state == FSMState.VALIDATE_PARAMS:
                await self._validate_params()
            elif self.state == FSMState.EXECUTE_DAG:
                self.context["results"] = {}
                await self._execute_dag()
            elif self.state == FSMState.FOLLOWUP_ANSWER:
                await self._answer_followup()
            elif self.state == FSMState.SAVE_TURN:
                await self._save_turn()
            else:
                self.state = FSMState.FINALIZE

        return self.context.get("final_answer", "сталася помилка під час обробки запиту.")

    def _is_query_relevant_to_routes(self, query: str) -> bool:
        keywords = ["Карпати", "гори", "маршрут", "похід", "вершина"]
        return any(keyword.lower() in query.lower() for keyword in keywords)

    def _has_prior_context(self) -> bool:
        return bool(self.context.get("results")) or bool(self.memory.to_messages())

    async def _parse_intent(self):
        history = self.memory.to_messages()
        has_prev_route = bool(self.context.get("results"))
        prompt = f"""Аналізуй запит користувача та історію діалогу. Визнач intent.

Запит: {self.context['query']}
Історія: {json.dumps(history, ensure_ascii=False)}
Чи є попередні результати маршруту в пам'яті: {has_prev_route}

Правила визначення intent:
- "route_planning" — ТІЛЬКИ якщо запитується НОВИЙ маршрут/вершина (вперше або інша вершина) І запит стосується гір в Україні.
- "followup" — уточнення/питання до вже обговореного маршруту (погода, безпека, деталі, дата, час, км, порада)
- "calendar" — запит додати подію в календар
- "general" — загальне питання що не стосується маршруту
- інші наміри, не пов'язані з горами або маршрутами,  НЕ ВИКОНУЙ ПЛАНУВАННЯ МАРШРУТУ

Поверни ТІЛЬКИ валідний JSON об'єкт, без жодного тексту поза ним.
{{
  "intent": "route_planning",
  "params": {{
    "location": "назва місця або null",
    "route_name": "назва вершини/маршруту або null",
    "date": "YYYY-MM-DD або null"
  }},
  "missing_params": []
}}
"""
        response = await self.llm.generate([{"role": "user", "content": prompt}])
        try:
            raw = response.content if hasattr(response, "content") else str(response)
            content = raw.strip()
            logger.info(f"[PARSE_INTENT] LLM response: {content[:300]}")

            json_match = re.search(r"(\{.*\})", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                depth, json_end = 0, 0
                for i, char in enumerate(json_str):
                    if char == '{': depth += 1
                    elif char == '}': depth -= 1
                    if depth == 0 and i > 0:
                        json_end = i + 1
                        break
                if json_end > 0:
                    json_str = json_str[:json_end]
                data = json.loads(json_str)
            else:
                data = {}

            if data.get("intent") == "route_planning":
                location = data.get("params", {}).get("location")
                if location and not self._is_within_ukrainian_mountains(location):
                    data["intent"] = "general"

            self.context["intent"] = data.get("intent", "general")
            self.context["params"] = data.get("params", {})
            self.context["missing_params"] = data.get("missing_params", [])
            logger.info(f"[PARSE_INTENT] intent={self.context['intent']}, "
                        f"params={self.context['params']}")
            self.state = FSMState.VALIDATE_PARAMS

        except Exception as e:
            logger.error(f"[PARSE_INTENT] Error: {e}")
            self.context["intent"] = "route_planning"
            self.context["params"] = {"route_name": self.context["query"]}
            self.context["missing_params"] = []
            self.state = FSMState.VALIDATE_PARAMS

    def _is_within_ukrainian_mountains(self, location: str) -> bool:
        if not location:
            return False
        keywords = ["Карпати", "гори", "Україна"]
        return any(keyword.lower() in location.lower() for keyword in keywords)

    async def _validate_params(self):
        if self.context.get("missing_params"):
            logger.info(f"[!] Missing params: {self.context['missing_params']}")

        intent = self.context.get("intent", "route_planning")
        if intent in ("followup", "general"):
            if self.context.get("results") or self.memory.to_messages():
                logger.info(f"[FSM] intent='{intent}' → FOLLOWUP_ANSWER (no DAG re-run)")
                self.state = FSMState.FOLLOWUP_ANSWER
                return
        if intent == "calendar":
            logger.info("[FSM] intent='calendar' → calling _calendar_prompt inline")
            await self._calendar_prompt()
            self.state = FSMState.SAVE_TURN
            return
        self.state = FSMState.EXECUTE_DAG

    async def _execute_dag(self):

        logger.info("[*] Executing Hybrid FSM+DAG...")

        params = self.context["params"]
        query_location = (
            params.get("route_name")
            or params.get("location")
            or self.context["query"]
        )
        geo_location = self._clean_geo_name(
            params.get("location")
            or params.get("route_name")
            or self.context["query"]
        )
        if not params.get("route_name"):
            params["route_name"] = query_location
        logger.info(f"  [DAG] Query location: '{query_location}', Geo location: '{geo_location}'")

        logger.info("  [DAG] Step 1: RAG search + Geocoding (parallel)...")
        tasks_1, names_1 = [], []

        if "mcp-server-rag" in self.mcp.sessions:
            tasks_1.append(self.mcp.call_tool(
                "mcp-server-rag", "rag_search",
                {"query": query_location, "k": 8}
            ))
            names_1.append("rag_search")
        else:
            logger.warning("  mcp-server-rag not connected")
            self.context["results"]["rag"] = "RAG не підключено."

        if "mcp-server-map" in self.mcp.sessions:
            tasks_1.append(self.mcp.call_tool(
                "mcp-server-map", "geocode_location",
                {
                    "query": geo_location,
                    "limit": 5,
                    "preferBBox": [22.0, 47.5, 26.5, 49.5],
                    "preferNear": [24.5, 48.5],
                }
            ))
            names_1.append("geo")
        else:
            logger.warning("  mcp-server-map not connected")
            self.context["results"]["geo_raw"] = None

        if tasks_1:
            res_list = await asyncio.gather(*tasks_1, return_exceptions=True)
            for i, res in enumerate(res_list):
                name = names_1[i]
                if isinstance(res, Exception):
                    logger.error(f"  Step 1 error ({name}): {res}")
                    if name == "rag_search":
                        self.context["results"]["rag"] = "Помилка RAG."
                    elif name == "geo":
                        self.context["results"]["geo_raw"] = None
                    continue

                logger.info(f"  [{name.upper()}] raw: {str(res)[:200]}")

                if name == "rag_search":
                    raw_text = self._extract_text_result(res)
                    self.context["results"]["rag"] = raw_text
                    self.context["results"]["rag_tool_used"] = "rag_search"
                    logger.info(f"  [RAG_SEARCH] text extracted: {raw_text[:200]}")

                    chunks = []
                    try:
                        rag_data = json.loads(raw_text)
                        chunks = rag_data.get("chunks", [])
                    except Exception:
                        pass

                    if not chunks and "mcp-server-rag" in self.mcp.sessions:
                        alt_queries = [
                            f"маршрут {query_location}",
                            f"підйом на {query_location} опис",
                            query_location,
                        ]
                        for alt_q in alt_queries:
                            if alt_q == query_location:
                                continue 
                            logger.info(f"  [RAG] Retry with alt query: '{alt_q}'")
                            try:
                                alt_res = await self.mcp.call_tool(
                                    "mcp-server-rag", "rag_search",
                                    {"query": alt_q, "k": 8}
                                )
                                alt_text = self._extract_text_result(alt_res)
                                alt_data = json.loads(alt_text)
                                alt_chunks = alt_data.get("chunks", [])
                                if alt_chunks:
                                    chunks = alt_chunks
                                    raw_text = alt_text
                                    self.context["results"]["rag"] = raw_text
                                    logger.info(f"  [RAG] Alt query '{alt_q}' found {len(alt_chunks)} chunks")
                                    break
                            except Exception as alt_err:
                                logger.warning(f"  [RAG] Alt query failed: {alt_err}")

                    if chunks:
                        self.context["results"]["rag_chunks_text"] = "\n\n---\n\n".join(
                            [f"Фрагмент {i+1}:\n{chunk}" for i, chunk in enumerate(chunks[:6])]
                        )
                        self.context["results"]["rag_readable"] = raw_text
                        try:
                            logger.info(f"  [RAG] Running rag_analyze on {len(chunks)} chunks...")
                            analyze_res = await self.mcp.call_tool(
                                "mcp-server-rag", "rag_analyze",
                                {
                                    "query": query_location,
                                    "chunks": chunks,
                                    "analysis_type": "routes",
                                    "preferences": []
                                }
                            )
                            analyze_text = self._extract_text_result(analyze_res)
                            self.context["results"]["rag_analyzed"] = analyze_text
                            self.context["results"]["rag_readable"] = analyze_text
                            logger.info(f"  [RAG_ANALYZE] done: {analyze_text[:150]}")
                        except Exception as analyze_err:
                            logger.warning(f"  [RAG_ANALYZE] skipped: {analyze_err}")
                    else:
                        logger.warning(f"  [RAG] No chunks found for '{query_location}' (embedding API may be down)")
                        self.context["results"]["rag_readable"] = (
                            f"RAG пошук не повернув результатів для '{query_location}'. "
                            f"Можливо, є проблеми з підключенням до Embedding API."
                        )

                elif name == "geo":
                    self.context["results"]["geo_raw"] = res

        coords = self._extract_coords(self.context["results"].get("geo_raw"))

        if coords is None and "mcp-server-map" in self.mcp.sessions:
            lat_query = self._transliterate_ua(geo_location)
            logger.info(f"  [COORDS] Cyrillic geocode failed, retrying with Latin: '{lat_query}'")
            try:
                lat_res = await self.mcp.call_tool(
                    "mcp-server-map", "geocode_location",
                    {
                        "query": lat_query,
                        "limit": 5,
                        "preferBBox": [22.0, 47.5, 26.5, 49.5],
                        "preferNear": [24.5, 48.5],
                    }
                )
                coords = self._extract_coords(lat_res)
                if coords:
                    self.context["results"]["geo_raw"] = lat_res
                    logger.info(f"  [COORDS] Latin fallback success: {coords}")
                else:
                    logger.warning(f"  [COORDS] Latin fallback also failed for '{lat_query}'")
            except Exception as geo_err:
                logger.error(f"  [COORDS] Latin fallback error: {geo_err}")

        if coords is None and "mcp-server-map" in self.mcp.sessions:
            rag_name = self._extract_primary_route_name_from_rag()
            if rag_name:
                logger.info(f"  [COORDS] Retry with RAG route name: '{rag_name}'")
                for rq in (rag_name, self._transliterate_ua(rag_name)):
                    try:
                        rag_geo = await self.mcp.call_tool(
                            "mcp-server-map", "geocode_location",
                            {
                                "query": rq,
                                "limit": 5,
                                "preferBBox": [22.0, 47.5, 26.5, 49.5],
                                "preferNear": [24.5, 48.5],
                            }
                        )
                        coords = self._extract_coords(rag_geo)
                        if coords:
                            self.context["results"]["geo_raw"] = rag_geo
                            self.context["params"]["route_name"] = rag_name
                            logger.info(f"  [COORDS] RAG-name geocode success: {coords}")
                            break
                    except Exception as rag_geo_err:
                        logger.warning(f"  [COORDS] RAG-name geocode failed for '{rq}': {rag_geo_err}")

        self.context["results"]["coords"] = coords
        logger.info(f"  [COORDS] extracted: {coords}")

        logger.info("  [DAG] Step 2: Weather+ANR + Navigation+HTML + Safety (parallel)...")
        tasks_2 = []

        if coords and coords.get("lat") and coords.get("lon"):
            if "mcp-server-weather" in self.mcp.sessions:
                tasks_2.append(self._run_weather_with_anr(coords))
            else:
                logger.warning("  mcp-server-weather not available")
                self.context["results"]["weather"] = "Погода недоступна."
                self.context["results"]["best_day"] = None
        else:
            logger.warning(f"  No coords for weather: {coords}")
            self.context["results"]["weather"] = "Координати не визначено — прогноз недоступний."
            self.context["results"]["best_day"] = None

        if "mcp-server-navigation" in self.mcp.sessions:
            tasks_2.append(self._run_navigation_with_html(coords, query_location))
        else:
            logger.warning("  mcp-server-navigation not available")
            self.context["results"]["navigation"] = "Навігація недоступна."
            self.context["results"]["route_html_path"] = None

        if "mcp-server-rag" in self.mcp.sessions:
            tasks_2.append(self._run_safety_search(query_location))
        else:
            self.context["results"]["safety"] = ""

        if tasks_2:
            await asyncio.gather(*tasks_2)

        logger.info(f"  [DAG] Final results: { {k: str(v)[:80] for k, v in self.context['results'].items()} }")

        await self._generate_final_answer()
        await self._calendar_prompt()
        self.state = FSMState.SAVE_TURN

    async def _calendar_prompt(self):
        """MCP-крок: Створення .ics події з автовідкриттям у системному календарі."""
        logger.info("[*] FSM: Calendar prompt...")

   
        if self.context.get("intent") != "calendar":
            logger.info("[*] Calendar skipped: intent is not 'calendar'.")
            return

        if "mcp-server-calendar" in self.mcp.sessions:
            best_day = self.context["results"].get("best_day")
            event_date = (
                best_day
                or self.context["params"].get("date")
                or "2026-06-01"
            )

            route_name = (
                self.context["params"].get("route_name")
                or self.context["params"].get("location")
                or self.context.get("query", "Карпати")
            )
            safe_route = re.sub(r"[^A-Za-z0-9_\-А-Яа-яІіЇїЄєҐґ]", "_", str(route_name))
            ics_filename = f"hike_{safe_route}_{event_date}.ics"
            ics_path = (Path.cwd() / ics_filename).resolve()
            ics_uri = ics_path.as_uri()

            cal_args = {
                "title": f"Похід: {route_name}",
                "description": (
                    f"Маршрут: {self.context['results'].get('rag', '')[:300]}\n"
                    f"Запит: {self.context['query']}"
                ),
                "date": event_date,
                "location": self.context["params"].get("location") or route_name,
                "filename": str(ics_path)
            }

            try:
                logger.info(f"[*] Creating .ics: '{cal_args['title']}' on {event_date}")
                await self.mcp.call_tool("mcp-server-calendar", "create_ical_event", cal_args)

                suffix = f"\n\nПодія **'{route_name}'** додана до календаря на **{event_date}**."

                if ics_path.exists():
                    self.context.setdefault("results", {})["calendar_ics_path"] = str(ics_path)
                    try:
                        if sys.platform == "win32":
                            try:
                                os.startfile(str(ics_path))
                            except Exception:
                                subprocess.Popen(["cmd", "/c", "start", "", str(ics_path)], shell=False)
                        elif sys.platform == "darwin":
                            subprocess.Popen(["open", str(ics_path)])
                        else:
                            subprocess.Popen(["xdg-open", str(ics_path)])
                        suffix += f"\nФайл відкрито для імпорту: [{ics_path.name}]({ics_uri})"
                        logger.info(f"[*] .ics opened: {ics_path}")
                    except Exception as open_err:
                        suffix += f"\nФайл збережено: [{ics_path.name}]({ics_uri})"
                        logger.warning(f"  Could not auto-open .ics: {open_err}")
                else:
                    suffix += f"\nФайл не знайдено після створення: [{ics_path.name}]({ics_uri})"

                self.context["final_answer"] += suffix

            except Exception as e:
                logger.error(f"Calendar error: {e}")

    async def _answer_followup(self):
        logger.info("[*] FSM: FOLLOWUP_ANSWER (using existing context)...")
        results = self.context.get("results", {})
        history = self.memory.to_messages()

        ctx_parts = []
        if results.get("rag_analyzed"):
            ctx_parts.append(f"Маршрут (аналіз):\n{results['rag_analyzed'][:1500]}")
        elif results.get("rag_chunks_text"):
            ctx_parts.append(f"Маршрут:\n{results['rag_chunks_text'][:1500]}")
        if results.get("weather"):
            ctx_parts.append(f"Погода:\n{str(results['weather'])[:600]}")
        if results.get("weather_anr"):
            ctx_parts.append(f"AHP-ранжування днів:\n{str(results['weather_anr'])[:600]}")
        if results.get("best_day"):
            ctx_parts.append(f"Найкращий день: {results['best_day']}")
        if results.get("navigation"):
            nav = str(results['navigation'])
            ctx_parts.append(f"Навігація:\n{nav[:400]}")
        if results.get("safety"):
            ctx_parts.append(f"Безпека:\n{str(results['safety'])[:600]}")
        if results.get("route_html_path"):
            ctx_parts.append(f"HTML-карта: {results['route_html_path']}")

        context_block = "\n\n".join(ctx_parts) if ctx_parts else "Попередній контекст відсутній."

        prompt = (
            f"Відповідай ТІЛЬКИ на конкретне питання користувача. "
            f"НЕ переповідай весь маршрут заново.\n\n"
            f"Питання: {self.context['query']}\n\n"
            f"Наявний контекст маршруту:\n{context_block}\n\n"
            f"Відповідь українською мовою, стисло і по суті."
        )
        messages = list(history) + [{"role": "user", "content": prompt}]
        try:
            resp = await self.llm.generate(messages)
            self.context["final_answer"] = resp.content if hasattr(resp, "content") else str(resp)
        except Exception as e:
            logger.error(f"[FOLLOWUP] LLM error: {e}")
            self.context["final_answer"] = f"Помилка: {e}"
        self.state = FSMState.SAVE_TURN

    async def _save_turn(self):
        self.memory.add_user(self.context["query"])
        self.memory.add_assistant(self.context.get("final_answer", ""))
        logger.info("[*] FSM: Saved to short-term memory.")
        self.state = FSMState.FINALIZE

    async def _run_weather_with_anr(self, coords: Dict[str, float]):
       
        lat, lon = coords["lat"], coords["lon"]
        today = date_cls.today().isoformat()  

        try:
            weather_res = await self.mcp.call_tool(
                "mcp-server-weather", "get_weather_forecast",
                {"lat": lat, "lon": lon, "days": 3, "start_date": today}
            )
            self.context["results"]["weather"] = self._extract_text_result(weather_res)
            logger.info(f"  [WEATHER] forecast ok (start={today}, days=3): {self.context['results']['weather'][:150]}")
        except Exception as e:
            logger.error(f"  [WEATHER] forecast error: {e}")
            self.context["results"]["weather"] = f"Помилка прогнозу: {e}"
            self.context["results"]["best_day"] = None
            return

        weather_tools = [t.name for t in self.mcp.available_tools.get("mcp-server-weather", [])]
        logger.info(f"  [WEATHER] available tools: {weather_tools}")

        try:
            w_data = json.loads(self.context["results"]["weather"])
            forecast_points = w_data.get("data", [])
        except Exception:
            forecast_points = []
        logger.info(f"  [AHP] forecast points for ranking: {len(forecast_points)}")

        if "rank_days_ahp" in weather_tools and forecast_points:
            try:
                
                query_lower = self.context["query"].lower()
                if any(w in query_lower for w in ["безпечн", "safe"]):
                    criteria = [
                        {"factor": "rain",        "relation": "avoid", "importance": "critical"},
                        {"factor": "wind",        "relation": "avoid", "importance": "high"},
                        {"factor": "temperature", "relation": "neutral", "importance": "medium"},
                    ]
                elif any(w in query_lower for w in ["легк", "easy", "простий"]):
                    criteria = [
                        {"factor": "rain",        "relation": "avoid",   "importance": "high"},
                        {"factor": "wind",        "relation": "avoid",   "importance": "medium"},
                        {"factor": "temperature", "relation": "neutral", "importance": "low"},
                    ]
                else:
                    criteria = [
                        {"factor": "rain",        "relation": "avoid",   "importance": "high"},
                        {"factor": "wind",        "relation": "avoid",   "importance": "medium"},
                        {"factor": "temperature", "relation": "neutral", "importance": "low"},
                    ]

                logger.info(f"  [AHP] criteria based on query '{self.context['query']}': {criteria}")

                anr_res = await self.mcp.call_tool(
                    "mcp-server-weather", "rank_days_ahp",
                    {
                        "forecast_data": forecast_points,
                        "criteria": criteria
                    }
                )
                anr_text = self._extract_text_result(anr_res)
                logger.info(f"  [AHP] rank_days_ahp result: {anr_text[:300]}")

                try:
                    anr_data = json.loads(anr_text)
                    best_day_obj = anr_data.get("best_day") or (
                        anr_data.get("ranked_days", [{}])[0] if anr_data.get("ranked_days") else {}
                    )
                    best_date = (
                        best_day_obj.get("date")
                        or self._extract_best_day_date(anr_text)
                    )
                except Exception:
                    best_date = self._extract_best_day_date(anr_text)

                self.context["results"]["best_day"] = best_date
                self.context["results"]["weather_anr"] = anr_text
                logger.info(f"  [AHP] best day: {best_date}")

            except Exception as e:
                logger.error(f"  [AHP] rank_days_ahp error: {e}")
                self.context["results"]["best_day"] = None
                self.context["results"]["weather_anr"] = None
        else:
            if "rank_days_ahp" not in weather_tools:
                logger.warning(f"  [AHP] rank_days_ahp not found (available: {weather_tools})")
            else:
                logger.warning("  [AHP] No forecast points to rank")
            self.context["results"]["best_day"] = None
            self.context["results"]["weather_anr"] = None

    async def _run_navigation_with_html(self, coords: Optional[Dict[str, float]], query_location: str):
     
        if coords and coords.get("lat") and coords.get("lon"):
            end_point = [coords["lon"], coords["lat"]]
        else:
            logger.warning("  [NAV] No end coordinates, skipping navigation.")
            self.context["results"]["navigation"] = "Координати кінцевої точки не визначено."
            self.context["results"]["route_html_path"] = None
            return

        rag_points = await self._extract_nav_points_from_rag(query_location)
        if not rag_points:
            rag_points = self._extract_nav_points_heuristic()
        logger.info(f"  [NAV] RAG points from LLM: {rag_points}")

        start_name: Optional[str] = rag_points.get("start_point_name")
        end_name_hint: Optional[str] = rag_points.get("end_point_name") or self._extract_primary_route_name_from_rag()
        intermediate_names: List[str] = rag_points.get("intermediate_points", [])[:3]

        banned_fragments = (
            "ліс", "хреб", "середин", "маршрут", "етап", "стеж", "поворот",
            "підйом", "спуск", "почат", "кінец", "вершина", "гора", "урочище"
        )
        cleaned_waypoint_names: List[str] = []
        seen_wp = set()
        for nm in intermediate_names:
            s = self._clean_geo_name(str(nm or "")).strip(" .,")
            if len(s) < 3:
                continue
            low = s.lower()
            if any(b in low for b in banned_fragments):
                continue
            if low in seen_wp:
                continue
            seen_wp.add(low)
            cleaned_waypoint_names.append(s)
        intermediate_names = cleaned_waypoint_names[:3]

        async def geocode_ua(name: str, role: str = "") -> Optional[Dict[str, float]]:
         
            clean_name = self._clean_geo_name(name)
            lat_name = self._transliterate_ua(clean_name)
            candidates = [
                clean_name,
                lat_name,
                f"{lat_name} Ukraine",
                f"{clean_name} Карпати",
                f"{clean_name} Україна",
                name,
            ]
            seen = set()
            candidates = [c for c in candidates if not (c in seen or seen.add(c))]

            geo_base_args = {
                "limit": 5,
                "preferBBox": [22.0, 47.5, 26.5, 49.5],
                "preferNear": [24.5, 48.5],
            }

            for query in candidates:
                try:
                    res = await self.mcp.call_tool(
                        "mcp-server-map", "geocode_location",
                        {"query": query, **geo_base_args}
                    )
                    raw = self._extract_text_result(res)
                    data = json.loads(raw)
                    results_list = data.get("results", data.get("items", []))
                    if not results_list:
                        logger.warning(f"  [GEO/{role}] '{query}' → 0 results")
                        continue
                    for item in results_list:
                        lat = item.get("lat") or item.get("latitude")
                        lon = item.get("lon") or item.get("longitude")
                        if lat is None or lon is None:
                            continue
                        lat, lon = float(lat), float(lon)
                        country = item.get("countryIso", "").upper()
                        in_ukraine = (
                            country == "UA"
                            or (44.0 <= lat <= 52.5 and 22.0 <= lon <= 40.5)
                        )
                        if in_ukraine:
                            logger.info(f"  [GEO/{role}] '{name}' → lat={lat}, lon={lon} (q='{query}', iso='{country}')")
                            return {"lat": lat, "lon": lon}
                    logger.warning(f"  [GEO/{role}] '{query}' — no UA result ({len(results_list)} items)")
                except Exception as e:
                    logger.warning(f"  [GEO/{role}] '{query}' error: {e}")
            return None

        start_point: Optional[List[float]] = None
        start_label = "Старт"

        # If RAG didn't provide an explicit start but provided intermediate points,
        # use the first intermediate as a fallback start. This helps when RAG outputs
        # a linear description without marking the start explicitly.
        if not start_name and intermediate_names:
            fallback_start = intermediate_names.pop(0)
            logger.info(f"  [NAV] No explicit start from RAG — falling back to first intermediate: '{fallback_start}'")
            start_name = fallback_start

        if start_name and "mcp-server-map" in self.mcp.sessions:
            sc = await geocode_ua(start_name, role="START")
            if sc:
                start_point = [sc["lon"], sc["lat"]]
                start_label = start_name
            else:
                logger.warning(f"  [NAV] Could not geocode start '{start_name}' to UA coords")

        if start_point is None:
            logger.warning(f"  [NAV] Start point unresolved (start_name={start_name!r}); skipping route build")
            self.context["results"]["navigation"] = (
                "Стартову точку маршруту не вдалося визначити автоматично. "
                "Уточніть, будь ласка, населений пункт старту (наприклад: Ворохта/Дземброня/Заросляк)."
            )
            self.context["results"]["route_html_path"] = None
            return

        start_to_end_km = self._haversine_km(start_point[1], start_point[0], end_point[1], end_point[0])
        if start_to_end_km > 180 and end_name_hint and "mcp-server-map" in self.mcp.sessions:
            logger.warning(
                f"  [NAV] End point outlier ({start_to_end_km:.1f}km from start). "
                f"Retry end geocode by hint '{end_name_hint}'"
            )
            alt_end = await geocode_ua(end_name_hint, role="END_HINT")
            if alt_end:
                alt_dist = self._haversine_km(start_point[1], start_point[0], alt_end["lat"], alt_end["lon"])
                if alt_dist < start_to_end_km:
                    end_point = [alt_end["lon"], alt_end["lat"]]
                    logger.info(f"  [NAV] End point replaced by hint '{end_name_hint}' ({alt_dist:.1f}km)")

        linear_km = self._haversine_km(start_point[1], start_point[0], end_point[1], end_point[0])
        max_waypoint_near_km = max(8.0, linear_km * 1.4)

        waypoints: List[List[float]] = []
        waypoint_labels: List[str] = []

        if intermediate_names and "mcp-server-map" in self.mcp.sessions:
            geo_results = await asyncio.gather(
                *[geocode_ua(name, role=f"WP{i}") for i, name in enumerate(intermediate_names)]
            )
            for name, wc in zip(intermediate_names, geo_results):
                if wc:
                    d_start = self._haversine_km(start_point[1], start_point[0], wc["lat"], wc["lon"])
                    d_end = self._haversine_km(end_point[1], end_point[0], wc["lat"], wc["lon"])
                    if min(d_start, d_end) > max_waypoint_near_km:
                        logger.warning(
                            f"  [NAV] Waypoint '{name}' skipped as outlier: "
                            f"d_start={d_start:.1f}km, d_end={d_end:.1f}km, threshold={max_waypoint_near_km:.1f}km"
                        )
                        continue
                    waypoints.append([wc["lon"], wc["lat"]])
                    waypoint_labels.append(name)
                else:
                    logger.warning(f"  [NAV] Waypoint '{name}' skipped — no UA coords")

        # Validate all collected points (start, waypoints, end): if any point is outside
        # the Carpathian bbox, try re-geocoding that place name biased toward the main
        # cluster (end_point or centroid of existing waypoints). This avoids keeping
        # popular but distant localities with the same name.
        def in_carpath(lat: float, lon: float) -> bool:
            return 47.5 <= lat <= 49.5 and 22.0 <= lon <= 25.5

        # compute a preferred center: prefer end_point if present, otherwise centroid of waypoints
        preferred_center = None
        try:
            if end_point and isinstance(end_point, list) and len(end_point) == 2:
                preferred_center = [end_point[0], end_point[1]]
            elif waypoints:
                avg_lon = sum(wp[0] for wp in waypoints) / len(waypoints)
                avg_lat = sum(wp[1] for wp in waypoints) / len(waypoints)
                preferred_center = [avg_lon, avg_lat]
        except Exception:
            preferred_center = None

        # Re-check start
        try:
            if start_point and not in_carpath(start_point[1], start_point[0]) and start_name:
                logger.warning(f"  [NAV] Start '{start_name}' appears outside Carpathians; trying biased geocode")
                sc_near = await geocode_ua(start_name, role="START_RETRY", prefer_center=preferred_center)
                if sc_near:
                    logger.info(f"  [NAV] Start '{start_name}' replaced by nearby candidate: {sc_near['lat']},{sc_near['lon']}")
                    start_point = [sc_near["lon"], sc_near["lat"]]
        except Exception as e:
            logger.debug(f"  [NAV] Start re-geocode error: {e}")

        # Re-check each waypoint
        for idx, (label, wp) in enumerate(list(zip(waypoint_labels, waypoints))):
            try:
                if not in_carpath(wp[1], wp[0]):
                    logger.warning(f"  [NAV] Waypoint '{label}' at {wp[1]},{wp[0]} outside Carpathians; trying biased geocode")
                    replacement = await geocode_ua(label, role=f"WP_RETRY_{idx}", prefer_center=preferred_center)
                    if replacement:
                        logger.info(f"  [NAV] Waypoint '{label}' replaced by nearby candidate: {replacement['lat']},{replacement['lon']}")
                        waypoints[idx] = [replacement["lon"], replacement["lat"]]
            except Exception as e:
                logger.debug(f"  [NAV] Waypoint re-geocode error for '{label}': {e}")

        # Re-check end (in case it was selected from ambiguous results earlier)
        try:
            if end_point and not in_carpath(end_point[1], end_point[0]):
                logger.warning(f"  [NAV] End point appears outside Carpathians; trying biased geocode for '{query_location}'")
                end_repl = await geocode_ua(query_location, role="END_RETRY", prefer_center=preferred_center)
                if end_repl:
                    logger.info(f"  [NAV] End replaced by nearby candidate: {end_repl['lat']},{end_repl['lon']}")
                    end_point = [end_repl["lon"], end_repl["lat"]]
        except Exception as e:
            logger.debug(f"  [NAV] End re-geocode error: {e}")

        logger.info(
            f"  [NAV] Route: start={start_point} ({start_label}) "
            f"-> waypoints={waypoints} -> end={end_point} ({query_location})"
        )

        nav_args: Dict[str, Any] = {
            "start": start_point,
            "end": end_point,
            "routeType": "foot_hiking",
            "lang": "uk"
        }
        if waypoints:
            nav_args["waypoints"] = waypoints

        try:
            nav_res = await self.mcp.call_tool("mcp-server-navigation", "plan_route", nav_args)
            nav_text = self._extract_text_result(nav_res)
            logger.info(f"  [NAV] plan_route ok: {nav_text[:200]}")
            try:
                route_data = json.loads(nav_text)
            except Exception:
                route_data = {}

            route_len_km = float(route_data.get("length", 0) or 0) / 1000.0
            suspicious_route = (
                bool(waypoints)
                and linear_km > 0.5
                and (
                    bool(route_data.get("validation_warning"))
                    or route_len_km > linear_km * 4.0
                )
            )
            if suspicious_route:
                logger.warning(
                    f"  [NAV] suspicious route with waypoints (len={route_len_km:.1f}km, "
                    f"linear={linear_km:.1f}km) -> retry without waypoints"
                )
                nav_args_no_wp: Dict[str, Any] = {
                    "start": start_point,
                    "end": end_point,
                    "routeType": "foot_hiking",
                    "lang": "uk"
                }
                nav_res = await self.mcp.call_tool("mcp-server-navigation", "plan_route", nav_args_no_wp)
                nav_text = self._extract_text_result(nav_res)
                try:
                    route_data = json.loads(nav_text)
                except Exception:
                    route_data = {}
                waypoints = []
                waypoint_labels = []

            self.context["results"]["navigation"] = nav_text
            self.context["results"]["route_data"] = route_data
        except Exception as e:
            logger.error(f"  [NAV] plan_route error: {e}")
            self.context["results"]["navigation"] = f"Помилка побудови маршруту: {e}"
            self.context["results"]["route_html_path"] = None
            return

        nav_tools = [t.name for t in self.mcp.available_tools.get("mcp-server-navigation", [])]

        if "render_route_map" not in nav_tools or not route_data:
            logger.info(f"  [NAV] render_route_map not available (tools: {nav_tools})")
            self.context["results"]["route_html_path"] = None
            return

        route_name = self.context["params"].get("route_name", "route")
        safe_name = re.sub(r"[^\w\-]", "_", route_name)
        html_path = str(Path.cwd() / f"route_{safe_name}.html")

        marker_points = [{"lat": start_point[1], "lon": start_point[0], "label": f"🚩 {start_label}"}]
        for label, wp in zip(waypoint_labels, waypoints):
            marker_points.append({"lat": wp[1], "lon": wp[0], "label": f"📍 {label}"})
        marker_points.append({"lat": end_point[1], "lon": end_point[0], "label": f"🏁 {query_location}"})

        try:
            html_res = await self.mcp.call_tool(
                "mcp-server-navigation", "render_route_map",
                {"route_geometry": route_data, "output_path": html_path, "points": marker_points}
            )
            logger.info(f"  [NAV] render_route_map: {self._extract_text_result(html_res)}")
            self.context["results"]["route_html_path"] = html_path

            if Path(html_path).exists():
                try:
                    abs_path = str(Path(html_path).resolve())
                    logger.info(f"  [NAV] Opening HTML map: {abs_path}")
                    if sys.platform == "win32":
                        subprocess.Popen(["cmd", "/c", "start", "", abs_path], shell=False)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", abs_path])
                    else:
                        subprocess.Popen(["xdg-open", abs_path])
                    logger.info(f"  [NAV] HTML map opened: {abs_path}")
                except Exception as open_err:
                    logger.warning(f"  Could not auto-open HTML: {open_err}")
        except Exception as e:
            logger.error(f"  [NAV] render_route_map error: {e}")
            self.context["results"]["route_html_path"] = None


    async def _run_safety_search(self, query_location: str):
        try:
            safety_query = f"безпека похід гори {query_location} небезпеки спорядження перша допомога"
            res = await self.mcp.call_tool(
                "mcp-server-rag", "rag_safety_search",
                {"query": safety_query, "k": 5}
            )
            raw_text = self._extract_text_result(res)
            data = json.loads(raw_text)
            safety_chunks = data.get("safety_chunks", [])

            if safety_chunks:
                safety_text = self._compose_safety_section(safety_chunks)
                self.context["results"]["safety"] = safety_text
                logger.info(f"  [SAFETY] Found {len(safety_chunks)} safety recommendations")
            else:
                self.context["results"]["safety"] = ""
                logger.warning(f"  [SAFETY] No safety chunks found for '{query_location}'")

        except Exception as e:
            logger.error(f"  [SAFETY] Error: {e}")
            self.context["results"]["safety"] = ""


    async def _generate_final_answer(self):
        results = self.context["results"]

        rag_content = results.get("rag_readable") or results.get("rag", "Не знайдено")
        rag_analyzed = results.get("rag_analyzed", "")
        rag_tool = results.get("rag_tool_used", "rag_search")

        rag_chunks = results.get("rag_chunks_text", "")

        
        rag_section = ""
        if rag_chunks:
            rag_section += f"### Оригінальні описи маршрутів з бази знань:\n{rag_chunks[:1500]}\n\n"
        if rag_analyzed:
            rag_section += f"### Структурований аналіз маршрутів:\n{rag_analyzed[:900]}"
        if not rag_section:
            rag_section = f"### Дані з бази знань (`{rag_tool}`):\n{str(rag_content)[:1200]}"

        weather_section = self._compose_weather_section(results)
        anr_block = results.get("weather_anr")
        best_day = results.get("best_day")
        if anr_block:
            weather_section += f"\n\n### Найкращий день для походу (AHP-ранжування):\n{anr_block[:500]}"
        if best_day:
            weather_section = f"*Найкращий день для походу:** **{best_day}**\n\n{weather_section}"

        route_data = results.get("route_data")
        if isinstance(route_data, dict) and "length" in route_data:
            dist_km = route_data.get("length", 0) / 1000
            dur_h = route_data.get("duration", 0) / 3600
            nav_section = (
                f"Побудовано маршрут за допомогою MCP Navigation:\n"
                f"- Відстань: {dist_km:.2f} км\n"
                f"- Орієнтовний час руху: {dur_h:.1f} год\n"
                f"- Геометрія маршруту опрацьована успішно."
            )
        else:
            nav_section = results.get("navigation", "Маршрут не побудовано")
            if len(nav_section) > 500:
                nav_section = nav_section[:500] + "... [дані обрізано для економії токенів]"

        html_path = results.get("route_html_path")
        if html_path and Path(html_path).exists():
            nav_section += f"\n\nІнтерактивна HTML-карта збережена: `{html_path}`"

        safety_text = results.get("safety", "")
        safety_section = ""
        if safety_text:
            safety_section = (
                "\n\n4. Рекомендації безпеки (ризик -> дія):\n"
                f"{str(safety_text)[:1800]}"
            )

        prompt = f"""Склади вичерпну та корисну відповідь українською мовою на основі даних.
    ОБОВ'ЯЗКОВО включи ДЕТАЛЬНИЙ ОПИС маршруту, погоду, навігацію та РЕКОМЕНДАЦІЇ БЕЗПЕКИ.
    ВАЖЛИВО: не копіюй довгі цитати дослівно, узагальнюй по суті.
    ФОРМАТ: 4 розділи Markdown (Маршрут, Погода, Навігація, Безпека), по 3-5 коротких пунктів у кожному.
    У розділі Погода НЕ пиши вологість. Пиши тільки: температура, опади (дощ/сніг) за наявності, вітер, опис.
    У розділі Безпека дай обґрунтовані поради: "ризик -> дія" на основі наданого safety-тексту.
    Заверши відповідь логічним завершеним реченням.

Запит користувача: {self.context['query']}

1. {rag_section}

2. Погода та найкращий день:
{weather_section}

3. Маршрут (навігація):
{nav_section}
{safety_section}

Структуруй відповідь логічно. Використовуй Markdown.
"""
        try:
            resp = await self.llm.generate([{"role": "user", "content": prompt}])
            content = resp.content if hasattr(resp, "content") else str(resp)
            content = self._ensure_complete_sentence(content)
            content = self._ensure_sections_present(content, results)
            content = self._remove_humidity_lines(content)
            self.context["final_answer"] = content
        except Exception as e:
            logger.error(f"Final summary error: {e}")
            self.context["final_answer"] = f"Досягнуто ліміт токенів або сталася помилка LLM: {e}. Спробуйте пізніше."

    async def _extract_nav_points_from_rag(self, query_location: str) -> Dict[str, Any]:
       
        rag_text = self.context["results"].get("rag", "")
        if not rag_text:
            return {}

        prompt = f"""З тексту про маршрут на {query_location} витягни географічні точки.

Текст:
{rag_text[:2500]}

Поверни ТІЛЬКИ валідний JSON:
{{
  "start_point_name": "назва початкового населеного пункту або місця БЕЗ префіксів (наприклад 'Дземброня', 'Верховина', 'Ворохта') або null",
  "intermediate_points": ["назва проміжної точки БЕЗ префіксів г./пер./хр. (наприклад 'Говерла', 'Яблуниця')", ...]
}}

ВАЖЛИВО:
- НЕ включай префікси: г., гора, пер., перевал, хр., хребет, с., село, м., місто
- Повертай лише власну назву: 'Говерла' замість 'г. Говерла', 'Дземброня' замість 'с. Дземброня'
- Якщо в тексті немає чітких назв точок — поверни null і порожній список.
"""
        try:
            resp = await self.llm.generate([{"role": "user", "content": prompt}])
            raw = resp.content if hasattr(resp, "content") else str(resp)
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                logger.info(f"  [RAG_POINTS] LLM extracted: {data}")
                return data
        except Exception as e:
            logger.error(f"  [RAG_POINTS] LLM extraction error: {e}")
        return {}

    def _extract_text_result(self, result) -> str:
        """Перетворення MCP відповіді в рядок. Підтримує всі формати."""
        if result is None:
            return ""
        if hasattr(result, "content"):
            content = result.content
            if isinstance(content, list):
                parts = []
                for c in content:
                    if hasattr(c, "text"):
                        parts.append(c.text)
                    elif isinstance(c, dict):
                        parts.append(c.get("text", str(c)))
                    else:
                        parts.append(str(c))
                return "\n".join(parts)
            elif isinstance(content, str):
                return content
        if isinstance(result, dict):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    @staticmethod
    def _truncate_by_sentence(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text

        cut = text[:max_chars]
        last_boundary = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("\n"))
        if last_boundary >= max_chars // 2:
            return cut[: last_boundary + 1].rstrip()
        return cut.rstrip() + "..."

    def _ensure_complete_sentence(self, text: str) -> str:
        text = str(text or "").strip()
        if not text:
            return text
        if text[-1] in ".!?»”\"'":
            return text

        last_boundary = max(text.rfind("."), text.rfind("!"), text.rfind("?"))
        if last_boundary >= max(0, len(text) - 260):
            return text[: last_boundary + 1].rstrip()
        return text + "."

    def _extract_weather_brief(self, results: Dict[str, Any]) -> str:
        weather_raw = str(results.get("weather", "") or "")
        best_day = results.get("best_day")
        brief = []
        try:
            w = json.loads(weather_raw)
            days = w.get("data", []) if isinstance(w, dict) else []
            if days:
                d0 = days[0]
                brief.append(
                    f"Поточний прогноз: {d0.get('date', '-')}, t≈{d0.get('temperature', '-') }°C, "
                    f"дощ {d0.get('rain_mm', '-') } мм, вітер {d0.get('wind_m_s', '-') } м/с."
                )
        except Exception:
            pass
        if best_day:
            brief.append(f"Рекомендована дата походу: {best_day}.")
        return " ".join(brief).strip()

    def _compose_weather_section(self, results: Dict[str, Any]) -> str:
        weather_raw = str(results.get("weather", "") or "")
        try:
            w = json.loads(weather_raw)
            days = w.get("data", []) if isinstance(w, dict) else []
            if not days:
                return self._truncate_by_sentence(weather_raw, max_chars=500)

            lines: List[str] = []
            for d in days[:3]:
                date = d.get("date", "-")
                temp = d.get("temperature", "-")
                wind = d.get("wind_m_s", "-")
                desc = d.get("description", "без опису")
                rain = d.get("rain_mm", 0)
                if isinstance(rain, (int, float)) and rain > 0:
                    rain_part = f", дощ {rain} мм"
                else:
                    rain_part = ""
                lines.append(f"- {date}: {desc}, t≈{temp}°C, вітер {wind} м/с{rain_part}.")
            return "\n".join(lines)
        except Exception:
            return self._truncate_by_sentence(weather_raw, max_chars=500)

    def _extract_safety_brief(self, results: Dict[str, Any]) -> str:
        safety = str(results.get("safety", "") or "")
        if not safety:
            return ""
        return self._truncate_by_sentence(safety, max_chars=500)

    def _compose_safety_section(self, safety_chunks: List[Any]) -> str:
        hazard_keywords = (
            "лавин", "туман", "дощ", "гроз", "блискав", "скел", "обрив", "прірв",
            "річк", "переправ", "каменепад", "обморож", "переохолод", "орієнт", "компас",
            "нічлі", "бівуак", "мотузк", "страхув", "сніг", "лід", "хреб", "вітер"
        )
        noise_keywords = (
            "закон", "право", "обов’язки суб’єктів", "реєстрація туристичних груп",
            "загальні положення", "права туристів", "організація туризму"
        )

        picked: List[str] = []
        seen = set()

        for chunk in safety_chunks:
            text = str(chunk).strip()
            if not text:
                continue
            low = text.lower()

            if any(n in low for n in noise_keywords) and not any(h in low for h in hazard_keywords):
                continue
            if not any(h in low for h in hazard_keywords):
                continue

            lines = []
            for line in text.splitlines():
                s = line.strip(" -•\t")
                if not s:
                    continue
                sl = s.lower()
                if any(n in sl for n in noise_keywords) and not any(h in sl for h in hazard_keywords):
                    continue
                lines.append(s)

            summary = " ".join(lines[:4]).strip()
            summary = self._truncate_by_sentence(summary, max_chars=420)
            if not summary:
                continue

            key = summary.lower()
            if key in seen:
                continue
            seen.add(key)
            picked.append(f"- {summary}")
            if len(picked) >= 4:
                break

        if not picked:
            picked = ["- Орієнтуйтеся за картою і компасом, не сходьте з маршруту без потреби."]

        return "\n".join(picked)

    def _ensure_sections_present(self, content: str, results: Dict[str, Any]) -> str:
        out = content.strip()
        low = out.lower()

        if "погод" not in low:
            weather_brief = self._extract_weather_brief(results)
            if weather_brief:
                out += f"\n\n### Погода\n- {weather_brief}"

        best_day = results.get("best_day")
        if best_day and str(best_day) not in out:
            out += f"\n\n### Найкращий день\n- {best_day}."

        if "безпек" not in low:
            safety_brief = self._extract_safety_brief(results)
            if safety_brief:
                out += f"\n\n### Безпека\n- {safety_brief}"

        return self._ensure_complete_sentence(out)

    @staticmethod
    def _remove_humidity_lines(text: str) -> str:
        lines = str(text or "").splitlines()
        filtered = []
        for ln in lines:
            low = ln.lower()
            if "волог" in low or "humidity" in low:
                continue
            filtered.append(ln)
        return "\n".join(filtered).strip()

    def _extract_coords(self, geo_res) -> Optional[Dict[str, float]]:
        if geo_res is None:
            return None
        try:
            raw_text = self._extract_text_result(geo_res)
            logger.info(f"  [COORDS] raw geo text: {raw_text[:300]}")
            data = json.loads(raw_text)

            if isinstance(data, dict):
                for key in ("results", "items", "features"):
                    results_list = data.get(key)
                    if isinstance(results_list, list) and len(results_list) > 0:
                        for item in results_list:
                            lat = item.get("lat") or item.get("latitude")
                            lon = item.get("lon") or item.get("lng") or item.get("longitude")

                            if lat is None:
                                geom = item.get("geometry", {})
                                c = geom.get("coordinates", [])
                                if len(c) >= 2:
                                    lon, lat = c[0], c[1]
                            if lat is None or lon is None:
                                continue

                            lat_f = float(lat)
                            lon_f = float(lon)
                            country = str(item.get("countryIso", "")).upper()
                            in_ukraine = country == "UA" or (44.0 <= lat_f <= 52.5 and 22.0 <= lon_f <= 40.5)
                            if in_ukraine:
                                logger.info(f"  [COORDS] from '{key}' (UA): lat={lat_f}, lon={lon_f}")
                                return {"lat": lat_f, "lon": lon_f}

                        logger.info(f"  [COORDS] '{key}' had results, but none in UA")

                lat = data.get("lat") or data.get("latitude")
                lon = data.get("lon") or data.get("lng") or data.get("longitude")
                if lat is not None and lon is not None:
                    return {"lat": float(lat), "lon": float(lon)}

            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                lat = item.get("lat") or item.get("latitude")
                lon = item.get("lon") or item.get("lng") or item.get("longitude")
                if lat is not None and lon is not None:
                    return {"lat": float(lat), "lon": float(lon)}

        except Exception as e:
            logger.error(f"  [COORDS] error: {e}")
        return None

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        import math

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return 6371.0 * c

    def _extract_primary_route_name_from_rag(self) -> Optional[str]:
        rag_analyzed = self.context["results"].get("rag_analyzed", "")
        if rag_analyzed:
            try:
                data = json.loads(rag_analyzed)
                routes = data.get("structured_data", {}).get("routes", [])
                if routes and routes[0].get("name"):
                    return str(routes[0]["name"]).strip()
            except Exception:
                pass

        rag_raw = self.context["results"].get("rag", "")
        if rag_raw:
            try:
                data = json.loads(rag_raw)
                chunks = data.get("chunks", [])
                if chunks:
                    m = re.search(r"МАРШРУТ\s*:\s*[^\n]*-\s*(?:гора\s+|г\.\s*)?([A-Za-zА-Яа-яІіЇїЄєҐґ'’\-\s]{3,})", chunks[0], re.IGNORECASE)
                    if m:
                        return self._clean_geo_name(m.group(1)).strip()
            except Exception:
                pass
        return None

    def _extract_nav_points_heuristic(self) -> Dict[str, Any]:
        rag_raw = self.context["results"].get("rag", "")
        if not rag_raw:
            return {}
        try:
            data = json.loads(rag_raw)
            chunks = data.get("chunks", [])
            if not chunks:
                return {}

            line = None
            for ln in str(chunks[0]).splitlines():
                if "маршрут" in ln.lower() and ":" in ln:
                    line = ln
                    break
            if not line:
                return {}

            route_part = line.split(":", 1)[1].strip()
            parts = [self._clean_geo_name(p).strip(" .,") for p in route_part.split("-") if p.strip()]
            parts = [p for p in parts if len(p) >= 2]
            if len(parts) < 2:
                return {}

            return {
                "start_point_name": parts[0],
                "intermediate_points": parts[1:-1],
                "end_point_name": parts[-1]
            }
        except Exception:
            return {}

    @staticmethod
    def _clean_geo_name(name: str) -> str:
      
        prefixes = [
            r"^г\.\s*",         
            r"^гора\s+",         
            r"^пер\.\s*",       
            r"^перевал\s+",     
            r"^хр\.\s*",         
            r"^хребет\s+",       
            r"^с\.\s*",          
            r"^село\s+",     
            r"^м\.\s*",         
            r"^місто\s+",        
            r"^смт\.?\s*",      
            r"^вершина\s+",      
            r"^оз\.\s*",        
            r"^озеро\s+",        
            r"^потік\s+",      
            r"^урочище\s+",     
        ]
        cleaned = name.strip()
        for pattern in prefixes:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    _UA_TO_LAT: Dict[str, str] = {
        'А': 'A',  'а': 'a',  'Б': 'B',  'б': 'b',  'В': 'V',  'в': 'v',
        'Г': 'H',  'г': 'h',  'Ґ': 'G',  'ґ': 'g',  'Д': 'D',  'д': 'd',
        'Е': 'E',  'е': 'e',  'Є': 'Ye', 'є': 'ye', 'Ж': 'Zh', 'ж': 'zh',
        'З': 'Z',  'з': 'z',  'И': 'Y',  'и': 'y',  'І': 'I',  'і': 'i',
        'Ї': 'Yi', 'ї': 'yi', 'Й': 'Y',  'й': 'y',  'К': 'K',  'к': 'k',
        'Л': 'L',  'л': 'l',  'М': 'M',  'м': 'm',  'Н': 'N',  'н': 'n',
        'О': 'O',  'о': 'o',  'П': 'P',  'п': 'p',  'Р': 'R',  'р': 'r',
        'С': 'S',  'с': 's',  'Т': 'T',  'т': 't',  'У': 'U',  'у': 'u',
        'Ф': 'F',  'ф': 'f',  'Х': 'Kh', 'х': 'kh', 'Ц': 'Ts', 'ц': 'ts',
        'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Shch', 'щ': 'shch',
        'Ь': '',   'ь': '',   'Ю': 'Yu', 'ю': 'yu', 'Я': 'Ya', 'я': 'ya',
        "'": '',   '\u2019': '',
    }

    def _transliterate_ua(self, text: str) -> str:
        result = []
        for ch in text:
            result.append(self._UA_TO_LAT.get(ch, ch))
        return ''.join(result)

    def _extract_best_day_date(self, anr_text: str) -> Optional[str]:
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", anr_text)
        if date_match:
            return date_match.group()
        return None

    async def _run_and_store(self, server: str, tool: str, args: Dict[str, Any], result_key: str):
        try:
            res = await self.mcp.call_tool(server, tool, args)
            self.context["results"][result_key] = self._extract_text_result(res)
        except Exception as e:
            logger.error(f"Error calling {tool} on {server}: {e}")
            self.context["results"][result_key] = f"Помилка сервісу '{server}': {e}"



async def main():
    orchestrator = HybridOrchestrator()
    try:
        await orchestrator.initialize()

        print("\n" + "="*60)
        print("  Гірський асистент — Карпати")
        print("  Введіть запит або 'вихід' / 'exit' щоб завершити.")
        print("  Пам'ять зберігає останні 10 повідомлень діалогу.")
        print("="*60 + "\n")

        while True:
            try:
                query = input("[Ви]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[Завершення сесії]")
                break

            if not query:
                continue

            if query.lower() in ("вихід", "exit", "quit", "q"):
                print("[Асистент]: До побачення")
                break

            if query.lower() in ("очистити", "clear", "reset"):
                orchestrator.memory.clear()
                print("[Асистент]: Пам'ять очищено.\n")
                continue

            print()
            answer = await orchestrator.process_query(query)
            print(f"[Асистент]:\n{answer}\n")

    finally:
        await orchestrator.mcp.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())