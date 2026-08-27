"""Send mail over SMTP, or print to stdout when SMTP is not configured."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from ..config import get_settings


def send_email(subject: str, body_text: str, body_html: str | None = None) -> tuple[str, str]:
    """Return (status, detail).

    status is one of:
      * ``sent``   - handed to the SMTP server
      * ``logged`` - SMTP not configured, message printed to stdout
      * ``failed`` - SMTP raised; detail carries the error
    """
    settings = get_settings()
    recipients = settings.notify_recipients

    if not settings.smtp_host or not recipients:
        print(
            "\n=== [reminder email - SMTP disabled] ===\n"
            f"To: {', '.join(recipients) or '(no NOTIFY_TO set)'}\n"
            f"Subject: {subject}\n\n{body_text}\n"
            "=======================================\n"
        )
        return "logged", "SMTP not configured; printed to stdout"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(recipients)
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                if settings.smtp_starttls:
                    server.starttls()
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        print(f"[reminder email] send failed: {exc}")
        return "failed", str(exc)

    return "sent", ", ".join(recipients)
