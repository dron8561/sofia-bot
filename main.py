import os
import time
import threading
import sqlite3
from flask import Flask, request, jsonify
import requests
from openai import OpenAI
from bad_words import BAD_WORDS

# === Конфигурация ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = "София"
PORT = int(os.environ.get("PORT", 8000))

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("⚠️ Не установлены TELEGRAM_TOKEN и OPENAI_API_KEY. Установи переменные окружения.")

tg_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

# === Flask ===
app = Flask(__name__)

# === SQLite база памяти с потокобезопасностью ===
DB_PATH = "memory.db"
db_lock = threading.Lock()

def init_db():
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            user_id INTEGER,
            role TEXT,
            content TEXT,
            ts INTEGER
        )
        """)
        conn.commit()
        conn.close()

init_db()

def append_memory(user_id: int, role: str, content: str):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chats (user_id, role, content, ts) VALUES (?, ?, ?, ?)",
            (user_id, role, content, int(time.time()))
        )
        # оставляем только последние 20 сообщений
        cur.execute(
            "DELETE FROM chats WHERE rowid IN "
            "(SELECT rowid FROM chats WHERE user_id=? ORDER BY ts DESC LIMIT -1 OFFSET 20)",
            (user_id,)
        )
        conn.commit()
        conn.close()

def get_history(user_id: int):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT role, content FROM chats WHERE user_id=? ORDER BY ts ASC", (user_id,))
        rows = cur.fetchall()
        conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

# === Отправка сообщений в Telegram с обработкой ошибок ===
def telegram_send(chat_id: int, text: str):
    url = f"{tg_api}/sendMessage"
    try:
        response = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
        if response.status_code != 200:
            print(f"Ошибка Telegram API: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")

# === Личность Софии ===
SYSTEM_PROMPT = (
    f"Ты — {BOT_NAME}, милая, флиртующая собеседница. "
    "Говоришь легко, с теплом и улыбкой. Можно немного игриво, но без непристойностей. "
    "Избегай откровенных тем. Поддерживай позитив и нежность 💖"
)

# === Webhook обработчик ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if "message" not in data:
        return jsonify({"ok": True})

    msg = data["message"]
    chat_id = msg["chat"]["id"]
    user_id = msg["from"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        telegram_send(chat_id, "Я пока понимаю только текст 💬")
        return jsonify({"ok": True})

    # фильтр неприемлемых слов
    if any(bad in text.lower() for bad in BAD_WORDS):
        reply = "Давай оставим это для фантазий 😉 Лучше расскажи, как настроение?"
        telegram_send(chat_id, reply)
        append_memory(user_id, "assistant", reply)
        return jsonify({"ok": True})

    append_memory(user_id, "user", text)
    history = get_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": text}]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print("Ошибка OpenAI:", e)
        answer = "Кажется, я чуть задумалась 😅 попробуй повторить позже."

    append_memory(user_id, "assistant", answer)
    telegram_send(chat_id, answer)
    return jsonify({"ok": True})

@app.route("/", methods=["GET"])
def home():
    return f"{BOT_NAME} активна 🌸"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
