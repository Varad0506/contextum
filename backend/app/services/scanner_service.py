import logging
import os
from collections import Counter
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import RepositoryNotClonedError, ScanError
from app.core.language_map import (
    IGNORED_DIRECTORY_NAMES,
    IGNORED_FILE_NAMES,
    detect_language,
)
from app.models.scanned_file import ScannedFile
from app.services.repository_service import get_repository

logger = logging.getLogger("app.services.scanner_service")

# Skip files larger than this during scan (avoids choking on binary blobs,
# datasets, etc. accidentally committed to a repo). 10 MB is generous for
# source code files.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _walk_repository_files(root: Path):
    """
    Yields absolute Paths for every file under `root`, pruning ignored
    directories in-place so os.walk never descends into them (this is the
    key perf trick — without it, walking node_modules could take minutes).
    """
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place; os.walk respects mutations
        # to dirnames during iteration.
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRECTORY_NAMES]

        for filename in filenames:
            if filename in IGNORED_FILE_NAMES:
                continue
            yield Path(dirpath) / filename


def scan_repository(db: Session, repo_id: str) -> dict:
    """
    Recursively scans a cloned repository's files and persists metadata.

    Idempotent: deletes existing ScannedFile rows for this repo first, then
    re-inserts fresh ones based on current disk state. Returns a summary dict.
    """
    repo = get_repository(db, repo_id)

    if not repo.local_path or repo.status not in ("cloned", "scanned"):
        raise RepositoryNotClonedError(
            f"Repository '{repo_id}' is not in a scannable state (current status: "
            f"'{repo.status}'). Clone must succeed before scanning."
        )

    root = Path(repo.local_path)
    if not root.exists():
        raise RepositoryNotClonedError(
            f"Repository '{repo_id}' has local_path='{root}' but that path "
            "does not exist on disk. Try re-cloning."
        )

    try:
        # Clear previous scan results for this repo (idempotent re-scan).
        db.query(ScannedFile).filter(ScannedFile.repository_id == repo_id).delete()

        language_counter: Counter[str] = Counter()
        total_size = 0
        new_rows: list[ScannedFile] = []

        for abs_path in _walk_repository_files(root):
            try:
                stat = abs_path.stat()
            except OSError:
                # Broken symlink or race condition (file deleted mid-scan) — skip it.
                continue

            if stat.st_size > MAX_FILE_SIZE_BYTES:
                continue

            extension = abs_path.suffix.lower()
            language = detect_language(extension)
            relative_path = str(abs_path.relative_to(root))

            row = ScannedFile(
                repository_id=repo_id,
                name=abs_path.name,
                relative_path=relative_path,
                absolute_path=str(abs_path),
                extension=extension,
                language=language,
                size_bytes=stat.st_size,
            )
            new_rows.append(row)
            language_counter[language] += 1
            total_size += stat.st_size

        db.add_all(new_rows)

        # Mark the repository as scanned so later steps (parsing, etc.) can
        # check readiness without re-querying file counts.
        repo.status = "scanned"
        db.commit()

        logger.info(
            "Scanned repository %s: %d files, %d bytes total",
            repo_id, len(new_rows), total_size,
        )

        return {
            "repository_id": repo_id,
            "total_files": len(new_rows),
            "total_size_bytes": total_size,
            "languages": dict(language_counter),
            "message": f"Scan complete: {len(new_rows)} files indexed.",
        }

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while scanning repository %s", repo_id)
        raise ScanError(f"Failed to persist scan results: {exc}") from exc


def list_scanned_files(db: Session, repo_id: str) -> list[ScannedFile]:
    """Return all scanned files for a repository, alphabetically by path."""
    # Ensure repo exists (raises RepositoryNotFoundError otherwise)
    get_repository(db, repo_id)
    return (
        db.query(ScannedFile)
        .filter(ScannedFile.repository_id == repo_id)
        .order_by(ScannedFile.relative_path.asc())
        .all()
    )
