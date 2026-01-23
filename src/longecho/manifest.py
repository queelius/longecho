"""
ECHO manifest loading and validation.

This module handles manifest.json/manifest.yaml files for ECHO archives.
Manifests provide optional machine-readable metadata about archives,
including name, description, type, and sub-source configuration.

Key functions:
- `load_manifest()`: Load and validate manifest from a directory
- `find_manifest()`: Find manifest file (JSON or YAML) in a directory
- `validate_manifest_data()`: Validate manifest data against schema
- `save_manifest()`: Write manifest to file

The manifest schema is documented in spec/MANIFEST-SCHEMA.md.

Example:
    >>> from longecho.manifest import load_manifest
    >>> manifest = load_manifest("/path/to/archive")
    >>> if manifest:
    ...     print(f"Archive: {manifest.name}")
    ...     print(f"Description: {manifest.description}")
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False


def _find_schema_path() -> Optional[Path]:
    """
    Find the manifest schema file.

    Checks multiple locations to support both development and installed packages:
    1. Development: ../../../schemas/ relative to this module
    2. Installed: sys.prefix/share/longecho/schemas/

    Returns:
        Path to schema file if found, None otherwise
    """
    # Development path (running from source)
    dev_path = Path(__file__).parent.parent.parent / "schemas" / "manifest.schema.json"
    if dev_path.exists():
        return dev_path

    # Installed path (pip install)
    installed_path = Path(sys.prefix) / "share" / "longecho" / "schemas" / "manifest.schema.json"
    if installed_path.exists():
        return installed_path

    return None


SCHEMA_PATH: Optional[Path] = _find_schema_path()


@dataclass
class SourceConfig:
    """Configuration for a sub-archive source."""

    path: str
    order: Optional[int] = None
    browsable: Optional[bool] = None
    name: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        """Create SourceConfig from a dictionary."""
        return cls(
            path=data["path"],
            order=data.get("order"),
            browsable=data.get("browsable"),
            name=data.get("name"),
        )


@dataclass
class Manifest:
    """ECHO archive manifest."""

    version: str
    name: str
    description: str
    type: Optional[str] = None
    browsable: bool = True
    site: Optional[str] = None
    docs: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None
    sources: List[SourceConfig] = field(default_factory=list)

    # Path where manifest was loaded from
    path: Optional[Path] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], path: Optional[Path] = None) -> "Manifest":
        """Create Manifest from a dictionary."""
        sources = [
            SourceConfig.from_dict(s) for s in data.get("sources", [])
        ]

        return cls(
            version=data["version"],
            name=data["name"],
            description=data["description"],
            type=data.get("type"),
            browsable=data.get("browsable", True),
            site=data.get("site"),
            docs=data.get("docs"),
            icon=data.get("icon"),
            order=data.get("order"),
            sources=sources,
            path=path,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        result: Dict[str, Any] = {
            "version": self.version,
            "name": self.name,
            "description": self.description,
        }

        if self.type:
            result["type"] = self.type
        if not self.browsable:
            result["browsable"] = self.browsable
        if self.site:
            result["site"] = self.site
        if self.docs:
            result["docs"] = self.docs
        if self.icon:
            result["icon"] = self.icon
        if self.order is not None:
            result["order"] = self.order
        if self.sources:
            result["sources"] = [
                {k: v for k, v in {
                    "path": s.path,
                    "order": s.order,
                    "browsable": s.browsable,
                    "name": s.name,
                }.items() if v is not None}
                for s in self.sources
            ]

        return result


def find_manifest(path: Path) -> Optional[Path]:
    """
    Find manifest file at the root of a directory.

    Checks for manifest.json first, then manifest.yaml.

    Args:
        path: Directory to check

    Returns:
        Path to manifest if found, None otherwise
    """
    for name in ["manifest.json", "manifest.yaml", "manifest.yml"]:
        manifest = path / name
        if manifest.is_file():
            return manifest
    return None


def load_manifest_data(manifest_path: Path) -> Dict[str, Any]:
    """
    Load manifest data from a file.

    Args:
        manifest_path: Path to manifest file

    Returns:
        Dictionary with manifest data

    Raises:
        ValueError: If file format is not supported or parsing fails
    """
    content = manifest_path.read_text(encoding="utf-8")
    suffix = manifest_path.suffix.lower()

    if suffix == ".json":
        try:
            result: Dict[str, Any] = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {manifest_path}: {e}")

    elif suffix in (".yaml", ".yml"):
        if not YAML_AVAILABLE:
            raise ValueError(
                "PyYAML is required to read YAML manifests. "
                "Install with: pip install pyyaml"
            )
        try:
            result = yaml.safe_load(content)
            return result  # type: ignore[no-any-return]
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {manifest_path}: {e}")

    else:
        raise ValueError(f"Unsupported manifest format: {suffix}")


def validate_manifest_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate manifest data against the schema.

    Args:
        data: Manifest data dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Basic validation (always available)
    if "version" not in data:
        errors.append("Missing required field: version")
    elif data["version"] != "1.0":
        errors.append(f"Unsupported version: {data['version']}")

    if "name" not in data:
        errors.append("Missing required field: name")

    if "description" not in data:
        errors.append("Missing required field: description")

    if "type" in data and data["type"] not in ("database", "documents", "site", "mixed"):
        errors.append(f"Invalid type: {data['type']}")

    if "sources" in data:
        if not isinstance(data["sources"], list):
            errors.append("sources must be an array")
        else:
            for i, source in enumerate(data["sources"]):
                if not isinstance(source, dict):
                    errors.append(f"sources[{i}] must be an object")
                elif "path" not in source:
                    errors.append(f"sources[{i}] missing required field: path")

    # JSON Schema validation (if available)
    if JSONSCHEMA_AVAILABLE and SCHEMA_PATH and SCHEMA_PATH.exists():
        try:
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
            validator = jsonschema.Draft202012Validator(schema)
            for error in validator.iter_errors(data):
                errors.append(f"Schema: {error.message}")
        except Exception:
            pass  # Fall back to basic validation

    return errors


def load_manifest(path: Path) -> Optional[Manifest]:
    """
    Load and validate a manifest from a directory.

    Args:
        path: Directory containing the manifest

    Returns:
        Manifest object if found and valid, None otherwise

    Raises:
        ValueError: If manifest exists but is invalid
    """
    manifest_path = find_manifest(path)
    if not manifest_path:
        return None

    data = load_manifest_data(manifest_path)
    errors = validate_manifest_data(data)

    if errors:
        raise ValueError(f"Invalid manifest at {manifest_path}: {'; '.join(errors)}")

    return Manifest.from_dict(data, path=manifest_path)


def create_minimal_manifest(name: str, description: str) -> Manifest:
    """
    Create a minimal manifest.

    Args:
        name: Archive name
        description: Archive description

    Returns:
        Manifest object
    """
    return Manifest(
        version="1.0",
        name=name,
        description=description,
    )


def save_manifest(manifest: Manifest, path: Path, format: str = "json") -> Path:
    """
    Save a manifest to a file.

    Args:
        manifest: Manifest to save
        path: Directory to save in
        format: Output format ("json" or "yaml")

    Returns:
        Path to saved file
    """
    data = manifest.to_dict()

    if format == "json":
        output_path = path / "manifest.json"
        content = json.dumps(data, indent=2) + "\n"
    elif format in ("yaml", "yml"):
        if not YAML_AVAILABLE:
            raise ValueError("PyYAML is required to write YAML manifests")
        output_path = path / "manifest.yaml"
        content = yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:
        raise ValueError(f"Unsupported format: {format}")

    output_path.write_text(content, encoding="utf-8")
    return output_path
