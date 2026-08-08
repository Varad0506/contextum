import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ScannedFile(Base):
    """
    Represents a single file discovered during a repository scan.

    One Repository has many ScannedFiles (one-to-many). Re-scanning a repo
    deletes and recreates these rows, so this table always reflects the
    most recent scan's view of the filesystem.
    """

    __tablename__ = "scanned_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Path relative to the repository root, e.g. "src/app/main.py" — portable
    # across machines, unlike the absolute local_path.
    relative_path: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    absolute_path: Mapped[str] = mapped_column(String(2048), nullable=False)

    extension: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    repository = relationship("Repository", backref="scanned_files")

    def __repr__(self) -> str:
        return f"<ScannedFile id={self.id} path={self.relative_path!r} lang={self.language!r}>"
