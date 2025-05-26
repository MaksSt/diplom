import os
import telebot
import requests
import json

# Файлы для хранения заявок и запросов
APPLICATIONS_FILE = 'output/applications.json'
USER_QUERIES_FILE = 'output/user_queries.json'

def save_json_file(filename, data):
    #print(f"Saving data to {filename}: {data}") # Debug print
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    #print(f"Data saved to {filename}") # Debug print

def load_json_file(filename):
    #print(f"Loading data from {filename}") # Debug print
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            #print(f"Data loaded from {filename}: {loaded_data}") # Debug print
            return loaded_data
    #print(f"{filename} not found, returning empty list") # Debug print
    return []

def save_application_data(application_data, user_id):
    applications = load_json_file(APPLICATIONS_FILE)
    application_data['user_id'] = user_id  # Добавляем user_id в данные заявки
    applications.append(application_data)
    save_json_file(APPLICATIONS_FILE, applications)

def log_user_query(query, user_id, response_text):
    queries = load_json_file(USER_QUERIES_FILE)
    queries.append({"query": query, "user_id": user_id, "response": response_text})
    save_json_file(USER_QUERIES_FILE, queries)

from telebot import types

# Токены и ключи API
TELEGRAM_TOKEN = 'ТОКЕН БОТА СУДА'
CHAD_API_KEY = 'АПИ КЛЮЧ'
CHAD_API_URL = 'https://ask.chadgpt.ru/api/public/gpt-4o-mini'

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Получение абсолютного пути к prompts.json
current_directory = os.path.dirname(os.path.abspath(__file__))
prompts_path = os.path.join(current_directory, 'prompts.json')

# Загрузка заранее подготовленных определений из файла prompts.json
if os.path.exists(prompts_path):
    with open(prompts_path, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
else:
    prompts = []  # Если файл не найден

# Функция для отправки запроса к ChadGPT API
def get_chadgpt_response(prompt, history):
    request_json = {
        "message": prompt,
        "api_key": CHAD_API_KEY,
        "history": history  # Используем историю только из prompts.json
    }
    response = requests.post(url=CHAD_API_URL, json=request_json)

    if response.status_code != 200:
        return {"error": f'Ошибка! Код http-ответа: {response.status_code}'}
    resp_json = response.json()
    if resp_json['is_success']:
        return {
            "message": resp_json['response'],
            "used_words": resp_json['used_words_count']
        }
    else:
        return {"error": resp_json['error_message']}

# Переменные для хранения данных заявки
application_name = None
application_theme = None
application_phone = None
ожидание_поля_заявки = None # состояние ожидания поля заявки

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    application_button = types.KeyboardButton("Заявка")
    markup.add(application_button)
    bot.reply_to(message, "Привет! Задай вопрос, или нажмите кнопку 'Заявка' для подачи заявки на экскурсию в музей.", reply_markup=markup, parse_mode='Markdown')

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global ожидание_поля_заявки, application_name, application_theme, application_phone # Глобальные переменные для хранения данных заявки
    user_input = message.text
    # application_data = {} # Убрали объявление application_data здесь

    # log_user_query(user_input, message.from_user.id, None) # Логируем запрос пользователя с user_id и None в качестве ответа

    if message.text.lower() == "заявка":
        bot.send_message(message.chat.id, "Введите ваше имя:") # Запрашиваем имя
        ожидание_поля_заявки = "имя" # Устанавливаем состояние ожидания имени
    elif ожидание_поля_заявки == "имя": # Если ожидаем имя
        application_name = user_input.strip() # Получаем имя
        bot.send_message(message.chat.id, "Введите тему экскурсии (История колледжа, Промышленное развитие региона, Восстановление после пожара, Достижения выпускников, Современные технологии, Интерактивный контент):") # Запрашиваем тему
        ожидание_поля_заявки = "тема" # Устанавливаем состояние ожидания темы
    elif ожидание_поля_заявки == "тема": # Если ожидаем тему
        application_theme = user_input.strip() # Получаем тему
        bot.send_message(message.chat.id, "Введите ваш телефон:") # Запрашиваем телефон
        ожидание_поля_заявки = "телефон" # Устанавливаем состояние ожидания телефона
    elif ожидание_поля_заявки == "телефон": # Если ожидаем телефон
        application_phone = user_input.strip() # Получаем телефон
        # Собираем данные заявки в словарь
        application_data = {
            'name': application_name,
            'theme': application_theme,
            'phone': application_phone
        }
        save_application_data(application_data, message.from_user.id) # Сохраняем данные заявки с user_id
        bot.reply_to(message, "Заявка принята") # Отвечаем пользователю о принятии заявки
        ожидание_поля_заявки = None # Сбрасываем состояние ожидания
        # Обнуляем переменные для следующей заявки
        application_name = None
        application_theme = None
        application_phone = None
    else: # Если не ожидаем заявку
        bot.reply_to(message, "Запрос обрабатывается ") # Отвечаем пользователю о начале обработки запроса
        # Отправляем запрос к ChadGPT API с историей из prompts.json
        response = get_chadgpt_response(user_input, prompts)
        if 'error' in response:
            bot.reply_to(message, response['error']) # Отвечаем пользователю об ошибке
            log_user_query(user_input, message.from_user.id, None) # Логируем запрос пользователя и None в качестве ответа ассистента с user_id
        else:
            bot.reply_to(message, f"{response['message']}") # Отвечаем пользователю ответом от ChadGPT
            log_user_query(user_input, message.from_user.id, response['message']) # Логируем запрос пользователя и ответ ассистента с user_id

import threading
import time

def scan_applications():
    print("Scanning applications...") # Debug print
    applications = load_json_file(APPLICATIONS_FILE)
    updated = False
    for application in applications:
        if 'comments' in application and isinstance(application['comments'], list): # Проверка на наличие comments и что это список
            for comment in application['comments']:
                if isinstance(comment, dict) and 'text' in comment and 'send' not in comment: # Проверка структуры комментария
                    text_to_send = comment['text']
                    user_id = application.get('user_id') # Безопасное получение user_id
                    if user_id:
                        bot.send_message(user_id, text_to_send)
                        comment['send'] = True
                        updated = True
                        print(f"Sent message to user {user_id}: {text_to_send}") # Лог отправки
                    else:
                        print(f"User ID not found for application: {application}") # Лог ошибки, если нет user_id
        if updated:
            save_json_file(APPLICATIONS_FILE, applications) # Сохраняем изменения в файл
    print("Applications scanning complete.") # Debug print

def schedule_scan_applications():
    def run_scan():
        scan_applications()
        schedule_scan_applications() # Планируем следующий вызов через час

    timer = threading.Timer(3600, run_scan) # 3600 секунд = 1 час
    timer.start()
    print("Scheduled next applications scan in 1 hour.") # Лог планирования

if __name__ == '__main__':
    scan_applications()
    schedule_scan_applications() # Запускаем планирование сканирования
    bot.polling()
