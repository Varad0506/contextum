from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared declarative base class for all ORM models.

    Every model in app/models/*.py must inherit from this Base so that
    SQLAlchemy's metadata registry knows about it, and so
    Base.metadata.create_all() can create all tables at once.
    """
    pass
