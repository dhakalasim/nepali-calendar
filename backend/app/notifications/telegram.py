"""Deliver reminders as Telegram messages via the Bot API.

Free, no approval - the user creates a bot with @BotFather, sends it one
message, and the app picks up the chat id (see ``get_recent_chats``)."""

from __future__ import annotations

import httpx

from ..config import get_settings

_API = "https://api.telegram.org/bot{token}/{method}"


def _url(method: str) -> str:
    return _API.format(token=get_settings().telegram_bot_token, method=method)


def send_telegram(body: str, chat_ids: list[str]) -> tuple[str, str]:
    """Return (status, detail) - same convention as ``send_email``."""
    settings = get_settings()
    if not settings.telegram_configured or not chat_ids:
        print(
            "\n=== [reminder telegram - not configured] ===\n"
            f"To: {', '.join(chat_ids) or '(no chat id set)'}\n\n{body}\n"
            "============================================\n"
        )
        return "logged", "Telegram bot token not set; printed to stdout"

    sent: list[str] = []
    errors: list[str] = []
    with httpx.Client(timeout=30) as client:
        for chat_id in chat_ids:
            try:
                resp = client.post(
                    _url("sendMessage"),
                    json={"chat_id": chat_id, "text": body, "disable_web_page_preview": True},
                )
                payload = resp.json()
                if resp.status_code < 400 and payload.get("ok"):
                    sent.append(chat_id)
                else:
                    errors.append(f"{chat_id}: {payload.get('description', resp.text[:140])}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{chat_id}: {exc}")

    if sent and not errors:
        return "sent", f"telegram -> {', '.join(sent)}"
    if sent:
        return "sent", f"sent: {', '.join(sent)}; failed: {'; '.join(errors)}"
    return "failed", "; ".join(errors)


def get_recent_chats() -> list[dict]:
    """Chats that have recently messaged the bot - used to fill in a chat id."""
    settings = get_settings()
    if not settings.telegram_configured:
        return []
    try:
        resp = httpx.get(_url("getUpdates"), params={"limit": 20, "timeout": 0}, timeout=15)
        updates = resp.json().get("result", [])
    except Exception:  # noqa: BLE001
        return []

    seen: dict[str, dict] = {}
    for upd in updates:
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat")
        if not chat:
            continue
        cid = str(chat["id"])
        name = chat.get("title") or " ".join(
            filter(None, [chat.get("first_name"), chat.get("last_name")])
        ) or chat.get("username") or cid
        seen[cid] = {"chat_id": cid, "name": name, "last_text": msg.get("text", "")}
    return list(seen.values())
