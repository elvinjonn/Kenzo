
# -*- coding: utf-8 -*-
import os
import json
import hashlib

import telebot
from flask import Flask, request, abort

# TOKEN
TOKEN = (
    os.environ.get("KENZO_TOKEN", "")
    or os.environ.get("BOT_TOKEN", "")
).strip()

if not TOKEN:
    raise RuntimeError("Render Environment Variables ichiga BOT_TOKEN kiriting")

# BOT
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=False)
app = Flask(__name__)

# MAJBURIY OBUNA
CHANNELS = [
    ("@jaggerN1_kenzo", "https://t.me/jaggerN1_kenzo"),
    ("@elvinorg", "https://t.me/elvinorg"),
]

# HAVOLALAR
LINK_CHIT = "https://t.me/jaggerN1_kenzo"
LINK_CHANNEL = "https://t.me/jaggerN1_kenzo"
LINK_VIDEO = "https://t.me/chit_tutorial/26"
LINK_ADMIN = "https://t.me/Jagerrn1"

WELCOME = (
    "Assalomu alaykum! <b>KENZO🇺🇿</b> botiga xush kelibsiz.\n\n"
    "Quyidagi rangli tugmalardan birini tanlang 👇"
)

# ASOSIY RANGLI TUGMALAR
def menu_markup():
    return json.dumps({
        "keyboard": [
            [
                {"text": "🎮 Chit o‘rnatish", "style": "danger"},
                {"text": "📢 Kanalimiz", "style": "primary"}
            ],
            [
                {"text": "📹 O‘rnatish videosi", "style": "success"},
                {"text": "💬 Admin bilan aloqa", "style": "primary"}
            ]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }, ensure_ascii=False)


# HAVOLA TUGMALARI
def link_markup(label, url, style="primary"):
    return json.dumps({
        "inline_keyboard": [[
            {"text": label, "url": url, "style": style}
        ]]
    }, ensure_ascii=False)


# OBUNA TUGMALARI
def gate_markup():
    rows = [
        [{"text": "📢 Kanal 1", "url": CHANNELS[0][1],
          "style": "primary"}],
        [{"text": "📢 Kanal 2", "url": CHANNELS[1][1],
          "style": "primary"}],
        [{"text": "✅ Tekshirish", "callback_data": "kz_chk",
          "style": "success"}]
    ]
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)


# OBUNANI TEKSHIRISH
def is_member(channel, user_id):
    try:
        member = bot.get_chat_member(channel, user_id)
        return member.status in (
            "member", "administrator", "creator", "restricted"
        )
    except Exception as error:
        print("Obuna tekshirish xatosi:", repr(error))
        return False


def joined_all(user_id):
    return all(is_member(channel, user_id) for channel, _ in CHANNELS)


def send_gate(chat_id):
    bot.send_message(
        chat_id,
        "Botdan foydalanish uchun ikkala kanalga obuna bo‘ling 👇",
        reply_markup=gate_markup()
    )


def send_menu(chat_id):
    bot.send_message(
        chat_id,
        WELCOME,
        reply_markup=menu_markup()
    )


# START
@bot.message_handler(commands=["start"])
def start(message):
    if joined_all(message.from_user.id):
        send_menu(message.chat.id)
    else:
        send_gate(message.chat.id)


# OBUNANI QAYTA TEKSHIRISH
@bot.callback_query_handler(func=lambda call: call.data == "kz_chk")
def check_subscription(call):
    if joined_all(call.from_user.id):
        bot.answer_callback_query(
            call.id, "✅ Obuna tasdiqlandi!"
        )
        send_menu(call.message.chat.id)
    else:
        bot.answer_callback_query(
            call.id,
            "Avval ikkala kanalga ham obuna bo‘ling!",
            show_alert=True
        )


# ASOSIY MENYU
@bot.message_handler(content_types=["text"])
def menu(message):
    if not joined_all(message.from_user.id):
        send_gate(message.chat.id)
        return

    text = message.text or ""

    if text.startswith("🎮"):
        bot.send_message(
            message.chat.id,
            "🎮 Chit o‘rnatish uchun:",
            reply_markup=link_markup(
                "🎮 Chit o‘rnatish", LINK_CHIT, "danger"
            )
        )

    elif text.startswith("📢"):
        bot.send_message(
            message.chat.id,
            "📢 Rasmiy kanalimiz:",
            reply_markup=link_markup(
                "📢 Kanalga o‘tish", LINK_CHANNEL, "primary"
            )
        )

    elif text.startswith("📹"):
        bot.send_message(
            message.chat.id,
            "📹 O‘rnatish videosi:",
            reply_markup=link_markup(
                "📹 Videoni ko‘rish", LINK_VIDEO, "success"
            )
        )

    elif text.startswith("💬"):
        bot.send_message(
            message.chat.id,
            "💬 Admin bilan aloqa:",
            reply_markup=link_markup(
                "💬 Adminga yozish", LINK_ADMIN, "primary"
            )
        )

    else:
        send_menu(message.chat.id)


# WEBHOOK
SECRET = hashlib.sha256(
    ("kenzo" + TOKEN).encode()
).hexdigest()[:24]


@app.route("/")
def index():
    return "KENZO bot ishlayapti!"


@app.route("/kenzo-setwebhook")
def set_webhook():
    result = bot.set_webhook(
        url=f"https://{request.host}/kenzo/{SECRET}"
    )
    return f"Webhook o‘rnatildi: {result}"


@app.route("/kenzo/<secret>", methods=["POST"])
def webhook(secret):
    if secret != SECRET:
        abort(403)

    update = telebot.types.Update.de_json(
        request.get_data().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
