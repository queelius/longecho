"""
longecho - ECHO philosophy documentation and compliance validator.

ECHO is a philosophy for creating durable personal data archives.
longecho provides tools to check if directories are ECHO-compliant
and to discover ECHO-compliant sources.
"""

__version__ = "0.1.0"

from .checker import check_compliance, ComplianceResult
from .discovery import discover_sources, EchoSource

__all__ = [
    "__version__",
    "check_compliance",
    "ComplianceResult",
    "discover_sources",
    "EchoSource",
]
