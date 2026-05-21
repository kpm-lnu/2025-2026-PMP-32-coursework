# 📚 Reading Intellect Agent

# Встановлення і запуск програми 

Крок 1 — Завантаж код з GitHub
Зайди на  та натисни зелену кнопку "Code" → "Download ZIP". Розпакуй архів.

Крок 2 — Відкрий папку у PyCharm
File → Open → обери розпаковану папку

Крок 3 — Встанови бібліотеки
У терміналі PyCharm виконай:
pip install streamlit groq mcp fastmcp chromadb sentence-transformers wikipediaapi pandas pytest python-dotenv

Крок 4 — Налаштуй API ключ
Зареєструйся на console.groq.com та отримай безкоштовний API ключ. Створи файл .env у папці проєкту та встав:
GROQ_API_KEY=твій_ключ

Крок 5 — Запусти застосунок
streamlit run app.py

Застосунок відкриється у браузері за адресою http://localhost:8501

# 🧪 Тестування

pytest test_reading_analytics.py -v
Запускає 49 юніт-тестів які покривають всі основні функції системи.

# 👤 Автор

Ониськів Юліанна Ігорівна, студентка групи ПМП-32, Львівський національний університет імені Івана Франка, Факультет прикладної математики та інформатики, 2026.