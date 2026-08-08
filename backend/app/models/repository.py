import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp helper (avoids naive datetime warnings)."""
    return datetime.now(timezone.utc)


class Repository(Base):
    """
    Represents a codebase/repository registered with the platform.

    This is our first real table. Later steps (3+) will populate this
    from actual `git clone` operations; for now it's a plain CRUD-able model
    so we can prove the database layer works end-to-end.
    """

    __tablename__ = "repositories"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    local_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    default_branch: Mapped[str] = mapped_column(String(255), nullable=False, default="main")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="registered")
    # possible status values (informal, no DB-level enum yet):
    # "registered" -> "cloning" -> "cloned" -> "indexed" -> "failed"

    error_message: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    def __repr__(self) -> str:
        return f"<Repository id={self.id} name={self.name!r} status={self.status!r}>"
