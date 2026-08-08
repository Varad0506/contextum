import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ParsingError,
    RepositoryNotFoundError,
    RepositoryNotScannedError,
)
from app.db.session import get_db
from app.schemas.parsed_symbol import ParsedSymbolRead, ParseResultSummary
from app.services import parser_service

router = APIRouter(prefix="/repositories", tags=["Tree-sitter Parser"])
logger = logging.getLogger("app.api.symbols")


@router.post("/{repo_id}/parse", response_model=ParseResultSummary)
def parse_repository(repo_id: str, db: Session = Depends(get_db)):
    """
    Parse every supported source file (Python, JavaScript, TypeScript) in a
    scanned repository using Tree-sitter, extracting functions, classes,
    methods, imports, variables, comments, and detected API routes.

    Requires the repository to have been scanned first (POST /{id}/scan).
    """
    try:
        return parser_service.parse_repository(db, repo_id)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except RepositoryNotScannedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ParsingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{repo_id}/symbols", response_model=list[ParsedSymbolRead])
def get_symbols(
    repo_id: str,
    symbol_type: str | None = Query(
        default=None,
        description="Filter by type: function, class, method, import, variable, comment, api_route",
    ),
    db: Session = Depends(get_db),
):
    """List parsed symbols for a repository, optionally filtered by symbol_type."""
    try:
        return parser_service.list_symbols(db, repo_id, symbol_type)
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
