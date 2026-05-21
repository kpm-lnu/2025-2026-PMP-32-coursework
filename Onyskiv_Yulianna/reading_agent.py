import sqlite3
import os
import sys
import json
import hashlib
import chromadb
import math
from collections import Counter
from chromadb.utils import embedding_functions
from datetime import datetime, date
from mcp.server.fastmcp import FastMCP

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "reading_analytics.db")
CHROMA_PATH = os.path.join(APP_DIR, "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
book_collection = chroma_client.get_or_create_collection(
    name="book_chunks",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)
mcp = FastMCP("ReadingIntellectAgent")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def normalize_title(title: str) -> str:
    return ' '.join(title.strip().split()).title()

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    username TEXT,
                    book_title TEXT,
                    pages_read INTEGER,
                    last_page INTEGER DEFAULT 0,
                    minutes INTEGER,
                    mood TEXT
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash TEXT,
                    created_at TEXT,
                    daily_goal INTEGER DEFAULT 20
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT
                )
            ''')
            conn.commit()
    except Exception as e:
        sys.stderr.write(f"Database error: {e}\n")

init_db()

@mcp.tool()
def register_or_login(username: str, password: str):
    try:
        pwd_hash = hash_password(password)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT username, daily_goal, password_hash'
                ' FROM users WHERE username = ?',
                (username,)
            )
            user = cursor.fetchone()
            if user:
                if user[2] != pwd_hash:
                    return '❌ Невірний пароль. Спробуйте ще раз.'
                return (
                    f'✅ Вітаємо, {username}! '
                    f'Денна ціль: {user[1]} стор/день.'
                )
            else:
                created_at = datetime.now().strftime('%Y-%m-%d')
                cursor.execute(
                    'INSERT INTO users'
                    ' (username, password_hash, created_at, daily_goal)'
                    ' VALUES (?, ?, ?, ?)',
                    (username, pwd_hash, created_at, 20)
                )
                return (
                    f'✅ Профіль створено! Вітаємо, {username}! '
                    f'Денна ціль: 20 стор/день.'
                )
    except Exception as e:
        return f'❌ Помилка: {str(e)}'

@mcp.tool()
def update_user_goal(username: str, goal_pages_per_day: int):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET daily_goal = ? WHERE username = ?",
                (goal_pages_per_day, username)
            )
        return f"✅ Ціль оновлено! Тепер ваша ціль: {goal_pages_per_day} сторінок на день."
    except Exception as e:
        return f"❌ Помилка: {str(e)}"


@mcp.tool()
def get_daily_goal(username: str):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT daily_goal FROM users WHERE username = ?", (username,))
        res = cursor.fetchone()
        goal = res[0] if res and res[0] else 30

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("SELECT SUM(pages_read) FROM activities WHERE username = ? AND date LIKE ?",
                       (username, f"{today}%"))
        read_today = cursor.fetchone()[0] or 0

        return json.dumps({"goal": goal, "read": read_today})


@mcp.tool()
def log_reading_session(username: str, book_title: str, pages_read: int, current_page: int, minutes: int,
                        mood: str = "нейтральний", session_date: str = ""):
    if pages_read <= 0 or minutes <= 0:
        return "⚠️ Помилка: Кількість сторінок та час читання мають бути більшими за 0."
    book_title = normalize_title(book_title)

    if session_date:
        try:
            datetime.strptime(session_date, "%Y-%m-%d")
            timestamp = session_date + " 00:00"
        except ValueError:
            return "⚠️ Невірний формат дати. Використовуйте: РРРР-ММ-ДД"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO activities (date, username, book_title, pages_read, last_page, minutes, mood) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (timestamp, username, book_title, pages_read, current_page, minutes, mood)
            )
        return f"✅ Записано! Книга '{book_title}', сторінка {current_page}. Прочитано {pages_read} стор за {minutes} хв. Настрій: {mood}. Дата: {timestamp[:10]}."
    except Exception as e:
        return f"❌ Помилка при записі в БД: {str(e)}"


@mcp.tool()
def get_user_sessions(username: str, book_title: str = ""):

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if book_title:
                book_title = normalize_title(book_title)
                cursor.execute(
                    "SELECT id, date, book_title, pages_read, minutes, mood FROM activities WHERE username = ? AND book_title = ? ORDER BY date DESC",
                    (username, book_title)
                )
            else:
                cursor.execute(
                    "SELECT id, date, book_title, pages_read, minutes, mood FROM activities WHERE username = ? ORDER BY date DESC",
                    (username,)
                )
            rows = cursor.fetchall()
        if not rows:
            return "📭 Сесій не знайдено."
        lines = ["📋 ВАШІ СЕСІЇ:\n"]
        for r in rows:
            lines.append(f"ID:{r[0]} | {r[1][:10]} | '{r[2]}' | {r[3]} стор | {r[4]} хв | {r[5]}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Помилка: {str(e)}"


@mcp.tool()
def delete_reading_session(username: str, session_id: int):

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM activities WHERE id = ? AND username = ?",
                (session_id, username)
            )
            if not cursor.fetchone():
                return f"❌ Сесію з ID {session_id} не знайдено."
            cursor.execute("DELETE FROM activities WHERE id = ?", (session_id,))
        return f"✅ Сесію #{session_id} видалено."
    except Exception as e:
        return f"❌ Помилка: {str(e)}"


@mcp.tool()
def get_bookmark(username: str, book_title: str):
    try:
        book_title = normalize_title(book_title)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT last_page, date FROM activities WHERE username = ? AND book_title = ? ORDER BY id DESC LIMIT 1",
                (username, book_title)
            )
            result = cursor.fetchone()
        if result:
            return f"📖 У книзі '{book_title}' ви зупинилися на сторінці {result[0]} (остання сесія: {result[1]})."
        return f"🔍 Книга '{book_title}' ще не знайдена. Час почати читати!"
    except Exception as e:
        return f"⚠️ Помилка пошуку закладки: {str(e)}"


@mcp.tool()
def get_user_books(username: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT book_title, MAX(last_page) as last_page,
                   SUM(pages_read) as total_read, SUM(minutes) as total_minutes
                   FROM activities WHERE username = ?
                   GROUP BY book_title ORDER BY MAX(date) DESC""",
                (username,)
            )
            books = cursor.fetchall()
        if not books:
            return "📚 У вас ще немає записаних книг."
        lines = ["📚 ВАШІ КНИГИ:\n"]
        for b in books:
            lines.append(f"• '{b[0]}' — сторінка {b[1]}, прочитано {b[2]} стор за {b[3]} хв")
        return "\n".join(lines)
    except Exception as e:
        return f"⚠️ Помилка: {str(e)}"


@mcp.tool()
def analyze_reading_stats(username: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pages_read, minutes, mood FROM activities WHERE username = ?",
                (username,)
            )
            data = cursor.fetchall()

            cursor.execute("SELECT daily_goal FROM users WHERE username = ?", (username,))
            goal_row = cursor.fetchone()
            goal = goal_row[0] if goal_row else 20

        if not data:
            return "📊 Ваша база даних порожня. Запишіть першу сесію читання!"

        total_pages = sum(row[0] for row in data)
        total_minutes = sum(row[1] for row in data)
        sessions = len(data)
        speed = round((total_pages / total_minutes) * 60, 1) if total_minutes > 0 else 0
        avg_per_session = round(total_pages / sessions, 1)
        moods = [row[2] for row in data]
        most_common_mood = Counter(moods).most_common(1)[0][0] if moods else "немає даних"



        return (
            f"📈 АНАЛІТИКА для {username}:\n"
            f"📖 Всього прочитано сторінок: {total_pages}\n"
            f"⏱️ Загальний час: {total_minutes} хв ({round(total_minutes/60, 1)} год)\n"
            f"🔢 Кількість сесій: {sessions}\n"
            f"⚡ Середня швидкість: {speed} стор/год\n"
            f"📊 Середньо за сесію: {avg_per_session} стор\n"
            f"🎯 Ваша ціль: {goal} стор/день\n"
            f"😊 Найчастіший настрій: {most_common_mood}\n"
            f"🏆 Статус: {'🌟 Активний читач' if total_pages > 100 else '🌱 Початківець'}"
        )
    except Exception as e:
        return f"⚠️ Не вдалося провести аналіз: {str(e)}"


@mcp.tool()
def get_analytics_data(username: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT date, book_title, pages_read, minutes, mood
                   FROM activities WHERE username = ? ORDER BY date""",
                (username,)
            )
            rows = cursor.fetchall()
        if not rows:
            return "EMPTY"
        data = [{"date": r[0], "book": r[1], "pages": r[2], "minutes": r[3], "mood": r[4]} for r in rows]
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        return f"ERROR:{str(e)}"


@mcp.tool()
def add_book_content(username: str, book_title: str, content: str, chunk_size: int = 500):
    try:
        book_title = normalize_title(book_title)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM activities WHERE username = ? AND book_title = ? LIMIT 1",
                (username, book_title)
            )
            result = cursor.fetchone()

        if not result:
            return (
                f"⚠️ Книгу '{book_title}' ще не знайдено у вашій бібліотеці. "
                f"Спочатку запишіть сесію читання через log_reading_session, "
                f"потім додайте зміст через цю функцію."
            )

        book_id = str(result[0])

        overlap = 50
        chunks = []
        start = 0
        while start < len(content):
            end = min(start + chunk_size, len(content))
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - overlap

        if not chunks:
            return "⚠️ Текст порожній або занадто короткий."

        ids = [f"{username}_{book_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "username": username,
                "book_title": book_title,
                "book_id": book_id,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]

        book_collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

        return (
            f"✅ Зміст книги '{book_title}' успішно додано до векторної бази!\n"
            f"📦 Створено {len(chunks)} фрагментів по ~{chunk_size} символів.\n"
            f"🔍 Тепер можна шукати по тексту через search_in_book_content."
        )

    except Exception as e:
        return f"❌ Помилка при індексації: {str(e)}"


@mcp.tool()
def search_in_book_content(username: str, book_title: str, query: str, n_results: int = 3):

    try:
        book_title = normalize_title(book_title)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM activities WHERE username = ? AND book_title = ? LIMIT 1",
                (username, book_title)
            )
            result = cursor.fetchone()

        if not result:
            return f"❌ Книгу '{book_title}' не знайдено у вашій бібліотеці."

        book_id = str(result[0])

        search_results = book_collection.query(
            query_texts=[query],
            n_results=n_results,
            where={
                "$and": [
                    {"username": {"$eq": username}},
                    {"book_id": {"$eq": book_id}}
                ]
            }
        )

        documents = search_results.get("documents", [[]])[0]
        distances = search_results.get("distances", [[]])[0]

        if not documents:
            return (
                f"🔍 Не знайдено фрагментів для '{book_title}'.\n"
                f"💡 Додайте текст книги через інструмент add_book_content."
            )

        context_parts = []
        for i, (doc, dist) in enumerate(zip(documents, distances), 1):
            relevance = round((1 - dist) * 100, 1)
            context_parts.append(f"[Фрагмент {i} | Релевантність: {relevance}%]\n{doc}")

        context = "\n\n---\n\n".join(context_parts)

        return (
            f"RAG_CONTEXT для питання '{query}' з книги '{book_title}':\n\n"
            f"{context}\n\n"
            f"На основі цих фрагментів дай відповідь на питання: {query}"
        )

    except Exception as e:
        return f"❌ Помилка RAG-пошуку: {str(e)}"


@mcp.tool()
def list_indexed_books(username: str):
    try:
        results = book_collection.get(
            where={"username": {"$eq": username}},
            include=["metadatas"]
        )

        if not results["metadatas"]:
            return (
                f"📭 У векторній базі ще немає книг для '{username}'.\n"
                f"💡 Додайте текст через add_book_content."
            )

        book_stats: dict = {}
        for meta in results["metadatas"]:
            title = meta["book_title"]
            book_stats[title] = book_stats.get(title, 0) + 1

        lines = [f"📚 Проіндексовані книги '{username}':\n"]
        for title, count in book_stats.items():
            lines.append(f"  • {title} — {count} фрагментів")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Помилка: {str(e)}"


@mcp.tool()
def explain_text_fragment(text: str):
    return f"EXPLAIN:{text}"


@mcp.tool()
def explain_term_wikipedia(term: str):
    try:
        import wikipediaapi
        wiki_uk = wikipediaapi.Wikipedia(
            language='uk',
            user_agent='ReadingAgent/1.0'
        )
        page = wiki_uk.page(term)
        if page.exists():
            summary = page.summary[:600]
            return f"WIKI_RESULT:📖 {term} (Вікіпедія):\n{summary}\n🔗 {page.fullurl}"

        wiki_en = wikipediaapi.Wikipedia(
            language='en',
            user_agent='ReadingAgent/1.0'
        )
        page_en = wiki_en.page(term)
        if page_en.exists():
            summary = page_en.summary[:600]
            return f"WIKI_RESULT:📖 {term} (Wikipedia EN):\n{summary}\n🔗 {page_en.fullurl}"

        return f"❌ Термін '{term}' не знайдено у Вікіпедії."
    except Exception as e:
        return f"⚠️ Помилка пошуку у Вікіпедії: {str(e)}"


@mcp.tool()
def recommend_books(username: str, topic: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT book_title FROM activities WHERE username = ?",
                (username,)
            )
            books = [row[0] for row in cursor.fetchall()]

        if books:
            books_str = ", ".join(books)
            return f"RECOMMEND:тема '{topic}'. Користувач вже читав: {books_str}. Порекомендуй схожі книги яких немає в цьому списку."
        else:
            return f"RECOMMEND:{topic}"
    except Exception as e:
        return f"RECOMMEND:{topic}"


@mcp.tool()
def reading_plan(username: str, book_title: str, total_pages: int, deadline_date: str, already_read: int = 0):
    try:
        deadline = datetime.strptime(deadline_date, "%Y-%m-%d").date()
        today = date.today()
        if deadline <= today:
            return "⚠️ Дедлайн вже минув. Оберіть майбутню дату."
        days_left = (deadline - today).days
        pages_left = total_pages - already_read
        if pages_left <= 0:
            return f"🎉 Ви вже прочитали книгу '{book_title}'!"
        pages_per_day = math.ceil(pages_left / days_left, 1)
        minutes_per_day = round((pages_per_day / 30) * 60)
        return (
            f"📅 ПЛАН ЧИТАННЯ: '{book_title}'\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Читач: {username}\n"
            f"📖 Залишилось: {pages_left} з {total_pages} сторінок\n"
            f"📆 Днів до дедлайну: {days_left}\n"
            f"📌 Потрібно читати: {pages_per_day} стор/день\n"
            f"⏱️ Орієнтовно: ~{minutes_per_day} хв/день\n"
            f"🎯 Дедлайн: {deadline_date}"
        )
    except ValueError:
        return "⚠️ Невірний формат дати. Використовуйте: РРРР-ММ-ДД"
    except Exception as e:
        return f"⚠️ Помилка: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")