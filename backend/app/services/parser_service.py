import logging
from collections import Counter
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import ParsingError, RepositoryNotScannedError
from app.models.parsed_symbol import ParsedSymbol
from app.models.scanned_file import ScannedFile
from app.parsing.language_registry import is_supported, grammar_name
from app.parsing.queries import QUERY_BY_GRAMMAR, API_ROUTE_PATTERNS
from app.services.repository_service import get_repository

logger = logging.getLogger("app.services.parser_service")

# Truncate very long source snippets so the DB / API responses stay light.
MAX_SNIPPET_CHARS = 4000

# Cache of compiled (language, parser, query) tuples so we don't reload the
# grammar from disk for every single file — significant speedup on repos
# with hundreds of files of the same language.
_parser_cache: dict[str, tuple] = {}


def _get_parser_and_query(grammar: str):
    """
    Lazily loads and caches a Tree-sitter parser + compiled query for a
    given grammar name. Imports tree_sitter_languages here (not at module
    top-level) so the rest of the app can still import/run even if the
    package isn't installed yet (fails loudly only when parsing is used).
    """
    if grammar in _parser_cache:
        return _parser_cache[grammar]

    try:
        from tree_sitter_languages import get_parser, get_language
    except ImportError as exc:
        raise ParsingError(
            "tree-sitter-languages is not installed. Run: "
            "pip install tree-sitter==0.23.2 tree-sitter-languages==1.10.2"
        ) from exc

    parser = get_parser(grammar)
    language = get_language(grammar)
    query_str = QUERY_BY_GRAMMAR[grammar]
    query = language.query(query_str)

    _parser_cache[grammar] = (parser, query)
    return parser, query


def _node_text(node, source_bytes: bytes) -> str:
    text = source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[:MAX_SNIPPET_CHARS] + "\n... (truncated)"
    return text


def _is_inside_class(node) -> bool:
    """Walk up the AST to determine if a function_definition sits inside a class body."""
    current = node.parent
    while current is not None:
        if current.type == "class_definition" or current.type == "class_declaration":
            return True
        current = current.parent
    return False


CAPTURE_TO_SYMBOL_TYPE = {
    "function.def": "function",
    "class.def": "class",
    "method.def": "method",
    "import.def": "import",
    "comment.def": "comment",
    "variable.def": "variable",
}


def _extract_symbols_from_file(
    source_bytes: bytes, grammar: str, language: str
) -> list[dict]:
    """
    Runs the Tree-sitter query against a file's parsed tree and returns a
    list of symbol dicts (not yet ORM objects — file/repo IDs attached later).
    """
    parser, query = _get_parser_and_query(grammar)
    tree = parser.parse(source_bytes)

    symbols: list[dict] = []
    captures = query.captures(tree.root_node)

    for node, capture_name in captures:
        if capture_name not in CAPTURE_TO_SYMBOL_TYPE:
            continue  # skip .name captures, we only materialize .def captures

        symbol_type = CAPTURE_TO_SYMBOL_TYPE[capture_name]

        # Python distinguishes method vs. function by nesting inside a class;
        # JS/TS already has a distinct method_definition node type for this.
        if symbol_type == "function" and grammar == "python" and _is_inside_class(node):
            symbol_type = "method"

        name = _derive_symbol_name(node, symbol_type, source_bytes)

        symbols.append({
            "symbol_type": symbol_type,
            "name": name,
            "start_line": node.start_point[0] + 1,  # tree-sitter is 0-indexed
            "end_line": node.end_point[0] + 1,
            "source_snippet": _node_text(node, source_bytes),
        })

    # Secondary pass: API route detection via regex on raw text (framework
    # convention matching, not part of the language grammar itself).
    text = source_bytes.decode("utf-8", errors="replace")
    for line_num, line in enumerate(text.splitlines(), start=1):
        for pattern in API_ROUTE_PATTERNS:
            match = pattern.search(line)
            if match:
                method, path = match.group(1).upper(), match.group(2)
                symbols.append({
                    "symbol_type": "api_route",
                    "name": f"{method} {path}",
                    "start_line": line_num,
                    "end_line": line_num,
                    "source_snippet": line.strip()[:MAX_SNIPPET_CHARS],
                    "http_method": method,
                    "route_path": path,
                })

    return symbols


