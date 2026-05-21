import pytest
import sqlite3
import json
import hashlib
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def normalize_title(title: str) -> str:
    return ' '.join(title.strip().split()).title()


def init_db(db_path: str):
    with sqlite3.connect(db_path) as conn:
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
        conn.commit()



@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def db_with_user(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at, daily_goal) VALUES (?, ?, ?, ?)",
            ("testuser", hash_password("pass123"), "2025-01-01", 30)
        )
    return db_path


@pytest.fixture
def db_with_activities(db_with_user):
    with sqlite3.connect(db_with_user) as conn:
        conn.executemany(
            "INSERT INTO activities (date, username, book_title, pages_read, last_page, minutes, mood) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("2025-06-01 10:00", "testuser", "Кобзар", 20, 20, 30, "добрий"),
                ("2025-06-02 11:00", "testuser", "Кобзар", 15, 35, 25, "нейтральний"),
                ("2025-06-03 09:00", "testuser", "1984", 30, 30, 45, "чудовий"),
            ]
        )
    return db_with_user

class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_sha256_length(self):
        result = hash_password("anypassword")
        assert len(result) == 64

    def test_same_input_same_output(self):
        assert hash_password("hello") == hash_password("hello")

    def test_different_inputs_different_hashes(self):
        assert hash_password("password1") != hash_password("password2")

    def test_empty_string(self):
        result = hash_password("")
        assert len(result) == 64

    def test_unicode_password(self):
        result = hash_password("пароль123")
        assert len(result) == 64


class TestNormalizeTitle:
    def test_basic_title_case(self):
        assert normalize_title("kobzar") == "Kobzar"

    def test_strips_leading_trailing_spaces(self):
        assert normalize_title("  Кобзар  ") == "Кобзар"

    def test_collapses_multiple_spaces(self):
        assert normalize_title("all this world") == "All This World"

    def test_already_normalized(self):
        assert normalize_title("1984") == "1984"

    def test_mixed_case(self):
        result = normalize_title("the great gatsby")
        assert result == "The Great Gatsby"

    def test_single_word(self):
        assert normalize_title("dune") == "Dune"


class TestInitDb:
    def test_creates_activities_table(self, tmp_path):
        path = str(tmp_path / "new.db")
        init_db(path)
        with sqlite3.connect(path) as conn:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )]
        assert "activities" in tables

    def test_creates_users_table(self, tmp_path):
        path = str(tmp_path / "new.db")
        init_db(path)
        with sqlite3.connect(path) as conn:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )]
        assert "users" in tables

    def test_idempotent_call(self, db_path):

        init_db(db_path)  # другий виклик
        with sqlite3.connect(db_path) as conn:
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count == 0


def register_or_login_logic(username: str, password: str, db_path: str) -> str:
    pwd_hash = hash_password(password)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT username, daily_goal, password_hash FROM users WHERE username = ?',
            (username,)
        )
        user = cursor.fetchone()
        if user:
            if user[2] != pwd_hash:
                return '❌ Невірний пароль. Спробуйте ще раз.'
            return f'✅ Вітаємо, {username}! Денна ціль: {user[1]} стор/день.'
        else:
            created_at = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                'INSERT INTO users (username, password_hash, created_at, daily_goal) VALUES (?, ?, ?, ?)',
                (username, pwd_hash, created_at, 20)
            )
            return f'✅ Профіль створено! Вітаємо, {username}! Денна ціль: 20 стор/день.'


class TestRegisterOrLogin:
    def test_new_user_registration(self, db_path):
        result = register_or_login_logic("alice", "secret", db_path)
        assert "Профіль створено" in result
        assert "alice" in result

    def test_existing_user_correct_password(self, db_with_user):
        result = register_or_login_logic("testuser", "pass123", db_with_user)
        assert "Вітаємо" in result
        assert "testuser" in result

    def test_existing_user_wrong_password(self, db_with_user):
        result = register_or_login_logic("testuser", "wrongpass", db_with_user)
        assert "Невірний пароль" in result

    def test_new_user_stored_in_db(self, db_path):
        register_or_login_logic("bob", "mypass", db_path)
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT username FROM users WHERE username = 'bob'").fetchone()
        assert row is not None

    def test_default_goal_is_20(self, db_path):
        register_or_login_logic("charlie", "pass", db_path)
        with sqlite3.connect(db_path) as conn:
            goal = conn.execute(
                "SELECT daily_goal FROM users WHERE username = 'charlie'"
            ).fetchone()[0]
        assert goal == 20


