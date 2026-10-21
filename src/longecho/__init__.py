"""longecho -- compliance validator, discovery, and site builder for durable personal archives."""

__version__ = "0.5.0"

from .build import BuildResult, build_site
from .checker import (
    ComplianceResult,
    ComplianceWarning,
    EchoSource,
    Readme,
    WarningKind,
    check_compliance,
    find_warnings,
    parse_readme,
)
from .discovery import discover_sources, matches_query, search_sources
from .formats import (
    DURABILITY_CRITERIA,
    DURABLE_FORMAT_CATEGORIES,
    FORMATS,
    Format,
    Reader,
    format_for,
)

__all__ = [
    "DURABILITY_CRITERIA",
    "DURABLE_FORMAT_CATEGORIES",
    "FORMATS",
    "BuildResult",
    "ComplianceResult",
    "ComplianceWarning",
    "EchoSource",
    "Format",
    "Reader",
    "Readme",
    "WarningKind",
    "__version__",
    "build_site",
    "check_compliance",
    "discover_sources",
    "find_warnings",
    "format_for",
    "matches_query",
    "parse_readme",
    "search_sources",
]
