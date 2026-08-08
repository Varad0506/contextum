from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

# SQLite-specific connect arg: allows the connection to be used across
# threads, which is required because FastAPI can serve a single request
# using different threads under the hood (with the default thread pool).
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,  # logs SQL statements when DEBUG=true, useful while developing
    future=True,
)

# Each instance of SessionLocal() is an independent DB session/transaction.
# autoflush/autocommit are left at SQLAlchemy 2.0 defaults (autocommit=False).
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request.

    Guarantees the session is always closed, even if an exception is
    raised while handling the request, preventing connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
