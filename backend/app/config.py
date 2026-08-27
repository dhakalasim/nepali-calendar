"""Application settings, loaded from environment / .env file."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Database ---
    database_url: str = (
        "postgresql+psycopg2://nepcal:nepcal@localhost:5432/nepcal"
    )

    # --- CORS (comma separated) ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Email / SMTP (leave smtp_host blank to print reminders to stdout) ---
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Nepali Calendar <no-reply@example.com>"
    smtp_starttls: bool = True
    notify_to: str = ""  # comma separated fallback recipients (UI setting wins)

    # --- SMS (leave every provider blank to print texts to stdout) ---
    # sms_provider: "auto" picks whichever provider below has credentials.
    sms_provider: str = "auto"  # auto | console | aakash | sparrow | twilio

    # AakashSMS (aakashsms.com) - Nepal gateway, simplest signup
    aakash_sms_token: str = ""

    # Sparrow SMS (sparrowsms.com) - Nepal gateway
    sparrow_sms_token: str = ""
    sparrow_sms_from: str = ""  # approved sender identity

    # Twilio (twilio.com) - international
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from: str = ""  # Twilio number (+1...) or Messaging Service SID (MG...)

    # --- Scheduler ---
    notify_hour: int = 7  # hour of day (Asia/Kathmandu) to send the daily digest
    scheduler_enabled: bool = True

    # --- Links inside emails ---
    app_base_url: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def notify_recipients(self) -> list[str]:
        return [e.strip() for e in self.notify_to.split(",") if e.strip()]

    @property
    def smtp_configured(self) -> bool:
        # host is required; if a username is given a password must be too
        if not self.smtp_host:
            return False
        if self.smtp_user and not self.smtp_password:
            return False
        return True

    @property
    def twilio_configured(self) -> bool:
        return bool(
            self.twilio_account_sid and self.twilio_auth_token and self.twilio_from
        )

    @property
    def resolved_sms_provider(self) -> str:
        """Which SMS backend will actually be used."""
        if self.sms_provider and self.sms_provider != "auto":
            return self.sms_provider
        if self.aakash_sms_token:
            return "aakash"
        if self.sparrow_sms_token and self.sparrow_sms_from:
            return "sparrow"
        if self.twilio_configured:
            return "twilio"
        return "console"

    @property
    def sms_configured(self) -> bool:
        return self.resolved_sms_provider != "console"


@lru_cache
def get_settings() -> Settings:
    return Settings()
