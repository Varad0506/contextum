# Tree-sitter query (S-expression) definitions per language.
# Each query captures a node with a name Tree-sitter will report back via
# `capture_name`, which we map to our internal symbol_type in parser_service.
#
# Query syntax reference: https://tree-sitter.github.io/tree-sitter/using-parsers#query-syntax

PYTHON_QUERY = """
(function_definition
  name: (identifier) @function.name) @function.def

(class_definition
  name: (identifier) @class.name) @class.def

(import_statement) @import.def

(import_from_statement) @import.def

(comment) @comment.def

(expression_statement
  (assignment
    left: (identifier) @variable.name)) @variable.def
"""

# Methods in Python are function_definitions nested inside a class body.
# We don't need a separate query — parser_service distinguishes function
# vs. method by checking whether the function_definition's parent chain
# includes a class_definition's body (see is_inside_class() helper).

JAVASCRIPT_QUERY = """
(function_declaration
  name: (identifier) @function.name) @function.def

(class_declaration
  name: (identifier) @class.name) @class.def

(method_definition
  name: (property_identifier) @method.name) @method.def

(import_statement) @import.def

(comment) @comment.def

(variable_declarator
  name: (identifier) @variable.name) @variable.def
"""

# TypeScript grammar is a superset of JavaScript's node types for the
# constructs we care about here, so the same query works for both.
TYPESCRIPT_QUERY = JAVASCRIPT_QUERY

QUERY_BY_GRAMMAR: dict[str, str] = {
    "python": PYTHON_QUERY,
    "javascript": JAVASCRIPT_QUERY,
    "typescript": TYPESCRIPT_QUERY,
}


# --- API route detection (regex-assisted heuristic, applied to source lines) ---
# We look for common web-framework call/decorator patterns. This runs as a
# secondary pass over each file's raw text, independent of the AST query
# above, since route detection depends on framework conventions rather than
# pure language grammar.
import re  # noqa: E402

API_ROUTE_PATTERNS: list[re.Pattern] = [
    # FastAPI / Flask (Python): @app.get("/path"), @router.post('/path')
    re.compile(r'@\w*(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    # Express (JS/TS): app.get('/path', ...), router.post("/path", ...)
    re.compile(r'\b(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
]
