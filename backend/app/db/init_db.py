import logging

from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine

# Ensures all model classes are registered on Base.metadata before create_all runs
import app.models  # noqa: F401

logger = logging.getLogger("app.db.init_db")


def init_db() -> None:
    """
    Create all database tables that don't already exist.

    Safe to call on every application startup: create_all() only creates
    tables that are missing, it never drops or recreates existing ones.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except SQLAlchemyError as exc:
        logger.exception("Failed to initialize database tables.")
        # Re-raise so the app fails fast on startup rather than running
        # in a broken state with a half-initialized DB.
        raise RuntimeError(f"Database initialization failed: {exc}") from exc
