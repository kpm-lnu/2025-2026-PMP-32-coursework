"""

Запуск:  streamlit run app.py
"""

import asyncio
import sys
import os
import atexit
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from orchestrators.final_orcestrator import HybridOrchestrator

logger = logging.getLogger(__name__)

def _get_persistent_loop() -> asyncio.AbstractEventLoop:
    if "event_loop" not in st.session_state or st.session_state.event_loop.is_closed():
        loop = asyncio.new_event_loop()
        st.session_state.event_loop = loop
    return st.session_state.event_loop


def run_async(coro):
    loop = _get_persistent_loop()
    return loop.run_until_complete(coro)


def _shutdown_mcp():
    orc = st.session_state.get("orchestrator") if "session_state" in dir(st) else None
    if orc is None:
        return
    try:
        loop = st.session_state.get("event_loop")
        if loop and not loop.is_closed():
            loop.run_until_complete(orc.mcp.disconnect_all())
        else:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(orc.mcp.disconnect_all())
            loop.close()
    except Exception:
        pass

atexit.register(_shutdown_mcp)



st.set_page_config(
    page_title="Карпатський Маршрутний Асистент",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown("""
<style>
    /* Загальні стилі */
    .stChatMessage { max-width: 100%; }
    .block-container { padding-top: 2rem; }

    /* Стилі для заголовку */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .main-header h1 { color: #2E7D32; margin: 0; }
    .main-header p  { color: #666; margin: 0.3rem 0 0 0; }

    /* Sidebar */
    .sidebar-card {
        background: linear-gradient(135deg, #e8f5e9 0%, #f1f8e9 100%);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        border: 1px solid #c8e6c9;
    }
    .sidebar-card h4 {
        color: #1B5E20;
        margin: 0 0 10px 0;
        font-size: 1rem;
        letter-spacing: 0.3px;
    }
    .sidebar-card ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .sidebar-card ul li {
        color: #333333;
        font-size: 0.88rem;
        padding: 5px 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .sidebar-card ul li:last-child { border-bottom: none; }
    .sidebar-title {
        color: #1B5E20;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #4CAF50;
    }
    .sidebar-status {
        background: #f9fbe7;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 12px;
        border: 1px solid #dce775;
        color: #33691e;
        font-size: 0.85rem;
    }

    /* Main header */
    .main-header p { color: #555555 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-title">Панель керування</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-card">
        <h4>Можливості системи</h4>
        <ul>
            <li>Пошук маршрутів у Карпатах (RAG)</li>
            <li>Прогноз погоди та вибір найкращого дня</li>
            <li>Побудова навігаційного маршруту</li>
            <li>Рекомендації безпеки для туристів</li>
            <li>Створення подій календаря (.ics)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Очистити чат", use_container_width=True, type="secondary"):
        if "orchestrator" in st.session_state and st.session_state.orchestrator is not None:
            st.session_state.orchestrator.memory.clear()
        st.session_state.messages = []
        st.session_state.html_maps = {}
        st.session_state.calendar_files = {}
        st.rerun()

    if st.session_state.get("initialized"):
        st.markdown('<div class="sidebar-status">Система активна — 5 MCP серверів підключено</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="sidebar-status">Ініціалізація...</div>', unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False

if "html_maps" not in st.session_state:
    st.session_state.html_maps = {} 

if "calendar_files" not in st.session_state:
    st.session_state.calendar_files = {}



def init_orchestrator():
    orchestrator = HybridOrchestrator()
    run_async(orchestrator.initialize())
    return orchestrator


if not st.session_state.initialized:
    with st.spinner("Ініціалізація MCP серверів та бази знань..."):
        try:
            st.session_state.orchestrator = init_orchestrator()
            st.session_state.initialized = True
            st.toast("Систему ініціалізовано!")
        except Exception as e:
            st.error(f"Помилка ініціалізації: {e}")
            logger.exception("Initialization error")
            st.stop()


st.markdown("""
<div class="main-header">
    <h1>Карпатський Маршрутний Асистент</h1>
    <p>Плануйте маршрути, дізнавайтесь погоду та отримуйте рекомендації безпеки</p>
</div>
""", unsafe_allow_html=True)



for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and idx in st.session_state.html_maps:
            html_path = st.session_state.html_maps[idx]
            if Path(html_path).exists():
                with st.expander("Інтерактивна карта маршруту", expanded=False):
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    st.components.v1.html(html_content, height=500, scrolling=True)

        if msg["role"] == "assistant" and idx in st.session_state.calendar_files:
            ics_path = Path(st.session_state.calendar_files[idx])
            if ics_path.exists():
                with open(ics_path, "rb") as f:
                    st.download_button(
                        label="Завантажити подію календаря (.ics)",
                        data=f.read(),
                        file_name=ics_path.name,
                        mime="text/calendar",
                        key=f"dl_ics_hist_{idx}"
                    )

def is_within_ukrainian_mountains(lat: float, lon: float) -> bool:
    ukraine_carpathians_bbox = {
        "min_lat": 47.5, "max_lat": 49.5,
        "min_lon": 22.0, "max_lon": 25.5
    }
    return (
        ukraine_carpathians_bbox["min_lat"] <= lat <= ukraine_carpathians_bbox["max_lat"] and
        ukraine_carpathians_bbox["min_lon"] <= lon <= ukraine_carpathians_bbox["max_lon"]
    )

def extract_coordinates_from_prompt(prompt: str):
    import re
    match = re.search(r"([-+]?\d{1,2}\.\d+),\s*([-+]?\d{1,3}\.\d+)", prompt)
    if match:
        return float(match.group(1)), float(match.group(2))
    return None

if prompt := st.chat_input("Введіть ваш запит про маршрути в Карпатах..."):
    if "orchestrator" not in st.session_state or not st.session_state.orchestrator:
        st.session_state.orchestrator = init_orchestrator()

    try:
        # Set the query in the orchestrator context
        st.session_state.orchestrator.context["query"] = prompt
        # Call the asynchronous _parse_intent method
        run_async(st.session_state.orchestrator._parse_intent())
        intent = st.session_state.orchestrator.context.get("intent", "general")

        if intent == "calendar":
            run_async(st.session_state.orchestrator._calendar_prompt())
            st.success("Подія додана до календаря.")
            st.stop()

        elif intent == "followup":
            run_async(st.session_state.orchestrator._answer_followup())
            followup_answer = st.session_state.orchestrator.context.get("final_answer", "")
            st.markdown(followup_answer)
            st.stop()

        elif intent != "route_planning":
            # If the LLM classified intent as non-route, still proceed with processing.
            # Sometimes intent detection is conservative; RAG might still contain routes.
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                st.info("Надійшов загальний запит — перевіряю базу знань і можливість знайти маршрут. Якщо є дані, буде згенерована карта.")
            st.session_state.messages.append({"role": "assistant", "content": "Перевірка бази знань на наявність маршруту..."})
            # continue processing below (don't stop)
    except Exception as e:
        logger.exception("Error parsing intent")
        st.error(f"Помилка визначення наміру: {e}")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Аналізую запит, шукаю маршрут, перевіряю погоду..."):
            try:
                answer = run_async(
                    st.session_state.orchestrator.process_query(prompt)
                )
            except Exception as e:
                logger.exception("Error processing query")
                answer = f"Виникла помилка при обробці запиту: {e}"

        st.markdown(answer)

        html_path = (
            st.session_state.orchestrator.context
            .get("results", {})
            .get("route_html_path")
        )
        ics_path = (
            st.session_state.orchestrator.context
            .get("results", {})
            .get("calendar_ics_path")
        )
        msg_idx = len(st.session_state.messages)  

        if html_path and Path(html_path).exists():
            st.session_state.html_maps[msg_idx] = html_path
            with st.expander("Інтерактивна карта маршруту", expanded=True):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=500, scrolling=True)

        if ics_path and Path(ics_path).exists():
            st.session_state.calendar_files[msg_idx] = ics_path
            with open(ics_path, "rb") as f:
                st.download_button(
                    label="Завантажити подію календаря (.ics)",
                    data=f.read(),
                    file_name=Path(ics_path).name,
                    mime="text/calendar",
                    key=f"dl_ics_new_{msg_idx}"
                )

    st.session_state.messages.append({"role": "assistant", "content": answer})
