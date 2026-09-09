#!/usr/bin/env python3
"""Print your Telegram chat_id after you /start the bot."""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    token = settings.telegram_bot_token.strip()
    if not token:
        print("TELEGRAM_BOT_TOKEN is empty in .env")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{token}/getUpdates"
    data = httpx.get(url, timeout=20.0).json()
    if not data.get("ok"):
        print("Telegram error:", data)
        sys.exit(1)

    updates = data.get("result") or []
    if not updates:
        print("Hali xabar yo‘q. Avval botga Telegramda /start yuboring, keyin qayta ishga tushiring.")
        sys.exit(0)

    seen: set[str] = set()
    for item in updates:
        chat = (item.get("message") or item.get("edited_message") or {}).get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None or str(chat_id) in seen:
            continue
        seen.add(str(chat_id))
        name = chat.get("username") or chat.get("first_name") or "unknown"
        print(f"chat_id={chat_id}  name={name}")
        print(f"→ .env ga yozing: TELEGRAM_CHAT_ID={chat_id}")


if __name__ == "__main__":
    main()
