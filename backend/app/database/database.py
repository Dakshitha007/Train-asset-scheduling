"""SQLAlchemy engine, declarative base, and request-scoped sessions."""

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """Base class for persisted entities."""


engine_options: dict[str, object] = {"pool_pre_ping": True, "echo": settings.database_echo}
if settings.database_url.startswith("sqlite:"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

if settings.database_url.startswith("sqlite:"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, connection_record) -> None:
        del connection_record
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def initialize_database() -> None:
    """Create a local SQLite schema or verify the migrated PostgreSQL connection."""
    if settings.database_url.startswith("sqlite:") and settings.auto_create_sqlite_schema:
        from backend.app.database import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        return
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
