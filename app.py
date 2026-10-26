# -*- coding: utf-8 -*-
"""
KENZO🇺🇿 (@Kenzocheatbot) — majburiy obunali menyu boti.

keys_bot.py bilan BITTA Render xizmatida ishlaydi (alohida xizmat ochish shart emas).
Token: Render'dagi KENZO_TOKEN o'zgaruvchisi (yoki kenzo_token.txt fayli).
Ulash: https://<manzil>.onrender.com/kenzo-setwebhook
"""
import os
import json
import hashlib

import telebot
from flask import Flask, request, abort

BASE = os.path.dirname(os.path.abspath(__file__))


def _read(name, default=""):
    try:
        with open(os.path.join(BASE, name), encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return default


TOKEN = (os.environ.get("KENZO_TOKEN", "") or os.environ.get("BOT_TOKEN", "")).strip() or _read("kenzo_token.txt")

# ----------------------------------------------------------------------
# SOZLAMALAR
# ----------------------------------------------------------------------
# Majburiy obuna kanallari: (kanal, havola)
CHANNELS = [
    ("@jaggerN1_kenzo", "https://t.me/jaggerN1_kenzo"),
    ("@elvinorg", "https://t.me/elvinorg"),
]
LINK_CHIT = "https://t.me/jaggerN1_kenzo"      # 🎮 Chit o'rnatish
LINK_CHANNEL = "https://t.me/jaggerN1_kenzo"   # 📢 Kanalimiz
LINK_VIDEO = "https://t.me/chit_tutorial/26"   # 📹 O'rnatish videosi
LINK_ADMIN = "https://t.me/Jagerrn1"           # 💬 Admin bilan aloqa

WELCOME = ("Assalomu alaykum! <b>KENZO🇺🇿</b> botiga xush kelibsiz.\n\n"
           "Quyidagi tugmalardan birini tanlang 👇")

kbot = telebot.TeleBot(TOKEN or "0:TEST", parse_mode="HTML", threaded=False)


# ----------------------------------------------------------------------
# Tugmalar. "style" maydoni Telegram'da tugma rangini beradi:
#   danger = qizil, primary = ko'k, success = yashil (sariq rang yo'q).
# Eski Telegram ilovalari rangni ko'rsatmasa, tugma oddiy chiqadi, ishlashiga zarar yo'q.
# ----------------------------------------------------------------------
def menu_markup():
    return json.dumps({
        "keyboard": [
            [{"text": "🎮 Chit o‘rnatish", "style": "danger"},
             {"text": "📢 Kanalimiz", "style": "primary"}],
            [{"text": "📹 O‘rnatish videosi", "style": "success"},
             {"text": "💬 Admin bilan aloqa"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
    })


def link_markup(label, url, style):
    return json.dumps({"inline_keyboard": [[{"text": label, "url": url, "style": style}]]})


def gate_markup():
    rows = [[{"text": f"📢 {chat}", "url": url, "style": "primary"}] for chat, url in CHANNELS]
    rows.append([{"text": "✅ Tekshirish", "callback_data": "kz_chk", "style": "success"}])
    return json.dumps({"inline_keyboard": rows})


# ----------------------------------------------------------------------
# Obuna tekshiruvi
# ----------------------------------------------------------------------
def is_member(chat, uid):
    try:
        m = kbot.get_chat_member(chat, uid)
        return m.status in ("member", "administrator", "creator", "restricted")
    except Exception:
        return False   # bot kanalda admin bo'lmasa ham shu yerga tushadi


def joined_all(uid):
    return all(is_member(chat, uid) for chat, _ in CHANNELS)


def send_gate(chat_id):
    kbot.send_message(
        chat_id,
        "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, "
        "so'ng «✅ Tekshirish» tugmasini bosing.",
        reply_markup=gate_markup())


def send_menu(chat_id):
    kbot.send_message(chat_id, WELCOME, reply_markup=menu_markup())


# ----------------------------------------------------------------------
# Handlerlar
# ----------------------------------------------------------------------
@kbot.message_handler(commands=["start"])
def on_start(m):
    if joined_all(m.from_user.id):
        send_menu(m.chat.id)
    else:
        send_gate(m.chat.id)


@kbot.callback_query_handler(func=lambda c: c.data == "kz_chk")
def on_check(c):
    if joined_all(c.from_user.id):
        kbot.answer_callback_query(c.id, "✅ Obuna tasdiqlandi")
        send_menu(c.message.chat.id)
    else:
        kbot.answer_callback_query(
            c.id, "Hali hamma kanallarga obuna bo'lmagansiz. Obuna bo'lib, qayta bosing.",
            show_alert=True)


@kbot.message_handler(func=lambda m: True, content_types=["text"])
def on_text(m):
    if not joined_all(m.from_user.id):
        return send_gate(m.chat.id)
    t = m.text or ""
    if t.startswith("🎮"):
        kbot.send_message(m.chat.id, "🎮 Chitni o'rnatish uchun kanalga o'ting:",
                          reply_markup=link_markup("🎮 Chit o‘rnatish", LINK_CHIT, "danger"))
    elif t.startswith("📢"):
        kbot.send_message(m.chat.id, "📢 Rasmiy kanalimiz:",
                          reply_markup=link_markup("📢 Kanalga o‘tish", LINK_CHANNEL, "primary"))
    elif t.startswith("📹"):
        kbot.send_message(m.chat.id, "📹 O'rnatish videosi:",
                          reply_markup=link_markup("📹 Videoni ko‘rish", LINK_VIDEO, "success"))
    elif t.startswith("💬"):
        kbot.send_message(m.chat.id, "💬 Savol bo'lsa, adminga yozing:",
                          reply_markup=link_markup("💬 Adminga yozish", LINK_ADMIN, "primary"))
    else:
        send_menu(m.chat.id)


# ----------------------------------------------------------------------
# Webhook (keys_bot.py dagi Flask ilovasiga ulanadi)
# ----------------------------------------------------------------------
SECRET = hashlib.sha256(("kenzo" + (TOKEN or "x")).encode()).hexdigest()[:24]


def webhook(secret):
    if secret != SECRET:
        abort(403)
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    try:
        kbot.process_new_updates([update])
    except Exception as e:   # bot yiqilmasin
        print("kenzo update error:", repr(e))
    return "ok"


def set_webhook():
    url = f"https://{request.host}/kenzo/{SECRET}"
    kbot.remove_webhook()
    ok = kbot.set_webhook(url=url)
    return f"kenzo webhook: {ok}"


def register(app):
    """Token bo'lsa, marshrutlarni Flask ilovasiga qo'shadi."""
    if not TOKEN:
        print("KENZO_TOKEN yo'q, kenzo bot o'chiq")
        return False
    app.add_url_rule("/kenzo/<secret>", "kenzo_hook", webhook, methods=["POST"])
    app.add_url_rule("/kenzo-setwebhook", "kenzo_set", set_webhook)
    return True


# ----------------------------------------------------------------------
# Flask ilovasi (gunicorn app:app)
# ----------------------------------------------------------------------
app = Flask(__name__)
register(app)


@app.route("/")
def index():
    return "KENZO🇺🇿 bot ishlayapti"
