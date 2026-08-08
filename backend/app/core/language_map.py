# Maps file extensions (lowercase, including the dot) to a human-readable
# language name. Extend this as new languages need support (e.g. Step 5's
# Tree-sitter parsing will rely on a subset of these being "known" languages).

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".m": "Objective-C",
    ".scala": "Scala",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".dockerfile": "Dockerfile",
    ".vue": "Vue",
    ".dart": "Dart",
    ".lua": "Lua",
    ".r": "R",
    ".pl": "Perl",
    ".ex": "Elixir",
    ".exs": "Elixir",
}

# Directory names that are always skipped during a scan, regardless of depth.
# Matched case-sensitively against the directory's basename.
IGNORED_DIRECTORY_NAMES: set[str] = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "__pycache__",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "target",       # Rust/Java build output
    "bin",
    "obj",          # .NET build output
    ".next",        # Next.js build cache
    ".nuxt",
    "coverage",
    ".tox",
    "vendor",       # PHP/Go vendored deps
    "egg-info",
}

# Individual filenames (not extensions) that are always skipped.
IGNORED_FILE_NAMES: set[str] = {
    ".DS_Store",
    "Thumbs.db",
    ".gitkeep",
}


def detect_language(extension: str) -> str:
    """Return the language name for a given lowercase extension, or 'Unknown'."""
    return EXTENSION_LANGUAGE_MAP.get(extension.lower(), "Unknown")