def _derive_symbol_name(node, symbol_type: str, source_bytes: bytes) -> str:
    """
    Finds the human-readable name for a captured .def node by locating its
    'name' field child (function name, class name, etc.). Falls back to a
    truncated snippet for nodes without a clean name field (imports, comments).
    """
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text(name_node, source_bytes)[:512]

    # imports/comments/variables: use first line of the snippet as the "name"
    snippet = _node_text(node, source_bytes)
    first_line = snippet.splitlines()[0] if snippet else ""
    return first_line.strip()[:512]


def parse_repository(db: Session, repo_id: str) -> dict:
    """
    Parses every supported source file in a repository with Tree-sitter,
    extracting functions, classes, methods, imports, variables, comments,
    and detected API routes. Idempotent: clears prior symbols for this repo
    before inserting fresh results.
    """
    repo = get_repository(db, repo_id)

    if repo.status not in ("scanned",):
        raise RepositoryNotScannedError(
            f"Repository '{repo_id}' has not been scanned yet (current status: "
            f"'{repo.status}'). Run POST /repositories/{repo_id}/scan first."
        )

    files = db.query(ScannedFile).filter(ScannedFile.repository_id == repo_id).all()

    try:
        db.query(ParsedSymbol).filter(ParsedSymbol.repository_id == repo_id).delete()

        symbol_counter: Counter[str] = Counter()
        new_rows: list[ParsedSymbol] = []
        files_parsed = 0
        files_skipped = 0

        for scanned_file in files:
            if not is_supported(scanned_file.language):
                files_skipped += 1
                continue

            path = Path(scanned_file.absolute_path)
            try:
                source_bytes = path.read_bytes()
            except OSError:
                logger.warning("Could not read file %s during parsing, skipping.", path)
                files_skipped += 1
                continue

            grammar = grammar_name(scanned_file.language)
            try:
                symbols = _extract_symbols_from_file(source_bytes, grammar, scanned_file.language)
            except Exception:
                logger.exception("Failed to parse file %s, skipping.", path)
                files_skipped += 1
                continue

            for sym in symbols:
                new_rows.append(ParsedSymbol(
                    repository_id=repo_id,
                    file_id=scanned_file.id,
                    symbol_type=sym["symbol_type"],
                    name=sym["name"],
                    language=scanned_file.language,
                    start_line=sym["start_line"],
                    end_line=sym["end_line"],
                    source_snippet=sym.get("source_snippet"),
                    http_method=sym.get("http_method"),
                    route_path=sym.get("route_path"),
                ))
                symbol_counter[sym["symbol_type"]] += 1

            files_parsed += 1

        db.add_all(new_rows)
        repo.status = "parsed"
        db.commit()

        logger.info(
            "Parsed repository %s: %d files parsed, %d skipped, %d symbols extracted",
            repo_id, files_parsed, files_skipped, len(new_rows),
        )

        return {
            "repository_id": repo_id,
            "files_parsed": files_parsed,
            "files_skipped_unsupported": files_skipped,
            "total_symbols": len(new_rows),
            "symbol_counts": dict(symbol_counter),
            "message": f"Parse complete: {len(new_rows)} symbols extracted from {files_parsed} files.",
        }

    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while parsing repository %s", repo_id)
        raise ParsingError(f"Failed to persist parse results: {exc}") from exc


def list_symbols(db: Session, repo_id: str, symbol_type: str | None = None) -> list[ParsedSymbol]:
    """List parsed symbols for a repository, optionally filtered by type."""
    get_repository(db, repo_id)  # raises RepositoryNotFoundError if missing
    query = db.query(ParsedSymbol).filter(ParsedSymbol.repository_id == repo_id)
    if symbol_type:
        query = query.filter(ParsedSymbol.symbol_type == symbol_type)
    return query.order_by(ParsedSymbol.start_line.asc()).all()
