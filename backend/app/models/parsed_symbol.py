import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParsedSymbol(Base):
    """
    Represents a single code symbol extracted from a file via Tree-sitter:
    a function, class, method, import, variable, comment, or detected API route.

    One ScannedFile has many ParsedSymbols. Re-parsing a repo clears and
    recreates these rows, same pattern as ScannedFile during a re-scan.
    """

    __tablename__ = "parsed_symbols"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scanned_files.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # One of: "function", "class", "method", "import", "variable", "comment", "api_route"
    symbol_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(512), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)

    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)

    # Raw source text of the symbol (function body, class def line, import
    # statement, etc.) — capped implicitly by us truncating long ones.
    source_snippet: Mapped[str] = mapped_column(Text, nullable=True)

    # For api_route symbols: e.g. "GET" — null for everything else.
    http_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # For api_route symbols: e.g. "/users/{id}" — null for everything else.
    route_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    repository = relationship("Repository", backref="parsed_symbols")
    file = relationship("ScannedFile", backref="parsed_symbols")

    def __repr__(self) -> str:
        return f"<ParsedSymbol type={self.symbol_type!r} name={self.name!r} lines={self.start_line}-{self.end_line}>"
