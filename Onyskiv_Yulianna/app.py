import asyncio
import json
import os
import sys
import sqlite3
import traceback
import time
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="Агент Читача", page_icon="📚", layout="wide")

server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reading_agent.py")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reading_analytics.db")

server_params = StdioServerParameters(
    command=sys.executable,
    args=["-u", server_path],
    env={**os.environ, "PYTHONUNBUFFERED": "1"}
)

DIRECT_RESULT_TOOLS = {
    "get_user_sessions",
    "delete_reading_session",
    "get_user_books",
    "analyze_reading_stats",
    "get_bookmark",
    "log_reading_session",
    "update_user_goal",
    "reading_plan",
    "list_indexed_books",
    "clear_chat_history",
}

def load_chat_history_from_db(username: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE username = ? ORDER BY id ASC LIMIT 100",
                (username,)
            )
            rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]
    except Exception:
        return []


def save_message_to_db(username: str, role: str, content: str):
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO chat_history (username, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (username, role, content, timestamp)
            )
    except Exception:
        pass


def clear_chat_history_in_db(username: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM chat_history WHERE username = ?", (username,))
    except Exception:
        pass

def show_login():
    st.title('📚 Reading Agent')
    st.markdown('### Вхід / Реєстрація')
    username = st.text_input('Імʼя користувача:')
    password = st.text_input('Пароль:', type='password')
    if st.button('Увійти / Зареєструватись'):
        if username and password:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                call_tool_directly('register_or_login',
                         {'username': username, 'password': password})
            )
            if '❌' in result:
                st.error(result)
            else:
                st.session_state.username = username
                st.session_state.password = password
                st.success(result)
                st.rerun()
        else:
            st.warning('Введіть імʼя та пароль.')


def convert_mcp_tools_to_groq(mcp_tools):
    groq_tools = []
    for tool in mcp_tools.tools:
        groq_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema
            }
        })
    return groq_tools


def ask_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Відповідай ТІЛЬКИ українською мовою. Не використовуй жодних інших мов чи символів. Будь корисним помічником читача."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


async def call_tool_directly(tool_name: str, args: dict) -> str:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, args)
            return result.content[0].text


async def run_agent(user_prompt: str, username: str):
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                mcp_tools = await session.list_tools()
                groq_tools = convert_mcp_tools_to_groq(mcp_tools)

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"Ти — інтелектуальний помічник читача. Поточний користувач: '{username}'. "
                                f"Завжди передавай username='{username}' у всі інструменти. "
                                f"Відповідай ТІЛЬКИ українською мовою. Не використовуй жодних інших мов чи символів.\n\n"
                                "ПРАВИЛА ДЛЯ RAG:\n"
                                "- Якщо користувач питає про ЗМІСТ книги: виклич 'search_in_book_content'.\n"
                                "- Якщо отримав RAG_CONTEXT — використай ці фрагменти для відповіді.\n"
                                "- Якщо фрагментів немає — порадь додати текст через 'add_book_content'.\n"
                                "- Ніколи не вигадуй зміст книг — тільки на основі знайденого контексту.\n\n"
                               "ПРАВИЛА ДЛЯ ПОЯСНЕНЬ:\n"
                               "- Якщо користувач просить пояснити складний фрагмент тексту: виклич 'explain_text_fragment'.\n"
                               "- Якщо користувач питає що таке якийсь термін або поняття: виклич 'explain_term_wikipedia'.\n"
                               "- Якщо користувач просить знайти визначення або інформацію про щось: виклич 'explain_term_wikipedia'.\n\n"
                                "ПРАВИЛА ДЛЯ СЕСІЙ:\n"
                                "- Якщо користувач питає про свої сесії або хоче їх переглянути: виклич 'get_user_sessions'.\n"
                                "- Якщо користувач хоче видалити сесію: спочатку виклич 'get_user_sessions', потім 'delete_reading_session'.\n\n"
                                "ПРАВИЛА ДЛЯ РЕКОМЕНДАЦІЙ:\n"  
                                "- Якщо користувач просить порекомендувати книги: виклич 'recommend_books' з username і темою.\n"

                            )
                        },
                        {"role": "user", "content": user_prompt}
                    ],
                    tools=groq_tools,
                    tool_choice="auto"
                )

                msg = response.choices[0].message
                if not msg.tool_calls:
                    return msg.content or "Агент не дав відповіді."

                messages_history = [
                    {"role": "system",
                     "content": f"Ти помічник читача. Користувач: '{username}'. Відповідай ТІЛЬКИ українською мовою."},
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls}
                ]

                tool_results_for_llm = []
                for tool_call in msg.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    tool_name = tool_call.function.name
                    result = await session.call_tool(tool_name, args)
                    tool_result = result.content[0].text

                    if tool_result.startswith("EXPLAIN:"):
                        return ask_groq(f"Поясни термін '{tool_result[8:]}' простими словами.")
                    elif tool_result.startswith("RECOMMEND:"):
                        return ask_groq(f"Порекомендуй 5 книг на тему '{tool_result[10:]}'.")
                    elif tool_result.startswith("WIKI_RESULT:"):
                        return tool_result[12:]


                    if tool_name in DIRECT_RESULT_TOOLS:
                        return tool_result

                    tool_results_for_llm.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })

                if tool_results_for_llm:
                    messages_history.extend(tool_results_for_llm)
                    final_response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=messages_history
                    )
                    return final_response.choices[0].message.content
                return msg.content
    except Exception as e:
        return f"Помилка: {str(e)}\n\n{traceback.format_exc()}"


