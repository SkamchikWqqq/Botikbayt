import telebot
import json
import os
from telebot import types
from flask import Flask, request

TOKEN = "7917190360:AAFxfFYsEsx9kQiPbh7MtZ6N7HLZcSPQRNs"
ADMIN_ID = 130231824

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
server = Flask(__name__)

CHANNELS_FILE = "channels.json"


def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=4)


def check_subscription(user_id):
    channels = load_channels()
    for ch in channels:
        try:
            info = bot.get_chat_member(ch["id"], user_id)
            if info.status not in ["member", "creator", "administrator"]:
                return False
        except:
            return False
    return True


def generate_keyboard():
    channels = load_channels()
    kb = types.InlineKeyboardMarkup()
    for ch in channels:
        kb.add(types.InlineKeyboardButton(
            f"📢 Подписаться на {ch['name']}",
            url=ch['invite']
        ))
    kb.add(types.InlineKeyboardButton("✅ Я подписался", callback_data="check"))
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    channels = load_channels()

    text = "📢 Для использования бота необходимо подписаться на наши каналы:\n\n"
    for ch in channels:
        text += f"• {ch['name']}\n"

    text += "\nПосле подписки нажмите кнопку «✅ Я подписался»"

    bot.send_message(message.chat.id, text, reply_markup=generate_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "check")
def check(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Подписка подтверждена")
        bot.send_message(call.from_user.id, "🔥 Дождитесь ответа поддержки.")
    else:
        bot.answer_callback_query(call.id, "❌ Нет подписки на 1+ каналов")
        bot.send_message(call.from_user.id, "❌ Подпишитесь на все каналы!", reply_markup=generate_keyboard())


# ================= ADMIN PANEL ================= #

@bot.message_handler(commands=["admin"])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Добавить канал", "➖ Удалить канал")
    kb.add("📋 Посмотреть каналы")
    bot.send_message(message.chat.id, "🔐 Админ панель", reply_markup=kb)


@bot.message_handler(func=lambda m: m.text == "📋 Посмотреть каналы")
def list_ch(message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = load_channels()
    if not channels:
        bot.send_message(message.chat.id, "❌ Нет каналов")
    else:
        text = "📌 Каналы:\n"
        for ch in channels:
            text += f"{ch['name']} — {ch['id']}\n"
        bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "➕ Добавить канал")
def add_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "📨 Отправьте invite-ссылку канала:")
    bot.register_next_step_handler(message, add_channel)


def add_channel(message):
    if message.from_user.id != ADMIN_ID:
        return

    invite = message.text.strip()
    try:
        chat = bot.get_chat(invite)
        ch_id = chat.id
        ch_name = chat.title or chat.username or "Канал"

        channels = load_channels()
        for c in channels:
            if c["id"] == ch_id:
                bot.send_message(message.chat.id, "⚠️ Этот канал уже есть!")
                return

        channels.append({"id": ch_id, "name": ch_name, "invite": invite})
        save_channels(channels)

        bot.send_message(message.chat.id,
                         f"✅ Добавлено:\n📌 {ch_name}\n🆔 {ch_id}")
    except:
        bot.send_message(message.chat.id,
                         "❌ Ошибка! Приглашение неверное или бот не админ!")


@bot.message_handler(func=lambda m: m.text == "➖ Удалить канал")
def remove_start(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🔻 Введите ID удаляемого канала:")
    bot.register_next_step_handler(message, remove_channel)


def remove_channel(message):
    if message.from_user.id != ADMIN_ID:
        return

    ch_id = message.text.strip()
    channels = load_channels()
    updated = [c for c in channels if str(c["id"]) != ch_id]

    if len(updated) != len(channels):
        save_channels(updated)
        bot.send_message(message.chat.id, "🗑 Канал удалён!")
    else:
        bot.send_message(message.chat.id, "❌ Канала с таким ID нет!")


# ============ WEBHOOK (Render) ============ #

@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_json())])
    return "OK", 200


@server.route("/", methods=["GET"])
def index():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    return "Webhook set", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
