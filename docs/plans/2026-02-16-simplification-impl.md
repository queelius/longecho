# longecho Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify longecho by unifying data models, simplifying the manifest to YAML-only with all-optional fields, adding README frontmatter parsing, and focusing the spec directory.

**Architecture:** Replace three source representations (ComplianceResult fields, EchoSource, SourceInfo) with one unified EchoSource. Add Readme parsing with frontmatter extraction. Simplify Manifest to YAML-only, all-optional. Cascade: manifest > frontmatter > README heading/paragraph > dirname.

**Tech Stack:** Python 3.9+, PyYAML (promoted to core dep), pytest, mypy, ruff

**Design doc:** `docs/plans/2026-02-16-simplification-design.md`

---

### Task 1: Add README parsing with frontmatter extraction

New functions in `src/longecho/checker.py`. Pure addition — no existing code changes yet.

**Files:**
- Modify: `src/longecho/checker.py` (add Readme, split_frontmatter, parse_readme)
- Create: `tests/test_readme.py`

**Step 1: Write tests for split_frontmatter**

Create `tests/test_readme.py`:

```python
"""Tests for README parsing with frontmatter extraction."""

import pytest
from pathlib import Path
from longecho.checker import Readme, split_frontmatter, parse_readme


class TestSplitFrontmatter:
    """Tests for split_frontmatter function."""

    def test_no_frontmatter(self):
        fm, body = split_frontmatter("# Title\n\nContent here.")
        assert fm is None
        assert body == "# Title\n\nContent here."

    def test_yaml_frontmatter(self):
        content = "---\ntitle: Hello\ndate: 2024-01-15\n---\n# Title\n\nContent."
        fm, body = split_frontmatter(content)
        assert fm == {"title": "Hello", "date": "2024-01-15"}
        assert body.strip() == "# Title\n\nContent."

    def test_empty_frontmatter(self):
        content = "---\n---\n# Title"
        fm, body = split_frontmatter(content)
        assert fm is None  # empty YAML returns None
        assert "# Title" in body

    def test_no_closing_delimiter(self):
        content = "---\ntitle: Hello\n# No closing delimiter"
        fm, body = split_frontmatter(content)
        assert fm is None  # malformed = no frontmatter
        assert content == body  # return original content as body

    def test_frontmatter_must_start_at_beginning(self):
        content = "Some text\n---\ntitle: Hello\n---\nMore text"
        fm, body = split_frontmatter(content)
        assert fm is None
        assert body == content


class TestParseReadme:
    """Tests for parse_readme function."""

    def test_simple_readme(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# My Project\n\nA great project.\n\nMore details.")
        result = parse_readme(readme)
        assert result is not None
        assert result.title == "My Project"
        assert result.summary == "A great project."

    def test_readme_with_frontmatter(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "---\ntitle: Custom Title\ndescription: Custom desc\n---\n"
            "# Heading\n\nFirst paragraph."
        )
        result = parse_readme(readme)
        assert result.frontmatter == {"title": "Custom Title", "description": "Custom desc"}
        assert result.title == "Heading"
        assert result.summary == "First paragraph."

    def test_no_heading(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("Just a paragraph with no heading.")
        result = parse_readme(readme)
        assert result.title is None
        assert result.summary == "Just a paragraph with no heading."

    def test_multiline_paragraph(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\nFirst line\nsecond line.\n\nSecond paragraph.")
        result = parse_readme(readme)
        assert result.summary == "First line second line."

    def test_nonexistent_file(self, tmp_path):
        result = parse_readme(tmp_path / "NOPE.md")
        assert result is None

    def test_skips_subheadings_before_paragraph(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\n## Section\n\nActual content.")
        result = parse_readme(readme)
        assert result.title == "Title"
        assert result.summary == "Actual content."

    def test_summary_truncation(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Title\n\n" + "x" * 600)
        result = parse_readme(readme)
        assert len(result.summary) <= 500
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_readme.py -v`
Expected: ImportError — split_frontmatter and Readme don't exist yet