def show_analytics(username: str):
    try:
        import pandas as pd
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            call_tool_directly("get_analytics_data", {"username": username})
        )

        if result == "EMPTY":
            st.info("📊 Немає даних для аналітики.")
            return

        data = json.loads(result)
        df = pd.DataFrame(data)

        df["date"] = pd.to_datetime(df["date"])
        st.markdown("### 📈 Аналітика читання")

        period = st.selectbox("Період:", ["Весь час", "7 днів", "30 днів"])
        if period == "7 днів":
            df = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        elif period == "30 днів":
            df = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)]

        c1, c2, c3 = st.columns(3)
        c1.metric("📖 Всього сторінок", df["pages_read"].sum())
        c2.metric("⏱️ Годин читання", round(df["minutes"].sum() / 60, 1))
        c3.metric("📅 Сесій", len(df))

        df["день"] = df["date"].dt.strftime("%Y-%m-%d")
        chart_data = df.groupby("день")["pages_read"].sum().reset_index()
        chart_data.columns = ["Дата", "Сторінки"]
        chart_data = chart_data.sort_values("Дата")
        st.bar_chart(chart_data.set_index("Дата"), height=300, use_container_width=False, width=600)

    except Exception as e:
        st.error(f"Помилка аналітики: {e}")


def show_indexing_page(username: str):
    st.title("📖 Індексація книг для RAG-пошуку")
    if st.button("🔍 Показати проіндексовані книги"):
        loop = asyncio.new_event_loop()
        try:
            res = loop.run_until_complete(call_tool_directly("list_indexed_books", {"username": username}))
            st.info(res)
        finally:
            loop.close()

    st.markdown("---")
    book_title = st.text_input("Назва книги для індексації:")
    input_method = st.radio("Метод:", ["Текст", "Файл .txt"])
    content = ""
    if input_method == "Текст":
        content = st.text_area("Вставте текст:")
    else:
        file = st.file_uploader("Завантажте файл", type=["txt"])
        if file:
            content = file.read().decode("utf-8")

    if st.button("📦 Проіндексувати"):
        if book_title and content:
            with st.spinner("Обробка..."):
                loop = asyncio.new_event_loop()
                try:
                    res = loop.run_until_complete(call_tool_directly("add_book_content", {
                        "username": username,
                        "book_title": book_title,
                        "content": content,
                        "chunk_size": 500
                    }))
                    st.success(res)
                finally:
                    loop.close()


