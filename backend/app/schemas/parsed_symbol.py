from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParsedSymbolRead(BaseModel):
    """Response shape for a single parsed symbol record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    file_id: str
    symbol_type: str
    name: str
    language: str
    start_line: int
    end_line: int
    source_snippet: str | None
    http_method: str | None
    route_path: str | None
    created_at: datetime


class ParseResultSummary(BaseModel):
    """Response returned after triggering a parse run."""

    repository_id: str
    files_parsed: int
    files_skipped_unsupported: int
    total_symbols: int
    symbol_counts: dict[str, int]  # symbol_type -> count
    message: str
