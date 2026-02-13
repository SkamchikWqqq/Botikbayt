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

TOKEN = "8508097253:AAG8cAoYMnASMXQBUGIzBr1PPANCz_HN9ao"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Админы (ИСПРАВЛЕНО НА USERNAME) ---
ADMINS = ["cunpar","Ytrautr"]

# --- Каналы для проверки (ТВОЙ КОД НЕ ИЗМЕНЕН) ---
CHANNEL_LINKS = [
    "https://t.me/+cH6hfRE443g5N2I0",
    "https://t.me/+yO5vZ2dUyRE3MzM0"
]

CHANNEL_IDS = [
    -1002647209017,
    -1002415070098
]

# --- Кнопка подписки ---
sub_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал 1", url=CHANNEL_LINKS[0])],
        [InlineKeyboardButton(text="📢 Подписаться на канал 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
    ]
)

# --- Проверка подписки ---
async def is_subscribed(user_id):

    channels = CHANNEL_IDS.copy()

    async with aiosqlite.connect("bot.db") as db:
        async with db.execute("SELECT channel_id FROM channels") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                channels.append(row[0])

    for channel in channels:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status in ["left", "kicked"]:
                return False

        except:
            return False

    return True


# =========================
# БАЗА ДАННЫХ
# =========================

async def init_db():

    async with aiosqlite.connect("bot.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER,
            link TEXT
        )
        """)

        await db.commit()


async def add_user(user_id):

    async with aiosqlite.connect("bot.db") as db:

        await db.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,)
        )

        await db.commit()


async def get_users():

    async with aiosqlite.connect("bot.db") as db:

        async with db.execute("SELECT user_id FROM users") as cursor:

            rows = await cursor.fetchall()

            return [row[0] for row in rows]


async def add_channel(channel_id, link):

    async with aiosqlite.connect("bot.db") as db:

        await db.execute(
            "INSERT INTO channels (channel_id, link) VALUES (?, ?)",
            (channel_id, link)
        )

        await db.commit()


async def get_channels():

    async with aiosqlite.connect("bot.db") as db:

        async with db.execute("SELECT id, channel_id, link FROM channels") as cursor:

            return await cursor.fetchall()


async def delete_channel(db_id):

    async with aiosqlite.connect("bot.db") as db:

        await db.execute(
            "DELETE FROM channels WHERE id = ?",
            (db_id,)
        )

        await db.commit()


# =========================
# FSM
# =========================

class BroadcastState(StatesGroup):

    text = State()


class AddChannelState(StatesGroup):

    link = State()
    id = State()


class DeleteChannelState(StatesGroup):

    id = State()


# =========================
# КЛАВИАТУРЫ
# =========================

def admin_kb():

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📨 Рассылка")],
            [KeyboardButton(text="➕ Добавить канал")],
            [KeyboardButton(text="📋 Список каналов")],
            [KeyboardButton(text="❌ Удалить канал")]
        ],
        resize_keyboard=True
    )


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: types.Message):

    await add_user(message.from_user.id)

    if not await is_subscribed(message.from_user.id):

        await message.answer(
            "Подпишитесь на каналы:",
            reply_markup=sub_kb
        )

        return

    if message.from_user.username in ADMINS:

        await message.answer(
            "Админ панель",
            reply_markup=admin_kb()
        )

    else:

        await message.answer("Вы подписаны")


# =========================
# ПРОВЕРКА ПОДПИСКИ
# =========================

@dp.callback_query(F.data == "check_sub")
async def check(callback: types.CallbackQuery):

    if await is_subscribed(callback.from_user.id):

        if callback.from_user.username in ADMINS:

            await callback.message.answer(
                "Админ панель",
                reply_markup=admin_kb()
            )

        else:

            await callback.message.answer("Подписка подтверждена")

    else:

        await callback.answer("Вы не подписаны", show_alert=True)


# =========================
# РАССЫЛКА
# =========================

@dp.message(F.text == "📨 Рассылка")
async def broadcast_start(message: types.Message, state: FSMContext):

    if message.from_user.username not in ADMINS:
        return

    await message.answer("Введите текст:")

    await state.set_state(BroadcastState.text)


@dp.message(BroadcastState.text)
async def broadcast_send(message: types.Message, state: FSMContext):

    users = await get_users()

    sent = 0

    for user in users:

        try:

            await bot.send_message(user, message.text)

            sent += 1

        except:
            pass

    await message.answer(f"Отправлено {sent}")

    await state.clear()


# =========================
# ДОБАВИТЬ КАНАЛ
# =========================

@dp.message(F.text == "➕ Добавить канал")
async def add_channel_start(message: types.Message, state: FSMContext):

    if message.from_user.username not in ADMINS:
        return

    await message.answer("Отправьте ссылку:")

    await state.set_state(AddChannelState.link)


@dp.message(AddChannelState.link)
async def add_channel_link(message: types.Message, state: FSMContext):

    await state.update_data(link=message.text)

    await message.answer("Отправьте ID канала:")

    await state.set_state(AddChannelState.id)


@dp.message(AddChannelState.id)
async def add_channel_id(message: types.Message, state: FSMContext):

    data = await state.get_data()

    await add_channel(int(message.text), data["link"])

    await message.answer("Канал добавлен")

    await state.clear()


# =========================
# СПИСОК КАНАЛОВ
# =========================

@dp.message(F.text == "📋 Список каналов")
async def list_channels(message: types.Message):

    if message.from_user.username not in ADMINS:
        return

    channels = await get_channels()

    if not channels:

        await message.answer("Нет каналов")

        return

    text = "Каналы:\n\n"

    for ch in channels:

        text += f"ID записи: {ch[0]}\n"
        text += f"Channel ID: {ch[1]}\n"
        text += f"Link: {ch[2]}\n\n"

    await message.answer(text)


# =========================
# УДАЛИТЬ КАНАЛ
# =========================

@dp.message(F.text == "❌ Удалить канал")
async def delete_channel_start(message: types.Message, state: FSMContext):

    if message.from_user.username not in ADMINS:
        return

    channels = await get_channels()

    if not channels:
        await message.answer("Нет каналов")
        return

    text = "Отправьте ID записи для удаления:\n\n"
    for ch in channels:
        text += f"{ch[0]} — {ch[2]}\n"

    await message.answer(text)

    await state.set_state(DeleteChannelState.id)


@dp.message(DeleteChannelState.id)
async def delete_channel_confirm(message: types.Message, state: FSMContext):

    await delete_channel(int(message.text))
    await message.answer("Канал удален")
    await state.clear()



# =========================
# ЗАПУСК
# =========================

async def main():

    await init_db()

    await dp.start_polling(bot)


asyncio.run(main())
