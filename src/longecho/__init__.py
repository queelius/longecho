"""longecho -- compliance validator, discovery, and site builder for durable personal archives."""

__version__ = "0.4.0"

from .build import BuildResult, build_site
from .checker import (
    DURABLE_FORMAT_CATEGORIES,
    ComplianceResult,
    EchoSource,
    Readme,
    check_compliance,
    parse_readme,
)
from .discovery import discover_sources, matches_query, search_sources

__all__ = [
    "BuildResult",
    "ComplianceResult",
    "DURABLE_FORMAT_CATEGORIES",
    "EchoSource",
    "Readme",
    "__version__",
    "build_site",
    "check_compliance",
    "discover_sources",
    "matches_query",
    "parse_readme",
    "search_sources",
]
