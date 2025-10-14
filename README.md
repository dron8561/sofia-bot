# 🤖 София — флиртующий Telegram-бот с ИИ

Милая и лёгкая собеседница, работает на OpenAI + Flask.

---

## 🔧 Установка локально (для теста)

1. Получи токен бота от [@BotFather](https://t.me/BotFather)
2. Получи API-ключ OpenAI: https://platform.openai.com/
3. Склони репозиторий или распакуй архив:
   ```bash
   git clone <твой-репо>
   cd sofia-bot
   ```
4. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
5. Установи переменные окружения (в Linux/macOS):
   ```bash
   export TELEGRAM_TOKEN="твой_токен"
   export OPENAI_API_KEY="твой_api_key"
   ```
   В Windows PowerShell:
   ```powershell
   setx TELEGRAM_TOKEN "твой_токен"
   setx OPENAI_API_KEY "твой_api_key"
   ```
6. Запусти локально:
   ```bash
   python main.py
   ```
7. Настрой webhook (замени localhost при необходимости):
   ```bash
   curl "https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://<твoй-url>/webhook"
   ```

---

## ☁️ Деплой на Render (бесплатный хостинг)

1. Создай репозиторий на GitHub и запушь файлы.
2. Зарегистрируйся на https://render.com и создай **New Web Service**.
3. Подключи GitHub-репо и выбери ветку.
4. В Environment → Add Environment Variables добавь:
   - TELEGRAM_TOKEN
   - OPENAI_API_KEY
5. Команда запуска (Start Command): `gunicorn main:app --bind 0.0.0.0:$PORT`
6. После деплоя вызови:
   ```
   https://api.telegram.org/bot<TELEGRAM_TOKEN>/setWebhook?url=https://<render_url>/webhook
   ```

---

## ⚠️ Важно про безопасность и модерацию

- НЕ вставляй ключи и токены прямо в код. Используй переменные окружения.
- Бот фильтрует откровенные слова, но следи за поведением и логами.
- OpenAI API платный — контролируй расходы (max_tokens, frequency).
- Убедись, что твой бот соблюдает правила Telegram и OpenAI.

---

## Дополнительно

Можно добавить:
- модуль модерации (OpenAI moderation) перед отправкой в генератор;
- голосовые ответы (TTS);
- кнопки и быстрые ответы (InlineKeyboard).
