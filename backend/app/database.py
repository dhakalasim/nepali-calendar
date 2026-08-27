"""SQLAlchemy engine / session wiring."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


# Columns added after the first release. create_all() never ALTERs an existing
# table, so we add these by hand on start-up (idempotent).
_ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "app_settings": {
        "notify_telegram": "TEXT DEFAULT ''",
        "telegram_enabled": "BOOLEAN DEFAULT FALSE",
    },
}


def _ensure_added_columns() -> None:
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    for table, columns in _ADDED_COLUMNS.items():
        if table not in tables:
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        missing = {n: ddl for n, ddl in columns.items() if n not in existing}
        if not missing:
            continue
        with engine.begin() as conn:
            for name, ddl in missing.items():
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db() -> None:
    """Create tables that do not yet exist, and add any columns introduced
    after the first release. No migration tool - the schema is small and
    single-tenant. Import models here so they are registered on ``Base``.
    """
    from . import models  # noqa: F401  (registers mappers)

    Base.metadata.create_all(bind=engine)
    _ensure_added_columns()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
