"""Tests for README parsing with frontmatter extraction."""

import datetime

from longecho.checker import parse_readme, split_frontmatter


class TestSplitFrontmatter:
    """Tests for split_frontmatter function."""

    def test_no_frontmatter(self):
        fm, body = split_frontmatter("# Title\n\nContent here.")
        assert fm is None
        assert body == "# Title\n\nContent here."

    def test_yaml_frontmatter(self):
        content = "---\ntitle: Hello\ndate: 2024-01-15\n---\n# Title\n\nContent."
        fm, body = split_frontmatter(content)
        assert fm == {"title": "Hello", "date": datetime.date(2024, 1, 15)}
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
