import os
import sqlite3
import time
from flask import Flask, request, jsonify
import requests
from openai import OpenAI
import os
from bad_words import BAD_WORDS

# === Конфигурация ===
# ВАЖНО: не сохраняй ключи в коде. Установи их как переменные окружения на хостинге (Render).
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
BOT_NAME = "София"
PORT = int(os.environ.get("PORT", 8000))

if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("⚠️ Не установлены TELEGRAM_TOKEN и OPENAI_API_KEY. Установи переменные окружения.")

tg_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Flask ===
app = Flask(__name__)

# === SQLite база памяти ===
DB_PATH = "memory.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

def append_memory(user_id: int, role: str, content: str):
    cur.execute("INSERT INTO chats (user_id, role, content, ts) VALUES (?, ?, ?, ?)",
                (user_id, role, content, int(time.time())))
    conn.commit()
    # сохраняем последние 20 сообщений
    cur.execute("DELETE FROM chats WHERE rowid IN (SELECT rowid FROM chats WHERE user_id=? ORDER BY ts DESC LIMIT -1 OFFSET 20)", (user_id,))
    conn.commit()

def get_history(user_id: int):
    cur.execute("SELECT role, content FROM chats WHERE user_id=? ORDER BY ts ASC", (user_id,))
    rows = cur.fetchall()
    return [{"role": r[0], "content": r[1]} for r in rows]

def telegram_send(chat_id: int, text: str):
    url = f"{tg_api}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

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
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    messages.append({"role": "user", "content": text})

    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=400,
            temperature=0.9
        )
        answer = resp.choices[0].message.content.strip()
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