def log_reading_session_logic(username, book_title, pages_read, current_page,
                               minutes, mood, session_date, db_path) -> str:
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
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO activities (date, username, book_title, pages_read, last_page, minutes, mood) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, username, book_title, pages_read, current_page, minutes, mood)
        )
    return f"✅ Записано! Книга '{book_title}', сторінка {current_page}."


class TestLogReadingSession:
    def test_successful_log(self, db_with_user):
        result = log_reading_session_logic(
            "testuser", "кобзар", 10, 50, 20, "добрий", "2025-06-01", db_with_user
        )
        assert "✅" in result

    def test_zero_pages_rejected(self, db_with_user):
        result = log_reading_session_logic(
            "testuser", "кобзар", 0, 50, 20, "добрий", "", db_with_user
        )
        assert "Помилка" in result

    def test_zero_minutes_rejected(self, db_with_user):
        result = log_reading_session_logic(
            "testuser", "кобзар", 10, 50, 0, "добрий", "", db_with_user
        )
        assert "Помилка" in result

    def test_negative_pages_rejected(self, db_with_user):
        result = log_reading_session_logic(
            "testuser", "кобзар", -5, 50, 20, "добрий", "", db_with_user
        )
        assert "Помилка" in result

    def test_invalid_date_format(self, db_with_user):
        result = log_reading_session_logic(
            "testuser", "кобзар", 10, 50, 20, "добрий", "01-06-2025", db_with_user
        )
        assert "Невірний формат" in result

    def test_title_normalized_in_db(self, db_with_user):
        log_reading_session_logic(
            "testuser", "  великий гетсбі  ", 10, 50, 20, "добрий", "2025-06-01", db_with_user
        )
        with sqlite3.connect(db_with_user) as conn:
            title = conn.execute(
                "SELECT book_title FROM activities WHERE username = 'testuser' ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        assert title == "Великий Гетсбі"

    def test_session_stored_in_db(self, db_with_user):
        log_reading_session_logic(
            "testuser", "Дюна", 20, 100, 40, "чудовий", "2025-06-01", db_with_user
        )
        with sqlite3.connect(db_with_user) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM activities WHERE username = 'testuser' AND book_title = 'Дюна'"
            ).fetchone()[0]
        assert count == 1


def get_bookmark_logic(username: str, book_title: str, db_path: str) -> str:
    book_title = normalize_title(book_title)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_page, date FROM activities WHERE username = ? AND book_title = ? ORDER BY id DESC LIMIT 1",
            (username, book_title)
        )
        result = cursor.fetchone()
    if result:
        return f"📖 У книзі '{book_title}' ви зупинилися на сторінці {result[0]}."
    return f"🔍 Книга '{book_title}' ще не знайдена."


class TestGetBookmark:
    def test_existing_book(self, db_with_activities):
        result = get_bookmark_logic("testuser", "Кобзар", db_with_activities)
        assert "📖" in result
        assert "35" in result  # last_page з другої сесії

    def test_nonexistent_book(self, db_with_activities):
        result = get_bookmark_logic("testuser", "Незнайома книга", db_with_activities)
        assert "🔍" in result

    def test_title_normalized_for_lookup(self, db_with_activities):
        result = get_bookmark_logic("testuser", "  кобзар  ", db_with_activities)
        assert "📖" in result

    def test_unknown_user(self, db_with_activities):
        result = get_bookmark_logic("unknownuser", "Кобзар", db_with_activities)
        assert "🔍" in result

