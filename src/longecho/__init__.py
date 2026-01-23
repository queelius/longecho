"""
longecho - ECHO philosophy documentation and compliance validator.

ECHO is a philosophy for creating durable personal data archives.
longecho provides tools to check if directories are ECHO-compliant,
discover ECHO-compliant sources, and build static sites for archives.
"""

__version__ = "0.2.0"

from .checker import check_compliance, ComplianceResult
from .discovery import discover_sources, EchoSource
from .manifest import load_manifest, Manifest, SourceConfig
from .build import build_site, BuildResult

__all__ = [
    "__version__",
    "check_compliance",
    "ComplianceResult",
    "discover_sources",
    "EchoSource",
    "load_manifest",
    "Manifest",
    "SourceConfig",
    "build_site",
    "BuildResult",
]
