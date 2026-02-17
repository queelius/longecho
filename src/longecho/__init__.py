"""longecho -- ECHO compliance validator, discovery, and site builder."""

__version__ = "0.2.0"

from .build import BuildResult, build_site
from .checker import (
    ComplianceResult,
    EchoSource,
    Readme,
    check_compliance,
    parse_readme,
)
from .discovery import discover_sources
from .manifest import Manifest, SourceConfig, load_manifest

__all__ = [
    "BuildResult",
    "ComplianceResult",
    "EchoSource",
    "Manifest",
    "Readme",
    "SourceConfig",
    "__version__",
    "build_site",
    "check_compliance",
    "discover_sources",
    "load_manifest",
    "parse_readme",
]
