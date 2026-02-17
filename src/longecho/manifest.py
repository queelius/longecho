"""
ECHO manifest loading.

Manifests are YAML files (manifest.yaml) providing optional machine-readable
metadata about ECHO archives. All fields are optional.

Example manifest.yaml:
    name: My Archive
    description: Personal data archive
    icon: "\U0001F4E6"
    sources:
      - conversations/
      - path: bookmarks/
        name: My Bookmarks
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass
class SourceConfig:
    """A source entry in a manifest."""

    path: str
    name: Optional[str] = None
    icon: Optional[str] = None
    order: Optional[int] = None


@dataclass
class Manifest:
    """ECHO archive manifest. All fields optional."""

    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sources: list[SourceConfig] = field(default_factory=list)
    path: Optional[Path] = None  # where loaded from

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: Optional[Path] = None) -> "Manifest":
        """Create Manifest from a dictionary."""
        sources: list[SourceConfig] = []
        for s in data.get("sources", []):
            if isinstance(s, str):
                sources.append(SourceConfig(path=s))
            elif isinstance(s, dict):
                sources.append(SourceConfig(
                    path=s["path"],
                    name=s.get("name"),
                    icon=s.get("icon"),
                    order=s.get("order"),
                ))

        return cls(
            name=data.get("name"),
            description=data.get("description"),
            icon=data.get("icon"),
            sources=sources,
            path=path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, omitting None values."""
        result: dict[str, Any] = {}
        if self.name is not None:
            result["name"] = self.name
        if self.description is not None:
            result["description"] = self.description
        if self.icon is not None:
            result["icon"] = self.icon
        if self.sources:
            result["sources"] = [
                self._source_to_dict(s) for s in self.sources
            ]
        return result

    @staticmethod
    def _source_to_dict(s: SourceConfig) -> Any:
        """Serialize a SourceConfig -- plain string if only path, else dict."""
        extras = {k: v for k, v in {
            "name": s.name, "icon": s.icon, "order": s.order,
        }.items() if v is not None}
        if not extras:
            return s.path
        return {"path": s.path, **extras}


def find_manifest(path: Path) -> Optional[Path]:
    """Find manifest.yaml or manifest.yml in a directory."""
    for name in ["manifest.yaml", "manifest.yml"]:
        manifest = path / name
        if manifest.is_file():
            return manifest
    return None


def load_manifest(path: Path) -> Optional[Manifest]:
    """Load manifest from a directory. Returns None if no manifest found.

    Raises:
        ValueError: If manifest exists but is invalid YAML or not a dict.
    """
    manifest_path = find_manifest(path)
    if not manifest_path:
        return None

    try:
        content = manifest_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {manifest_path}: {e}") from e

    if not isinstance(data, dict):
        raise ValueError(f"Manifest must be a YAML mapping: {manifest_path}")

    return Manifest.from_dict(data, path=manifest_path)


def save_manifest(manifest: Manifest, path: Path) -> Path:
    """Save manifest as YAML."""
    output_path = path / "manifest.yaml"
    content = yaml.dump(manifest.to_dict(), default_flow_style=False, sort_keys=False)
    output_path.write_text(content, encoding="utf-8")
    return output_path
