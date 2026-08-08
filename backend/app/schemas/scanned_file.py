from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScannedFileRead(BaseModel):
    """Response shape for a single scanned file record."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    name: str
    relative_path: str
    extension: str
    language: str
    size_bytes: int
    created_at: datetime


class ScanResultSummary(BaseModel):
    """Response returned after triggering a scan."""

    repository_id: str
    total_files: int
    total_size_bytes: int
    languages: dict[str, int]  # language -> file count
    message: str
