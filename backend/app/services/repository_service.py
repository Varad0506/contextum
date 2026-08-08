import logging
import re
import shutil
import uuid

from git import Repo as GitRepo
from git.exc import GitCommandError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    CloneError,
    DuplicateRepositoryError,
    InvalidRepositoryURLError,
    RepositoryNotFoundError,
)
from app.models.repository import Repository

logger = logging.getLogger("app.services.repository_service")
settings = get_settings()

# Accepts:
#   https://github.com/user/repo
#   https://github.com/user/repo.git
#   http://gitlab.com/group/sub/repo.git
#   git@github.com:user/repo.git
_URL_PATTERN = re.compile(
    r"^(https?://[\w.\-]+/[\w.\-/]+?(\.git)?/?|git@[\w.\-]+:[\w.\-/]+?\.git)$"
)


def validate_repository_url(url: str) -> str:
    """
    Validate that a URL looks like a real git remote (http/https/ssh).
    Returns the trimmed URL if valid, otherwise raises InvalidRepositoryURLError.

    This is intentionally a format check only — it does NOT verify the repo
    exists or is reachable. That's discovered naturally when `git clone` runs.
    """
    cleaned = url.strip()
    if not cleaned:
        raise InvalidRepositoryURLError("Repository URL cannot be empty.")

    if not _URL_PATTERN.match(cleaned):
        raise InvalidRepositoryURLError(
            f"'{url}' does not look like a valid git repository URL. "
            "Expected an https:// or git@ SSH URL."
        )
    return cleaned


def _derive_repo_name(url: str) -> str:
    """Extract a human-readable repo name from its URL, e.g. 'Hello-World'."""
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[: -len(".git")]
    return name or "unnamed-repository"


def _check_duplicate(db: Session, url: str) -> None:
    existing = db.query(Repository).filter(Repository.url == url).first()
    if existing is not None:
        raise DuplicateRepositoryError(
            f"Repository with URL '{url}' is already registered (id={existing.id})."
        )


def create_and_clone_repository(db: Session, url: str, branch: str | None) -> Repository:
    """
    Validates the URL, checks for duplicates, registers a DB row, then
    clones the repository to disk — updating status at every transition.

    Status flow: registered -> cloning -> cloned | failed
    """
    clean_url = validate_repository_url(url)
    _check_duplicate(db, clean_url)

    repo_row = Repository(
        id=str(uuid.uuid4()),
        name=_derive_repo_name(clean_url),
        url=clean_url,
        default_branch=branch or "main",
        status="registered",
    )

    try:
        db.add(repo_row)
        db.commit()
        db.refresh(repo_row)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to insert repository row before cloning.")
        raise CloneError(f"Could not save repository metadata: {exc}") from exc

    # Destination folder is keyed by the DB-generated UUID to avoid
    # collisions and to sidestep filesystem-unsafe characters in repo names.
    dest_path = settings.repo_storage_dir / repo_row.id

    repo_row.status = "cloning"
    db.commit()

    try:
        clone_kwargs = {"depth": 1}  # shallow clone: faster, saves disk space
        if branch:
            clone_kwargs["branch"] = branch

        git_repo = GitRepo.clone_from(clean_url, dest_path, **clone_kwargs)
        active_branch = _resolve_active_branch(git_repo, fallback=branch or "main")

        repo_row.status = "cloned"
        repo_row.local_path = str(dest_path)
        repo_row.default_branch = active_branch
        repo_row.error_message = None
        db.commit()
        db.refresh(repo_row)
        logger.info("Cloned repository %s -> %s", clean_url, dest_path)
        return repo_row

    except GitCommandError as exc:
        _cleanup_partial_clone(dest_path)
        repo_row.status = "failed"
        repo_row.error_message = str(exc)[:2048]
        db.commit()
        logger.error("Git clone failed for %s: %s", clean_url, exc)
        raise CloneError(f"Failed to clone repository: {exc}") from exc

    except Exception as exc:  # noqa: BLE001 - catch-all so status always ends up 'failed'
        _cleanup_partial_clone(dest_path)
        repo_row.status = "failed"
        repo_row.error_message = str(exc)[:2048]
        db.commit()
        logger.exception("Unexpected error while cloning %s", clean_url)
        raise CloneError(f"Unexpected error while cloning repository: {exc}") from exc


def _resolve_active_branch(git_repo: GitRepo, fallback: str) -> str:
    """Best-effort read of the branch actually checked out after cloning."""
    try:
        return git_repo.active_branch.name
    except (TypeError, ValueError):
        # Happens for detached HEAD states (e.g. shallow clone of a tag/commit)
        return fallback


def _cleanup_partial_clone(dest_path) -> None:
    """Remove a partially-cloned directory so retries don't collide."""
    try:
        if dest_path.exists():
            shutil.rmtree(dest_path, ignore_errors=True)
    except OSError:
        logger.warning("Could not fully clean up partial clone at %s", dest_path)


def list_repositories(db: Session) -> list[Repository]:
    """Return all registered repositories, newest first."""
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


def get_repository(db: Session, repo_id: str) -> Repository:
    """Fetch a single repository by ID or raise RepositoryNotFoundError."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if repo is None:
        raise RepositoryNotFoundError(f"Repository with id '{repo_id}' was not found.")
    return repo


def delete_repository(db: Session, repo_id: str) -> None:
    """
    Delete a repository's DB row AND its cloned files on disk.
    DB deletion happens first; if disk cleanup fails, we log a warning but
    don't fail the request, since the DB is the source of truth for the API.
    """
    repo = get_repository(db, repo_id)
    local_path = repo.local_path

    try:
        db.delete(repo)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to delete repository row id=%s", repo_id)
        raise CloneError(f"Could not delete repository record: {exc}") from exc

    if local_path:
        try:
            shutil.rmtree(local_path, ignore_errors=True)
            logger.info("Deleted local files for repository id=%s at %s", repo_id, local_path)
        except OSError:
            logger.warning(
                "Repository id=%s DB record deleted, but failed to remove local files at %s",
                repo_id,
                local_path,
            )