def analyze_reading_stats_logic(username: str, db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT pages_read, minutes FROM activities WHERE username = ?", (username,))
        data = cursor.fetchall()
        cursor.execute("SELECT daily_goal FROM users WHERE username = ?", (username,))
        goal_row = cursor.fetchone()
        goal = goal_row[0] if goal_row else 20

    if not data:
        return "📊 Ваша база даних порожня."

    total_pages = sum(r[0] for r in data)
    total_minutes = sum(r[1] for r in data)
    sessions = len(data)
    speed = round((total_pages / total_minutes) * 60, 1) if total_minutes > 0 else 0
    avg_per_session = round(total_pages / sessions, 1)

    status = '🌟 Активний читач' if total_pages > 100 else '🌱 Початківець'
    return (
        f"📈 АНАЛІТИКА для {username}:\n"
        f"📖 Всього прочитано сторінок: {total_pages}\n"
        f"⏱️ Загальний час: {total_minutes} хв\n"
        f"🔢 Кількість сесій: {sessions}\n"
        f"⚡ Середня швидкість: {speed} стор/год\n"
        f"📊 Середньо за сесію: {avg_per_session} стор\n"
        f"🎯 Ваша ціль: {goal} стор/день\n"
        f"🏆 Статус: {status}"
    )


class TestAnalyzeReadingStats:
    def test_empty_db_returns_message(self, db_with_user):
        result = analyze_reading_stats_logic("testuser", db_with_user)
        assert "порожня" in result

    def test_total_pages_correct(self, db_with_activities):
        result = analyze_reading_stats_logic("testuser", db_with_activities)
        assert "65" in result

    def test_session_count_correct(self, db_with_activities):
        result = analyze_reading_stats_logic("testuser", db_with_activities)
        assert "3" in result

    def test_beginner_status(self, db_with_activities):
        result = analyze_reading_stats_logic("testuser", db_with_activities)
        assert "Початківець" in result

    def test_active_reader_status(self, db_with_user):
        with sqlite3.connect(db_with_user) as conn:
            conn.execute(
                "INSERT INTO activities (date, username, book_title, pages_read, last_page, minutes, mood) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("2025-06-01", "testuser", "Велика книга", 150, 150, 200, "чудовий")
            )
        result = analyze_reading_stats_logic("testuser", db_with_user)
        assert "Активний читач" in result

    def test_speed_calculation(self, db_with_user):
        with sqlite3.connect(db_with_user) as conn:
            conn.execute(
                "INSERT INTO activities (date, username, book_title, pages_read, last_page, minutes, mood) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("2025-06-01", "testuser", "Тест книга", 60, 60, 60, "добрий")
            )
        result = analyze_reading_stats_logic("testuser", db_with_user)
        assert "60.0" in result

    def test_unknown_user_returns_empty(self, db_path):
        result = analyze_reading_stats_logic("nobody", db_path)
        assert "порожня" in result


def update_user_goal_logic(username: str, goal: int, db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE users SET daily_goal = ? WHERE username = ?", (goal, username))
    return f"✅ Ціль оновлено! Тепер ваша ціль: {goal} сторінок на день."


class TestUpdateUserGoal:
    def test_goal_updated_successfully(self, db_with_user):
        result = update_user_goal_logic("testuser", 50, db_with_user)
        assert "50" in result

    def test_goal_persisted_in_db(self, db_with_user):
        update_user_goal_logic("testuser", 45, db_with_user)
        with sqlite3.connect(db_with_user) as conn:
            goal = conn.execute(
                "SELECT daily_goal FROM users WHERE username = 'testuser'"
            ).fetchone()[0]
        assert goal == 45

    def test_returns_success_message(self, db_with_user):
        result = update_user_goal_logic("testuser", 25, db_with_user)
        assert "✅" in result


def get_user_books_logic(username: str, db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
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


class TestGetUserBooks:
    def test_no_books_returns_message(self, db_with_user):
        result = get_user_books_logic("testuser", db_with_user)
        assert "немає" in result

    def test_books_listed(self, db_with_activities):
        result = get_user_books_logic("testuser", db_with_activities)
        assert "Кобзар" in result
        assert "1984" in result

    def test_aggregated_pages_correct(self, db_with_activities):
        result = get_user_books_logic("testuser", db_with_activities)
        # Кобзар: 20 + 15 = 35 стор
        assert "35" in result

    def test_unknown_user_no_books(self, db_with_activities):
        result = get_user_books_logic("nobody", db_with_activities)
        assert "немає" in result


def get_daily_goal_logic(username: str, db_path: str) -> str:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT daily_goal FROM users WHERE username = ?", (username,))
        res = cursor.fetchone()
        goal = res[0] if res and res[0] else 30

        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT SUM(pages_read) FROM activities WHERE username = ? AND date LIKE ?",
            (username, f"{today}%")
        )
        read_today = cursor.fetchone()[0] or 0

    return json.dumps({"goal": goal, "read": read_today})


class TestGetDailyGoal:
    def test_returns_valid_json(self, db_with_user):
        result = get_daily_goal_logic("testuser", db_with_user)
        data = json.loads(result)
        assert "goal" in data
        assert "read" in data

    def test_goal_matches_user_setting(self, db_with_user):
        result = get_daily_goal_logic("testuser", db_with_user)
        data = json.loads(result)
        assert data["goal"] == 30  # встановлено у фікстурі

    def test_default_goal_for_unknown_user(self, db_path):
        result = get_daily_goal_logic("nobody", db_path)
        data = json.loads(result)
        assert data["goal"] == 30

    def test_read_today_is_integer(self, db_with_user):
        result = get_daily_goal_logic("testuser", db_with_user)
        data = json.loads(result)
        assert isinstance(data["read"], int)