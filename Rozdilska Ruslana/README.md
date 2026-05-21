# Курсова робота — Роздільська Руслана, ПМп-32

**Тема:** Розробка інформаційних систем підтримки музейної діяльності на основі відкритого програмного забезпечення

## Як запустити

### 1. Встановити XAMPP
- Завантажити з https://www.apachefriends.org/
- Встановити як звичайну програму
- Запустити XAMPP Control Panel
- Натиснути Start навпроти Apache і MySQL

### 2. Встановити Omeka Classic
- Завантажити з https://omeka.org/classic/download/
- Розпакувати архів, перейменувати папку на `omeka`
- Скопіювати у `C:\xampp\htdocs\omeka`

### 3. Створити базу даних
- Відкрити http://localhost/phpmyadmin
- Зліва натиснути New
- Назва: `omeka_museum`, кодування: `utf8_unicode_ci`
- Натиснути Створити

### 4. Імпортувати базу даних
- У phpMyAdmin зліва обрати `omeka_museum`
- Вкладка Імпорт → Вибрати файл → обрати `omeka_museum.sql` з цієї папки
- Натиснути Import

### 5. Налаштувати підключення до БД
Відкрити `C:\xampp\htdocs\omeka\db.ini` у блокноті і прописати:

host     = "localhost"
username = "root"
password = ""
dbname   = "omeka_museum"
prefix   = "omeka_"
charset  = "utf8"
port     = ""

### 6. Встановити плагіни
- Скопіювати плагіни DailyItem, DonateButton, Feedback, ItemViews, QRCode ( у `C:\xampp\htdocs\omeka\plugins\`)
- Відкрити http://localhost/omeka/admin → Plugins
- Натиснути Install навпроти кожного плагіна

### 7. Відкрити сайт
- Публічна частина: http://localhost/omeka
- Адмінпанель: http://localhost/omeka/admin

## Telegram-бот
Встановити залежності і запустити:
pip install pyTelegramBotAPI requests
python bot_telegram.py

## Склад репозиторію
- `DailyItem/`, `DonateButton/`, `Feedback/`, `ItemViews/`, `QRCode/` — 5 авторських PHP-плагінів для Omeka
- `bot_telegram.py` — Telegram-бот на Python
- `omeka_museum.sql` — дамп бази даних з експонатами