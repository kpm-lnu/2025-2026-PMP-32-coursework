# інструкція запуску

 Файли ключів зберігаються в `.env`.

1) Вимоги
- Python 3.10+ (рекомендовано 3.11)
- Системні інструменти: `git`, `python`, `pip`

2) Встановлення

```bash
# склонуйте репозиторій

# Створити віртуальне середовище
python3.11 -m venv .venv
source .venv/bin/activate

# Оновити pip
pip install --upgrade pip setuptools wheel

# Встановити залежності
pip install -r requirements.txt
```

3) Налаштувати `.env`
- Скопіюйте `.env.template` → `.env` і підставте свої ключі.


5) Запуск 

streamlit run app.py

