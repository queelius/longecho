"""
longecho - ECHO philosophy documentation and compliance validator.

ECHO is a philosophy for creating durable personal data archives.
longecho provides tools to check if directories are ECHO-compliant,
discover ECHO-compliant sources, and build static sites for archives.
"""

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
    "__version__",
    "check_compliance",
    "ComplianceResult",
    "discover_sources",
    "EchoSource",
    "load_manifest",
    "Manifest",
    "parse_readme",
    "Readme",
    "SourceConfig",
    "build_site",
    "BuildResult",
]
