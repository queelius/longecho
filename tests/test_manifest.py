"""Tests for ECHO manifest handling."""

import pytest

from longecho.manifest import (
    Manifest,
    SourceConfig,
    find_manifest,
    load_manifest,
    save_manifest,
)


class TestSourceConfig:
    def test_from_string(self):
        sc = SourceConfig(path="conversations/")
        assert sc.path == "conversations/"
        assert sc.name is None
        assert sc.icon is None
        assert sc.order is None

    def test_full(self):
        sc = SourceConfig(path="data/", name="My Data", icon="\U0001F4CA", order=1)
        assert sc.name == "My Data"
        assert sc.icon == "\U0001F4CA"


class TestManifest:
    def test_empty_manifest(self):
        m = Manifest()
        assert m.name is None
        assert m.description is None
        assert m.sources == []

    def test_full_manifest(self):
        m = Manifest(
            name="Archive",
            description="My archive",
            icon="\U0001F4E6",
            sources=[SourceConfig(path="data/")],
        )
        assert m.name == "Archive"
        assert len(m.sources) == 1

    def test_from_dict_minimal(self):
        m = Manifest.from_dict({})
        assert m.name is None
        assert m.sources == []

    def test_from_dict_with_sources(self):
        m = Manifest.from_dict({
            "name": "Test",
            "sources": [
                "conversations/",
                {"path": "bookmarks/", "name": "Links", "icon": "\U0001F516"},
            ]
        })
        assert m.name == "Test"
        assert len(m.sources) == 2
        assert m.sources[0].path == "conversations/"
        assert m.sources[0].name is None
        assert m.sources[1].path == "bookmarks/"
        assert m.sources[1].name == "Links"
        assert m.sources[1].icon == "\U0001F516"

    def test_from_dict_ignores_unknown_fields(self):
        m = Manifest.from_dict({"name": "Test", "version": "1.0", "type": "database"})
        assert m.name == "Test"

    def test_to_dict_omits_none(self):
        m = Manifest(name="Test")
        d = m.to_dict()
        assert d == {"name": "Test"}
        assert "description" not in d
        assert "sources" not in d

    def test_to_dict_full(self):
        m = Manifest(
            name="Archive",
            description="Desc",
            icon="\U0001F4E6",
            sources=[SourceConfig(path="a/"), SourceConfig(path="b/", name="B")],
        )
        d = m.to_dict()
        assert d["name"] == "Archive"
        assert d["sources"][0] == "a/"
        assert d["sources"][1] == {"path": "b/", "name": "B"}


class TestFindManifest:
    def test_finds_yaml(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text("name: Test")
        assert find_manifest(tmp_path) == tmp_path / "manifest.yaml"

    def test_finds_yml(self, tmp_path):
        (tmp_path / "manifest.yml").write_text("name: Test")
        assert find_manifest(tmp_path) == tmp_path / "manifest.yml"

    def test_prefers_yaml_over_yml(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text("name: A")
        (tmp_path / "manifest.yml").write_text("name: B")
        assert find_manifest(tmp_path) == tmp_path / "manifest.yaml"

    def test_returns_none(self, tmp_path):
        assert find_manifest(tmp_path) is None

    def test_ignores_json(self, tmp_path):
        (tmp_path / "manifest.json").write_text('{"name": "Test"}')
        assert find_manifest(tmp_path) is None


class TestLoadManifest:
    def test_loads_yaml(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text("name: Test\ndescription: A test")
        m = load_manifest(tmp_path)
        assert m is not None
        assert m.name == "Test"

    def test_loads_mixed_sources(self, tmp_path):
        content = "sources:\n  - conversations/\n  - path: bookmarks/\n    name: Links"
        (tmp_path / "manifest.yaml").write_text(content)
        m = load_manifest(tmp_path)
        assert len(m.sources) == 2
        assert m.sources[0].path == "conversations/"
        assert m.sources[1].name == "Links"

    def test_returns_none_if_missing(self, tmp_path):
        assert load_manifest(tmp_path) is None

    def test_invalid_yaml_raises(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text(": : invalid: [")
        with pytest.raises(ValueError):
            load_manifest(tmp_path)

    def test_non_dict_raises(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text("- just\n- a\n- list")
        with pytest.raises(ValueError):
            load_manifest(tmp_path)

    def test_empty_manifest_loads(self, tmp_path):
        (tmp_path / "manifest.yaml").write_text("")
        # Empty YAML returns None, which is not a dict
        with pytest.raises(ValueError):
            load_manifest(tmp_path)


class TestSaveManifest:
    def test_saves_yaml(self, tmp_path):
        m = Manifest(name="Test", description="Desc")
        path = save_manifest(m, tmp_path)
        assert path == tmp_path / "manifest.yaml"
        assert path.exists()
        loaded = load_manifest(tmp_path)
        assert loaded.name == "Test"

    def test_roundtrip_with_sources(self, tmp_path):
        m = Manifest(
            name="Archive",
            sources=[
                SourceConfig(path="a/"),
                SourceConfig(path="b/", name="B", icon="\U0001F4DA"),
            ],
        )
        save_manifest(m, tmp_path)
        loaded = load_manifest(tmp_path)
        assert len(loaded.sources) == 2
        assert loaded.sources[1].name == "B"
