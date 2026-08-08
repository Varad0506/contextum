import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import RepositoryNotClonedError, RepositoryNotFoundError, ScanError
from app.db.session import get_db
from app.schemas.scanned_file import ScannedFileRead, ScanResultSummary
from app.services import scanner_service

router = APIRouter(prefix="/repositories", tags=["Repository Scanner"])
logger = logging.getLogger("app.api.files")


@router.post("/{repo_id}/scan", response_model=ScanResultSummary)
def scan_repository(repo_id: str, db: Session = Depends(get_db)):
    """
    Recursively scan a cloned repository's files and store their metadata.

    Safe to call multiple times: each call replaces prior scan results for
    this repository with a fresh snapshot of the current filesystem state.
    """
    try:
        return scanner_service.scan_repository(db, repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RepositoryNotClonedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ScanError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{repo_id}/files", response_model=list[ScannedFileRead])
def get_scanned_files(repo_id: str, db: Session = Depends(get_db)):
    """List all files discovered in the most recent scan of a repository."""
    try:
        return scanner_service.list_scanned_files(db, repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
