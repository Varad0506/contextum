from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Liveness check that confirms both the API and the database connection
    are working. Runs a trivial `SELECT 1` to verify SQLite connectivity.
    """
    settings = get_settings()

    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # broad on purpose: this is a diagnostic endpoint
        db_status = f"error: {exc}"

    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
    }
