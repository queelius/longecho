"""
Tests for the ECHO manifest module.
"""

import json
import pytest
from pathlib import Path

from longecho.manifest import (
    find_manifest,
    load_manifest_data,
    validate_manifest_data,
    load_manifest,
    create_minimal_manifest,
    save_manifest,
    Manifest,
    SourceConfig,
)


class TestFindManifest:
    """Tests for find_manifest function."""

    def test_finds_manifest_json(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text('{"version": "1.0"}')

        result = find_manifest(temp_dir)
        assert result == manifest

    def test_finds_manifest_yaml(self, temp_dir):
        manifest = temp_dir / "manifest.yaml"
        manifest.write_text("version: '1.0'")

        result = find_manifest(temp_dir)
        assert result == manifest

    def test_prefers_json_over_yaml(self, temp_dir):
        (temp_dir / "manifest.json").write_text('{"version": "1.0"}')
        (temp_dir / "manifest.yaml").write_text("version: '1.0'")

        result = find_manifest(temp_dir)
        assert result.name == "manifest.json"

    def test_returns_none_if_missing(self, temp_dir):
        result = find_manifest(temp_dir)
        assert result is None


class TestLoadManifestData:
    """Tests for load_manifest_data function."""

    def test_loads_json(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text('{"version": "1.0", "name": "Test", "description": "A test"}')

        data = load_manifest_data(manifest)
        assert data["version"] == "1.0"
        assert data["name"] == "Test"

    def test_invalid_json_raises(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text("{invalid json}")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_manifest_data(manifest)


class TestValidateManifestData:
    """Tests for validate_manifest_data function."""

    def test_valid_minimal_manifest(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test archive"
        }
        errors = validate_manifest_data(data)
        assert len(errors) == 0

    def test_missing_version(self):
        data = {"name": "Test", "description": "A test"}
        errors = validate_manifest_data(data)
        assert any("version" in e for e in errors)

    def test_missing_name(self):
        data = {"version": "1.0", "description": "A test"}
        errors = validate_manifest_data(data)
        assert any("name" in e for e in errors)

    def test_missing_description(self):
        data = {"version": "1.0", "name": "Test"}
        errors = validate_manifest_data(data)
        assert any("description" in e for e in errors)

    def test_invalid_version(self):
        data = {"version": "2.0", "name": "Test", "description": "A test"}
        errors = validate_manifest_data(data)
        assert any("version" in e.lower() for e in errors)

    def test_invalid_type(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test",
            "type": "invalid"
        }
        errors = validate_manifest_data(data)
        assert any("type" in e.lower() for e in errors)

    def test_valid_type(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test",
            "type": "database"
        }
        errors = validate_manifest_data(data)
        assert not any("type" in e.lower() for e in errors)

    def test_sources_must_be_array(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test",
            "sources": "not an array"
        }
        errors = validate_manifest_data(data)
        assert any("sources" in e.lower() for e in errors)

    def test_sources_require_path(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test",
            "sources": [{"order": 1}]
        }
        errors = validate_manifest_data(data)
        assert any("path" in e.lower() for e in errors)


class TestLoadManifest:
    """Tests for load_manifest function."""

    def test_loads_valid_manifest(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text(json.dumps({
            "version": "1.0",
            "name": "Test Archive",
            "description": "A test archive"
        }))

        result = load_manifest(temp_dir)
        assert result is not None
        assert result.name == "Test Archive"
        assert result.version == "1.0"

    def test_returns_none_if_no_manifest(self, temp_dir):
        result = load_manifest(temp_dir)
        assert result is None

    def test_raises_on_invalid_manifest(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text('{"version": "1.0"}')  # Missing name and description

        with pytest.raises(ValueError):
            load_manifest(temp_dir)

    def test_loads_with_sources(self, temp_dir):
        manifest = temp_dir / "manifest.json"
        manifest.write_text(json.dumps({
            "version": "1.0",
            "name": "Test",
            "description": "Test",
            "sources": [
                {"path": "source1/", "order": 1},
                {"path": "source2/", "order": 2, "browsable": False}
            ]
        }))

        result = load_manifest(temp_dir)
        assert len(result.sources) == 2
        assert result.sources[0].path == "source1/"
        assert result.sources[0].order == 1
        assert result.sources[1].browsable is False


class TestManifest:
    """Tests for Manifest dataclass."""

    def test_from_dict(self):
        data = {
            "version": "1.0",
            "name": "Test",
            "description": "A test",
            "type": "database",
            "browsable": True,
            "icon": "chat"
        }
        manifest = Manifest.from_dict(data)
        assert manifest.name == "Test"
        assert manifest.type == "database"
        assert manifest.icon == "chat"

    def test_to_dict(self):
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="A test",
            type="database",
            icon="chat"
        )
        data = manifest.to_dict()
        assert data["version"] == "1.0"
        assert data["name"] == "Test"
        assert data["type"] == "database"

    def test_to_dict_omits_none(self):
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="A test"
        )
        data = manifest.to_dict()
        assert "type" not in data
        assert "icon" not in data

    def test_browsable_defaults_to_true(self):
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="A test"
        )
        assert manifest.browsable is True


class TestSourceConfig:
    """Tests for SourceConfig dataclass."""

    def test_from_dict_minimal(self):
        data = {"path": "source/"}
        config = SourceConfig.from_dict(data)
        assert config.path == "source/"
        assert config.order is None

    def test_from_dict_full(self):
        data = {
            "path": "source/",
            "order": 1,
            "browsable": False,
            "name": "Custom Name"
        }
        config = SourceConfig.from_dict(data)
        assert config.path == "source/"
        assert config.order == 1
        assert config.browsable is False
        assert config.name == "Custom Name"


class TestCreateMinimalManifest:
    """Tests for create_minimal_manifest function."""

    def test_creates_manifest(self):
        manifest = create_minimal_manifest("Test", "A test archive")
        assert manifest.version == "1.0"
        assert manifest.name == "Test"
        assert manifest.description == "A test archive"


class TestSaveManifest:
    """Tests for save_manifest function."""

    def test_save_json(self, temp_dir):
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="A test"
        )
        path = save_manifest(manifest, temp_dir, format="json")

        assert path.name == "manifest.json"
        assert path.exists()

        content = json.loads(path.read_text())
        assert content["name"] == "Test"

    def test_save_creates_valid_json(self, temp_dir):
        manifest = Manifest(
            version="1.0",
            name="Test",
            description="A test",
            type="database",
            sources=[
                SourceConfig(path="source1/", order=1),
                SourceConfig(path="source2/", browsable=False)
            ]
        )
        path = save_manifest(manifest, temp_dir)

        # Reload and verify
        loaded = load_manifest(temp_dir)
        assert loaded.name == "Test"
        assert len(loaded.sources) == 2
