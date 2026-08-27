"""Read/normalise the user-editable notification settings row."""

from __future__ import annotations

import re

from email_validator import EmailNotValidError, validate_email
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import AppSettings

_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


def _split(raw: str) -> list[str]:
    return [p.strip() for p in re.split(r"[,\n;]+", raw or "") if p.strip()]


def get_app_settings(db: Session) -> AppSettings:
    row = db.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def get_email_targets(db: Session) -> list[str]:
    """UI-configured emails, falling back to the NOTIFY_TO env var."""
    row = get_app_settings(db)
    return _split(row.notify_emails) or get_settings().notify_recipients


def get_sms_targets(db: Session) -> list[str]:
    return _split(get_app_settings(db).notify_phones)


def normalize_emails(raw: str) -> str:
    out: list[str] = []
    for addr in _split(raw):
        try:
            out.append(validate_email(addr, check_deliverability=False).normalized)
        except EmailNotValidError as exc:
            raise ValueError(f"Invalid email '{addr}': {exc}") from exc
    return ", ".join(out)


def normalize_phones(raw: str) -> str:
    out: list[str] = []
    for phone in _split(raw):
        cleaned = re.sub(r"[ ()\-]", "", phone)
        if not _PHONE_RE.match(cleaned):
            raise ValueError(
                f"Invalid phone '{phone}' - use international format, e.g. +9779800000000"
            )
        out.append(cleaned)
    return ", ".join(out)