**Step 3: Implement split_frontmatter, Readme, parse_readme**

Add to `src/longecho/checker.py` (after imports, before existing dataclasses):

```python
import yaml

@dataclass
class Readme:
    """A README parsed into its constituent parts."""
    frontmatter: Optional[dict]
    body: str
    title: Optional[str]
    summary: Optional[str]


def split_frontmatter(content: str) -> tuple[Optional[dict], str]:
    """Split YAML frontmatter from markdown content.

    Frontmatter must start at the very beginning of the content,
    delimited by --- lines.

    Returns:
        (frontmatter dict or None, remaining content)
    """
    if not content.startswith("---"):
        return None, content

    lines = content.split("\n")
    # Find closing ---
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            yaml_content = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            try:
                parsed = yaml.safe_load(yaml_content)
                if isinstance(parsed, dict):
                    return parsed, body
                return None, body
            except yaml.YAMLError:
                return None, body

    # No closing delimiter found
    return None, content


def parse_readme(readme_path: Path) -> Optional[Readme]:
    """Parse a README into frontmatter, title, and summary.

    Returns None if the file can't be read.
    """
    try:
        content = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    frontmatter, body = split_frontmatter(content)

    title = None
    summary_lines: list[str] = []
    in_paragraph = False

    for line in body.split("\n"):
        stripped = line.strip()

        # Extract first # heading as title
        if stripped.startswith("# ") and title is None:
            title = stripped[2:].strip()
            continue

        # Skip other headings
        if stripped.startswith("#"):
            if summary_lines:
                break  # hit next section, stop collecting
            continue

        # Empty line ends paragraph
        if not stripped:
            if in_paragraph:
                break
            continue

        in_paragraph = True
        summary_lines.append(stripped)

    summary = " ".join(summary_lines)[:500] if summary_lines else None
    return Readme(frontmatter=frontmatter, body=body, title=title, summary=summary)
```

Also add `yaml` to the imports at top of checker.py (replacing the conditional import).

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_readme.py -v`
Expected: All pass

**Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All 114 existing tests still pass (we only added code)

**Step 6: Commit**

```bash
git add tests/test_readme.py src/longecho/checker.py
git commit -m "feat: add README parsing with frontmatter extraction"
```

---

### Task 2: Simplify Manifest to YAML-only, all-optional

Rewrite manifest.py. Drop version/type/browsable/site/docs fields, JSON support, jsonschema.

**Files:**
- Rewrite: `src/longecho/manifest.py`
- Rewrite: `tests/test_manifest.py`

**Step 1: Write new manifest tests**

Rewrite `tests/test_manifest.py`:

```python
"""Tests for simplified ECHO manifest handling."""

import pytest
from pathlib import Path
from longecho.manifest import Manifest, SourceConfig, find_manifest, load_manifest, save_manifest


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
```

**Step 2: Run new tests to see them fail**

Run: `pytest tests/test_manifest.py -v`
Expected: Many failures — API has changed

**Step 3: Rewrite manifest.py**

Replace entire contents of `src/longecho/manifest.py`:

```python
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
        """Serialize a SourceConfig — plain string if only path, else dict."""
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
```

**Step 4: Run manifest tests**

Run: `pytest tests/test_manifest.py -v`
Expected: All pass

**Step 5: Commit**

```bash
git add src/longecho/manifest.py tests/test_manifest.py
git commit -m "feat: simplify manifest to YAML-only, all fields optional"
```

---

### Task 3: Unify data model — ComplianceResult + EchoSource

Rewrite checker.py: ComplianceResult carries EchoSource, remove extract_first_paragraph, use parse_readme.

**Files:**
- Modify: `src/longecho/checker.py`
- Modify: `tests/test_checker.py`

**Step 1: Update checker tests**

Key changes to `tests/test_checker.py`:
- Remove `TestExtractFirstParagraph` class (replaced by parse_readme tests)
- Update `TestCheckCompliance` to check `result.source` instead of `result.readme_summary` / `result.durable_formats`
- ComplianceResult no longer has readme_path, readme_summary, formats, durable_formats — those live on source

Update test assertions:
```python
# Old:
assert result.readme_summary is not None
assert result.durable_formats == [".db"]

