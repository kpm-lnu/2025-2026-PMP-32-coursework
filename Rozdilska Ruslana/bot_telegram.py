import telebot
import requests
import random
from telebot import types

bot = telebot.TeleBot('8819932296:AAGPQFZzh_q8YhIi9Oa7fuPDadsnNELPhsQ')
MUSEUM_URL = "http://192.168.0.227/omeka/"

user_waiting_search = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    response = requests.get(MUSEUM_URL + "api/items?per_page=1")
    total = response.headers.get('Omeka-Total-Results', '?')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('🏛 Каталог', '🔍 Пошук')
    markup.row('🌟 Експонат дня', '🖼 Виставки')
    markup.row('📞 Контакти', '🎟 Квитки')
    markup.row('📝 Відгук', '💚 Донат')

    bot.send_message(
        message.chat.id,
        "Вітаю! Я віртуальний гід музею. 🎨\n"
        "У нашій колекції зараз " + str(total) + " експонатів.\n\n"
        "Оберіть потрібний розділ у меню:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_messages(message):

    if message.text == '🏛 Каталог':
        response = requests.get(MUSEUM_URL + "api/items?per_page=1")
        total = response.headers.get('Omeka-Total-Results', '?')
        bot.send_message(message.chat.id, "У нашій колекції " + str(total) + " експонатів.\nПереглянути: " + MUSEUM_URL + "items/browse")

    elif message.text == '🌟 Експонат дня':
        response_total = requests.get(MUSEUM_URL + "api/items?per_page=1")
        total = int(response_total.headers.get('Omeka-Total-Results', 1))
        random_page = random.randint(1, total)
        response = requests.get(MUSEUM_URL + "api/items?per_page=1&page=" + str(random_page))
        items = response.json()

        if isinstance(items, list) and len(items) > 0 and isinstance(items[0], dict):
            item = items[0]
            title = ''
            description = ''
            for el in item['element_texts']:
                if el['element']['name'] == 'Title':
                    title = el['text']
                if el['element']['name'] == 'Description':
                    description = el['text']

            text = "🌟 Експонат дня!\n\n"
            text += "Назва: " + title + "\n"
            text += "Опис: " + description + "\n\n"
            text += "Детальніше: " + MUSEUM_URL + "items/show/" + str(item['id'])
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "Не вдалося отримати експонат.")

    elif message.text == '🔍 Пошук':
        user_waiting_search[message.chat.id] = True
        bot.send_message(message.chat.id, "Введіть назву або ключове слово для пошуку:")

    elif message.chat.id in user_waiting_search and user_waiting_search[message.chat.id]:
        user_waiting_search[message.chat.id] = False
        query = message.text

        response = requests.get(MUSEUM_URL + "api/items?search=" + query + "&per_page=3")
        items = response.json()

        if isinstance(items, list) and len(items) > 0:
            bot.send_message(message.chat.id, "Знайдено результатів: " + str(len(items)))
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = ''
                for el in item['element_texts']:
                    if el['element']['name'] == 'Title':
                        title = el['text']
                bot.send_message(message.chat.id, "🏺 " + title + "\n" + MUSEUM_URL + "items/show/" + str(item['id']))
        else:
            bot.send_message(message.chat.id, "Нічого не знайдено за запитом: " + query)

    elif message.text == '🖼 Виставки':
        text = ("Поточні виставки:\n\n"
                "1️⃣ «Мистецтво крізь віки» (Постійна експозиція)\n"
                "2️⃣ «Скарби нації» (До 30 листопада)\n\n"
                "Слідкуйте за оновленнями на сайті!")
        bot.send_message(message.chat.id, text)

    elif message.text == '📞 Контакти':
        text = ("📍 Адреса: вул. Музейна, 1, Київ\n"
                "🕒 Графік роботи: Вт-Нд з 10:00 до 18:00 (Пн - вихідний)\n"
                "📞 Гаряча лінія: +38 (0800) 11-22-33\n"
                "📧 Email: info@museum.ua")
        bot.send_message(message.chat.id, text)

    elif message.text == '🎟 Квитки':
        text = ("🎟 Вартість відвідування:\n"
                "- Дорослий: 150 грн\n"
                "- Студентський/Дитячий: 70 грн\n\n"
                "📸 Фотографувати можна, але БЕЗ спалаху!")
        bot.send_message(message.chat.id, text)

    elif message.text == '📝 Відгук':
        bot.send_message(message.chat.id, "Залиште відгук на сайті:\n" + MUSEUM_URL + "feedback")

    elif message.text == '💚 Донат':
        bot.send_message(message.chat.id, "Дякуємо за підтримку!\nhttps://send.monobank.ua/jar/1234567890")

    else:
        bot.send_message(message.chat.id, "Будь ласка, скористайтеся кнопками меню нижче. 🤖")

print("Бот запущений!")
bot.remove_webhook()
bot.infinity_polling()
