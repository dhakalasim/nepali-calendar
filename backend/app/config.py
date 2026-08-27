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
    notify_to: str = ""  # comma separated recipient addresses

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
    def email_enabled(self) -> bool:
        return bool(self.smtp_host and self.notify_recipients)


@lru_cache
def get_settings() -> Settings:
    return Settings()