def show_timer():
    st.title("⏱️ Таймер читання")
    username = st.session_state.get('username', '')

    book_title = st.text_input("Назва книги:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶️ Почати читання"):
            if book_title:
                st.session_state.timer_start = time.time()
                st.session_state.timer_book = book_title
                st.session_state.timer_running = True
                st.success(f"Таймер запущено для книги: {book_title}")
            else:
                st.warning("Введіть назву книги.")

    if st.session_state.get('timer_running'):
        elapsed_sec = int(time.time() - st.session_state.timer_start)
        elapsed_min = elapsed_sec // 60
        elapsed_s = elapsed_sec % 60
        st.info(
            f"⏳ Читаєте книгу: **{st.session_state.timer_book}**\n\n"
            f"Час: {elapsed_min:02d}:{elapsed_s:02d}"
        )

        st.markdown("---")
        st.markdown("✅ Запишіть сесію:")

        pages = st.number_input("Прочитано сторінок:", min_value=1, value=10)
        current_page = st.number_input("Поточна сторінка:", min_value=1, value=10)
        mood = st.selectbox("Настрій:", [
            "чудовий", "добрий", "нейтральний", "втомлений", "поганий"
        ])

        with col2:
            if st.button("⏹️ Завершити і зберегти"):
                elapsed_sec = int(time.time() - st.session_state.timer_start)
                elapsed_min = max(1, elapsed_sec // 60)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    call_tool_directly('log_reading_session', {
                        'username': username,
                        'book_title': st.session_state.timer_book,
                        'pages_read': pages,
                        'current_page': current_page,
                        'minutes': elapsed_min,
                        'mood': mood
                    })
                )

                st.session_state.timer_running = False
                st.session_state.timer_start = None
                st.session_state.timer_book = None
                st.success(f"✅ Сесію збережено! {elapsed_min} хв читання.\n{result}")
                st.rerun()

if "username" not in st.session_state:
    show_login()
else:
    username = st.session_state.username

    with st.sidebar:
        st.markdown(f"### 👤 {username}")

        try:
            goal_data_raw = asyncio.run(call_tool_directly("get_daily_goal", {"username": username}))
            goal_data = json.loads(goal_data_raw)

            goal = goal_data["goal"]
            read = goal_data["read"]

            progress = min(read / goal, 1.0) if goal > 0 else 0

            st.markdown(f"**Ціль на день: {goal} стор.**")
            st.progress(progress)
            st.caption(f"Прочитано {read} з {goal} сторінок")

            if read >= goal:
                st.success("🎉 Ціль виконана!")
        except Exception as e:
            st.error("Помилка завантаження цілі")

        st.markdown("---")

        page = st.radio("Навігація:", [
            "💬 Чат",
            "📊 Аналітика",
            "📚 Мої книги",
            "📖 Індексація",
            "⏱️ Таймер"
        ])

        st.markdown("---")
        if st.button("🚪 Вийти"):
            st.session_state.clear()
            st.rerun()

    if page == "💬 Чат":
        st.title("📚 Агент читача")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = load_chat_history_from_db(username)


        if st.button("🗑️ Очистити історію чату"):
            clear_chat_history_in_db(username)
            st.session_state.chat_history = []
            st.rerun()


        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

        prompt = st.chat_input("Запитай щось...")
        if prompt:

            save_message_to_db(username, "user", prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                loop = asyncio.new_event_loop()
                res = loop.run_until_complete(run_agent(prompt, username))
                st.markdown(res)


            save_message_to_db(username, "assistant", res)
            st.session_state.chat_history.append({"role": "assistant", "content": res})

    elif page == "📊 Аналітика":
        show_analytics(username)

    elif page == "📚 Мої книги":
        st.title("📚 Ваша бібліотека")
        loop = asyncio.new_event_loop()
        st.markdown(loop.run_until_complete(
            call_tool_directly("get_user_books", {"username": username})
        ))

    elif page == "📖 Індексація":
        show_indexing_page(username)

    elif page == "⏱️ Таймер":
        show_timer()