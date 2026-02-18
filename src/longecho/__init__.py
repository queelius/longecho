"""longecho -- compliance validator, discovery, and site builder for durable personal archives."""

__version__ = "0.3.0"

from .build import BuildResult, build_site
from .checker import (
    ComplianceResult,
    EchoSource,
    Readme,
    check_compliance,
    parse_readme,
)
from .discovery import discover_sources

__all__ = [
    "BuildResult",
    "ComplianceResult",
    "EchoSource",
    "Readme",
    "__version__",
    "build_site",
    "check_compliance",
    "discover_sources",
    "parse_readme",
]
