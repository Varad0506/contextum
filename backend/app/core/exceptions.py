class RepositoryError(Exception):
    """Base class for all repository-related domain errors."""


class InvalidRepositoryURLError(RepositoryError):
    """Raised when a repository URL fails format/host validation."""


class DuplicateRepositoryError(RepositoryError):
    """Raised when a repository with the same URL is already registered."""


class RepositoryNotFoundError(RepositoryError):
    """Raised when a repository ID doesn't exist in the database."""


class CloneError(RepositoryError):
    """Raised when `git clone` fails (network error, private repo, bad branch, etc.)."""


class ScanError(RepositoryError):
    """Raised when scanning a repository's files fails."""


class RepositoryNotClonedError(RepositoryError):
    """Raised when a scan is attempted on a repository that isn't cloned yet."""


class ParsingError(RepositoryError):
    """Raised when Tree-sitter parsing of a repository's files fails."""


class RepositoryNotScannedError(RepositoryError):
    """Raised when parsing is attempted before the repository has been scanned."""
