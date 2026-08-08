import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    CloneError,
    DuplicateRepositoryError,
    InvalidRepositoryURLError,
    RepositoryNotFoundError,
)
from app.db.session import get_db
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryDeleteResponse,
    RepositoryRead,
)
from app.services import repository_service

router = APIRouter(prefix="/repositories", tags=["Repositories"])
logger = logging.getLogger("app.api.repositories")


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def register_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    """
    Register a new repository and clone it locally.

    Flow: validate URL -> check duplicate -> insert DB row (status=registered)
    -> clone to disk (status=cloning -> cloned/failed).
    """
    try:
        return repository_service.create_and_clone_repository(
            db, url=payload.url, branch=payload.branch
        )
    except InvalidRepositoryURLError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except DuplicateRepositoryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except CloneError as exc:
        # Repository row still exists in DB with status="failed" for visibility.
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))


@router.get("", response_model=list[RepositoryRead])
def get_repositories(db: Session = Depends(get_db)):
    """List all registered repositories."""
    return repository_service.list_repositories(db)


@router.get("/{repo_id}", response_model=RepositoryRead)
def get_repository(repo_id: str, db: Session = Depends(get_db)):
    """Fetch details for a single repository by ID."""
    try:
        return repository_service.get_repository(db, repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{repo_id}", response_model=RepositoryDeleteResponse)
def remove_repository(repo_id: str, db: Session = Depends(get_db)):
    """Delete a repository's DB record and its cloned files on disk."""
    try:
        repository_service.delete_repository(db, repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CloneError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    return RepositoryDeleteResponse(id=repo_id, message="Repository deleted successfully.")
