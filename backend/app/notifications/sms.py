"""Send SMS through one of several providers, or print to stdout when none
is configured. Provider is chosen by ``Settings.resolved_sms_provider``."""

from __future__ import annotations

import re

import httpx

from ..config import get_settings

_TWILIO_API = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
_AAKASH_API = "https://sms.aakashsms.com/sms/v3/send/"
_SPARROW_API = "https://api.sparrowsms.com/v2/sms/"


def _local10(phone: str) -> str:
    """Reduce any Nepal number to the 10-digit local form the NP gateways want."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("977") and len(digits) > 10:
        digits = digits[3:]
    return digits[-10:]


def send_sms(body: str, recipients: list[str]) -> tuple[str, str]:
    """Return (status, detail) - same convention as ``send_email``."""
    settings = get_settings()
    provider = settings.resolved_sms_provider

    if provider == "console" or not recipients:
        print(
            "\n=== [reminder text - no SMS provider configured] ===\n"
            f"To: {', '.join(recipients) or '(no phone set)'}\n\n{body}\n"
            "====================================================\n"
        )
        return "logged", "No SMS provider configured; printed to stdout"

    if provider == "aakash":
        return _send_aakash(settings, body, recipients)
    if provider == "sparrow":
        return _send_sparrow(settings, body, recipients)
    if provider == "twilio":
        return _send_twilio(settings, body, recipients)
    return "failed", f"Unknown SMS provider '{provider}'"


def _send_aakash(settings, body: str, recipients: list[str]) -> tuple[str, str]:
    to = ",".join(_local10(r) for r in recipients)
    try:
        resp = httpx.post(
            _AAKASH_API,
            data={"auth_token": settings.aakash_sms_token, "to": to, "text": body},
            timeout=30,
        )
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return "failed", f"AakashSMS request failed: {exc}"
    if resp.status_code < 400 and not payload.get("error", False):
        return "sent", f"AakashSMS -> {to}"
    return "failed", f"AakashSMS {resp.status_code}: {payload.get('message', resp.text[:160])}"


def _send_sparrow(settings, body: str, recipients: list[str]) -> tuple[str, str]:
    to = ",".join(_local10(r) for r in recipients)
    try:
        resp = httpx.post(
            _SPARROW_API,
            data={
                "token": settings.sparrow_sms_token,
                "from": settings.sparrow_sms_from,
                "to": to,
                "text": body,
            },
            timeout=30,
        )
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return "failed", f"Sparrow SMS request failed: {exc}"
    if resp.status_code < 400 and payload.get("response_code") == 200:
        return "sent", f"Sparrow -> {to}"
    return "failed", f"Sparrow {resp.status_code}: {payload.get('response', resp.text[:160])}"


def _send_twilio(settings, body: str, recipients: list[str]) -> tuple[str, str]:
    url = _TWILIO_API.format(sid=settings.twilio_account_sid)
    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    sender_key = "MessagingServiceSid" if settings.twilio_from.startswith("MG") else "From"

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
