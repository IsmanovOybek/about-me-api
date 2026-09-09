from __future__ import annotations

import logging

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


def notify_chat_message(
    user_message: str,
    reply: str,
    locale: str,
    settings: Settings | None = None,
) -> None:
    """Send website chat transcript to the owner's Telegram chat."""
    cfg = settings or get_settings()
    token = cfg.telegram_bot_token.strip()
    chat_id = cfg.telegram_chat_id.strip()

    if not token or not chat_id:
        return

    text = (
        "🌐 Portfolio chat\n"
        f"Locale: {locale}\n\n"
        f"👤 Visitor:\n{user_message}\n\n"
        f"🤖 Reply:\n{reply}"
    )
    # Telegram hard limit ~4096 chars
    if len(text) > 4000:
        text = text[:3990] + "…"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        response = httpx.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=15.0,
        )
        if response.status_code >= 400:
            logger.warning(
                "Telegram notify failed: %s %s",
                response.status_code,
                response.text[:300],
            )
    except Exception:  # noqa: BLE001
        logger.exception("Telegram notify error")