# New:
assert result.source is not None
assert result.source.durable_formats == [".db"]
assert result.source.name == "source1"  # from README title or dirname
```

**Step 2: Rewrite checker.py data model**

Move `EchoSource` into checker.py (it was in discovery.py). New ComplianceResult:

```python
@dataclass
class EchoSource:
    """An ECHO-compliant data source."""
    path: Path
    readme_path: Path
    name: str
    description: str
    formats: list[str] = field(default_factory=list)
    durable_formats: list[str] = field(default_factory=list)
    icon: Optional[str] = None
    order: int = 0
    has_site: bool = False
    site_path: Optional[Path] = None

    def __str__(self) -> str:
        desc = self.description or "No description"
        if len(desc) > 60:
            desc = desc[:57] + "..."
        return f"{self.path}: {desc}"


@dataclass
class ComplianceResult:
    compliant: bool
    path: Path
    reason: Optional[str] = None
    source: Optional[EchoSource] = None

    def __str__(self) -> str:
        if self.compliant:
            return f"ECHO-compliant: {self.path}"
        return f"Not ECHO-compliant: {self.path} ({self.reason})"
```

Update `check_compliance` to build `EchoSource` when compliant:

```python
def check_compliance(path: Path) -> ComplianceResult:
    path = Path(path).resolve()

    if not path.exists():
        return ComplianceResult(compliant=False, path=path, reason="Path does not exist")
    if not path.is_dir():
        return ComplianceResult(compliant=False, path=path, reason="Path is not a directory")

    readme_file = find_readme(path)
    if not readme_file:
        return ComplianceResult(compliant=False, path=path, reason="No README.md or README.txt found")

    formats = detect_formats(path)
    durable = [f for f in formats if is_durable_format(f)]

    if not durable:
        return ComplianceResult(compliant=False, path=path, reason="No durable data formats found")

    # Parse README for name/description
    readme = parse_readme(readme_file)
    name = (readme.title if readme else None) or path.name
    description = (readme.summary if readme else None) or ""

    # Check for frontmatter overrides
    if readme and readme.frontmatter:
        fm = readme.frontmatter
        name = fm.get("title", name)
        description = fm.get("description", description)

    # Check for site/
    has_site = False
    site_path = None
    site_dir = path / "site"
    if site_dir.exists() and (site_dir / "index.html").exists():
        has_site = True
        site_path = site_dir

    source = EchoSource(
        path=path,
        readme_path=readme_file,
        name=name,
        description=description,
        formats=formats,
        durable_formats=durable,
        icon=readme.frontmatter.get("icon") if readme and readme.frontmatter else None,
        has_site=has_site,
        site_path=site_path,
    )

    return ComplianceResult(compliant=True, path=path, source=source)
