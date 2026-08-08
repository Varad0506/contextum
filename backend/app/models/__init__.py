# Import every ORM model here so that Base.metadata.create_all() can see
# it. If a model isn't imported somewhere before create_all() runs, its
# table will silently NOT be created.

from app.models.repository import Repository  # noqa: F401
from app.models.scanned_file import ScannedFile  # noqa: F401
from app.models.parsed_symbol import ParsedSymbol  # noqa: F401
