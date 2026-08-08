# Maps our internal language names (from app.core.language_map) to the
# grammar name expected by tree_sitter_languages.get_parser()/get_language().
#
# Only languages listed here are actually parsed with Tree-sitter in Step 5.
# Other detected languages (from the Step 4 scan) are still tracked as files,
# just skipped during symbol extraction — this keeps scope manageable while
# leaving a clear extension point (just add a query set + registry entry).

SUPPORTED_LANGUAGES: dict[str, str] = {
    "Python": "python",
    "JavaScript": "javascript",
    "TypeScript": "typescript",
}


def is_supported(language: str) -> bool:
    return language in SUPPORTED_LANGUAGES


def grammar_name(language: str) -> str:
    return SUPPORTED_LANGUAGES[language]
