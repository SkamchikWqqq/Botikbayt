import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "✅ Я онлайн!"

def run():
    port = int(os.environ.get("PORT", 8080))  # Получаем порт из переменной окружения
    app.run(host='0.0.0.0', port=port)  # Запускаем Flask на этом порту

Thread(target=run).start()
import asyncio

import aiosqlite

from aiogram import Bot, Dispatcher, types, F

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.filters import CommandStart

from aiogram.fsm.state import State, StatesGroup

from aiogram.fsm.context import FSMContext

# Изначальный список обязательных каналов
required_channels = [
    "@channel1",  # замените на свои каналы (открытые)
    "-1002415070098"  # замените на ID закрытого канала (например, для закрытого канала)
]

# Список администраторов
admins = ['cunpar', 'Ytrautr']

# Функция для проверки, является ли пользователь администратором
def is_admin(update: Update) -> bool:
    user_username = update.message.from_user.username
    return user_username in admins

# Функция для отображения кнопок
def show_channels(update: Update, context: CallbackContext) -> None:
    if not is_admin(update):
        update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return

    keyboard = [
        [InlineKeyboardButton("Добавить канал", callback_data='add_channel')],
        [InlineKeyboardButton("Удалить канал", callback_data='remove_channel')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите действие с каналами:", reply_markup=reply_markup)

# Функция для добавления канала
def add_channel(update: Update, context: CallbackContext) -> None:
    if not is_admin(update):
        update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return
    update.message.reply_text("Введите юзернейм канала для добавления (например, @example_channel) или ID для закрытого канала:")

# Функция для удаления канала
def remove_channel(update: Update, context: CallbackContext) -> None:
    if not is_admin(update):
        update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return
    update.message.reply_text("Введите юзернейм канала для удаления (например, @example_channel) или ID для закрытого канала:")

# Функция обработки введенного текста
def handle_text(update: Update, context: CallbackContext) -> None:
    if not is_admin(update):
        update.message.reply_text("❌ У вас нет прав для использования этой команды.")
        return

    user_input = update.message.text.strip()

    # Если пользователь хочет добавить канал
    if user_input.startswith('@') and update.message.text.startswith('@'):
        if user_input not in required_channels:
            required_channels.append(user_input)
            update.message.reply_text(f"Канал {user_input} добавлен в список обязательных.")
        else:
            update.message.reply_text(f"Канал {user_input} уже в списке обязательных.")
    
    # Если пользователь хочет добавить закрытый канал через ID
    elif user_input.startswith('-100'):
        if user_input not in required_channels:
            required_channels.append(user_input)
            update.message.reply_text(f"Закрытый канал с ID {user_input} добавлен в список обязательных.")
        else:
            update.message.reply_text(f"Закрытый канал с ID {user_input} уже в списке обязательных.")

    # Если пользователь хочет удалить канал
    elif user_input.startswith('@') or user_input.startswith('-100'):
        if user_input in required_channels:
            required_channels.remove(user_input)
            update.message.reply_text(f"Канал {user_input} удалён из списка обязательных.")
        else:
            update.message.reply_text(f"Канал {user_input} не найден в списке обязательных.")
    else:
        update.message.reply_text("Введите правильный юзернейм канала или ID канала, начиная с @ для открытых каналов и -100 для закрытых.")

# Функция проверки подписки
def check_subscription(update: Update, context: CallbackContext) -> bool:
    user_id = update.message.from_user.id
    for channel in required_channels:
        try:
            # Если канал открыт, используем get_chat_member
            if channel.startswith('@'):
                member = context.bot.get_chat_member(channel, user_id)
                if member.status not in ['member', 'administrator']:
                    return False
            # Если канал закрыт (ID), используем get_chat_member с ID
            elif channel.startswith('-100'):
                member = context.bot.get_chat_member(channel, user_id)
                if member.status not in ['member', 'administrator']:
                    return False
        except BadRequest:
            return False  # В случае ошибки (например, если канал не найден)
    return True

# Функция старта бота
def start(update: Update, context: CallbackContext) -> None:
    if check_subscription(update, context):
        update.message.reply_text("✅ Вы подписаны на все каналы, добро пожаловать!")
    else:
        update.message.reply_text("❌ Вам нужно подписаться на обязательные каналы, чтобы продолжить.")
        for channel in required_channels:
            update.message.reply_text(f"Подпишитесь на канал: {channel}")
    
    # Показываем кнопки добавления/удаления канала
    show_channels(update, context)

# Основной код запуска бота
def main():
    # Вставь сюда свой токен
    updater = Updater("8219425121:AAG5FZ3kIHE8XSVnjwthbkxYdXX-QDnFWYk", use_context=True)  # Вставь свой токен

    # Получаем диспетчера для добавления обработчиков
    dp = updater.dispatcher

    # Обработчик команды /start
    dp.add_handler(CommandHandler("start", start))

    # Обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    # Обработчик inline кнопок (для добавления/удаления канала)
    dp.add_handler(CallbackQueryHandler(add_channel, pattern='add_channel'))
    dp.add_handler(CallbackQueryHandler(remove_channel, pattern='remove_channel'))

    # Запускаем бота
    updater.start_polling()

    # Ожидаем завершения работы
    updater.idle()

if __name__ == '__main__':
    main()
