import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryRead

router = APIRouter(prefix="/db-check", tags=["DB Check (Step 2 test)"])
logger = logging.getLogger("app.api.db_check")


@router.post(
    "/repositories",
    response_model=RepositoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_repository(payload: RepositoryCreate, db: Session = Depends(get_db)):
    """
    Insert a Repository row. This is a temporary verification endpoint for
    Step 2 only, proving the ORM + SQLite write path works. The full
    Repository CRUD API arrives in Step 9.
    """
    repo = Repository(
        name=payload.name,
        url=str(payload.url),
        default_branch=payload.default_branch,
    )
    try:
        db.add(repo)
        db.commit()
        db.refresh(repo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A repository with this URL is already registered.",
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Unexpected database error while creating repository.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )
    return repo


@router.get("/repositories", response_model=list[RepositoryRead])
def list_repositories(db: Session = Depends(get_db)):
    """List all repositories currently stored in SQLite."""
    try:
        return db.query(Repository).order_by(Repository.created_at.desc()).all()
    except SQLAlchemyError as exc:
        logger.exception("Unexpected database error while listing repositories.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {exc}",
        )