```

Remove `extract_first_paragraph` function entirely.

**Step 3: Run checker tests**

Run: `pytest tests/test_checker.py tests/test_readme.py -v`
Expected: All pass

**Step 4: Commit**

```bash
git add src/longecho/checker.py tests/test_checker.py
git commit -m "feat: unify EchoSource into ComplianceResult, use parse_readme"
```

---

### Task 4: Simplify discovery.py

Use ComplianceResult.source directly. Remove duplicate EchoSource construction.

**Files:**
- Modify: `src/longecho/discovery.py`
- Modify: `tests/test_discovery.py`

**Step 1: Update discovery.py**

- Remove the `EchoSource` dataclass (now in checker.py)
- Import `EchoSource` from checker
- `discover_sources`: yield `result.source` directly instead of constructing EchoSource
- `get_source_info`: return `result.source` directly
- `search_sources`: use `source.description` instead of `source.readme_summary`

**Step 2: Update discovery tests**

- Import `EchoSource` from `longecho.checker` instead of `longecho.discovery`
- Update assertions: `source.readme_summary` → `source.description`

**Step 3: Run tests**

Run: `pytest tests/test_discovery.py -v`
Expected: All pass

**Step 4: Commit**

```bash
git add src/longecho/discovery.py tests/test_discovery.py
git commit -m "refactor: simplify discovery to use ComplianceResult.source"
```

---

### Task 5: Simplify build.py and templates

Remove SourceInfo, ICON_EMOJI_MAP, get_icon_emoji. Use EchoSource directly. Update templates.

**Files:**
- Modify: `src/longecho/build.py`
- Modify: `src/longecho/templates/index.html`
- Modify: `src/longecho/templates/source.html`
- Modify: `tests/test_build.py`

**Step 1: Update templates**

index.html changes:
- `{{ source.icon_emoji }}` → `{{ source.icon or '\U0001F4C1' }}`
- Remove `{% if source.type %}` block (type is gone)
- `{{ source.formats }}` → `{{ source.durable_formats }}`

source.html changes:
- `{{ icon_emoji }}` → `{{ icon or '\U0001F4C1' }}`
- Remove `{% if type %}` block
- `{{ formats }}` → `{{ durable_formats }}`

**Step 2: Rewrite build.py**

- Remove: `SourceInfo`, `ICON_EMOJI_MAP`, `get_icon_emoji`, `_build_source_info`
- Import `EchoSource` from checker
- `_load_sub_manifest` stays (it's clean)
- `_get_site_info` is absorbed into check_compliance now — remove
- `discover_sub_sources` returns `list[EchoSource]` — apply manifest overrides directly to source fields
- `build_source_page` takes `EchoSource` instead of `SourceInfo`
- `build_site` passes EchoSource attributes to templates
- Remove `deep` parameter (never used)

**Step 3: Update build tests**

- Remove `TestGetIconEmoji` class
- Remove imports: `get_icon_emoji`, `SourceInfo`, `ICON_EMOJI_MAP`
- Import `EchoSource` from checker
- Update `TestSourceInfo` → `TestEchoSource` (test default values)

**Step 4: Run tests**

Run: `pytest tests/test_build.py -v`
Expected: All pass

**Step 5: Run full suite**

Run: `pytest tests/ -v`
Expected: All pass

**Step 6: Commit**

```bash
git add src/longecho/build.py src/longecho/templates/ tests/test_build.py
git commit -m "refactor: use EchoSource directly in build, remove SourceInfo"
```

---

### Task 6: Update CLI, exports, and dependencies

**Files:**
- Modify: `src/longecho/cli.py`
- Modify: `src/longecho/__init__.py`
- Modify: `pyproject.toml`

**Step 1: Update cli.py**

- `check` command: access `result.source.description` instead of `result.readme_summary`, `result.source.durable_formats` instead of `result.durable_formats`
- `discover` command: `source.description` instead of `source.readme_summary`
- `search` command: same change
- `info` command: `source.description` instead of `source.readme_summary`
- `build` command: remove `deep` parameter
- Update docstring for build to say "manifest.yaml" not "manifest.json/yaml"

**Step 2: Update __init__.py**

```python
from .checker import ComplianceResult, EchoSource, Readme, check_compliance, parse_readme
from .discovery import discover_sources
from .manifest import Manifest, SourceConfig, load_manifest
from .build import BuildResult, build_site
```

Remove `EchoSource` import from discovery (it's now in checker).

**Step 3: Update pyproject.toml**

- Move `pyyaml>=6.0.0` from `[project.optional-dependencies] full` to `dependencies`
- Remove `jsonschema>=4.0.0` from `full`
- Remove `"black>=23.0.0"` and `"flake8>=6.0.0"` from dev (we use ruff)
- Remove `/schemas` from `[tool.hatch.build.targets.sdist] include`
- Remove `[tool.hatch.build.targets.wheel.shared-data]` section (no more schemas)

**Step 4: Run CLI tests**

Run: `pytest tests/test_cli.py -v`
Expected: All pass

**Step 5: Run full suite + tools**

Run: `pytest tests/ -v --cov=src/longecho --cov-report=term-missing`
Run: `ruff check src/longecho/`
Run: `mypy src/longecho/`

**Step 6: Commit**

```bash
git add src/longecho/__init__.py src/longecho/cli.py pyproject.toml
git commit -m "refactor: update CLI, exports, and dependencies"
```

---

### Task 7: Clean up spec files and schemas

**Files:**
- Delete: `spec/PERSONA-TK.md`
- Delete: `spec/STONE-TK.md`
- Delete: `spec/MANIFEST-SCHEMA.md`
- Delete: `schemas/manifest.schema.json`
- Move: `spec/INTERVIEW-INSIGHTS.md` → `DESIGN-NOTES.md`
- Modify: `spec/ECHO.md` (remove "Optional: Web Presentation" section)
- Modify: `spec/LONGECHO.md` (absorb manifest spec, update for YAML-only)
- Modify: `spec/index.md` (update links)
- Modify: `spec/TOOLKIT-ECOSYSTEM.md` (remove references to deleted specs)
- Modify: `mkdocs.yml` (update nav)

**Step 1: Delete files**

```bash
rm spec/PERSONA-TK.md spec/STONE-TK.md spec/MANIFEST-SCHEMA.md
rm -rf schemas/
mv spec/INTERVIEW-INSIGHTS.md DESIGN-NOTES.md
```

**Step 2: Update ECHO.md**

Remove everything from "## Optional: Web Presentation" through end of that section (lines ~95-157). Keep the "What ECHO Is Not" section. Update "Related" links to remove deleted files.

**Step 3: Update LONGECHO.md**

Add "## Archive Conventions" section covering:
- The site/ directory
- The manifest (YAML-only, all-optional, with examples)
- Hierarchical archives
- Source config in manifests

Remove references to manifest.json. Update all examples to YAML.

**Step 4: Update index.md, TOOLKIT-ECOSYSTEM.md, mkdocs.yml**

Remove links to deleted specs. Update navigation.

**Step 5: Commit**

```bash
git add -A spec/ schemas/ DESIGN-NOTES.md mkdocs.yml
git commit -m "docs: focus spec directory, simplify ECHO/LONGECHO separation"
```

---

### Task 8: Update test fixtures and conftest

Existing test fixtures use `manifest.json`. Update to `manifest.yaml`.

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/test_build.py` (fixtures that create manifest.json)

**Step 1: Update conftest.py**

Change any `manifest.json` fixture creation to `manifest.yaml` with YAML content.

**Step 2: Update test_build.py fixtures**

The `echo_compliant_with_sources` fixture writes `manifest.json` with `json.dumps`. Change to write `manifest.yaml` with `yaml.dump`.

**Step 3: Run full suite**

Run: `pytest tests/ -v --cov=src/longecho --cov-report=term-missing`
Expected: All pass

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: update fixtures from manifest.json to manifest.yaml"
```

---

### Task 9: Final verification and cleanup

**Step 1: Full test suite with coverage**

Run: `pytest tests/ -v --cov=src/longecho --cov-report=term-missing`
Expected: All tests pass, coverage >= 78%

**Step 2: Type checking**

Run: `mypy src/longecho/`
Expected: 0 errors

**Step 3: Linting**

Run: `ruff check src/longecho/`
Expected: All checks passed

**Step 4: Integration tests**

```bash
longecho check .
longecho discover .
longecho --help
longecho build .  # should work with the repo itself
```

**Step 5: Install and verify**

```bash
pip install -e ".[dev]"
```

**Step 6: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup after simplification"
```
