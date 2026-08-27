"""Send SMS via Twilio's REST API, or print to stdout when not configured."""

from __future__ import annotations

import httpx

from ..config import get_settings

_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def send_sms(body: str, recipients: list[str]) -> tuple[str, str]:
    """Return (status, detail) - same convention as ``send_email``."""
    settings = get_settings()

    if not settings.twilio_configured or not recipients:
        print(
            "\n=== [reminder text - Twilio disabled] ===\n"
            f"To: {', '.join(recipients) or '(no phone set)'}\n\n{body}\n"
            "=========================================\n"
        )
        return "logged", "Twilio not configured; printed to stdout"

    url = _API.format(sid=settings.twilio_account_sid)
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    sender_key = (
        "MessagingServiceSid"
        if settings.twilio_from.startswith("MG")
        else "From"
    )

    sent: list[str] = []
    errors: list[str] = []
    with httpx.Client(timeout=30) as client:
        for to in recipients:
            data = {"To": to, "Body": body, sender_key: settings.twilio_from}
            try:
                resp = client.post(url, data=data, auth=auth)
                if resp.status_code >= 400:
                    try:
                        reason = resp.json().get("message", resp.text)
                    except Exception:  # noqa: BLE001
                        reason = resp.text
                    errors.append(f"{to}: {resp.status_code} {reason[:140]}")
                else:
                    sent.append(to)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{to}: {exc}")

    if sent and not errors:
        return "sent", ", ".join(sent)
    if sent and errors:
        return "sent", f"sent: {', '.join(sent)}; failed: {'; '.join(errors)}"
    return "failed", "; ".join(errors)
