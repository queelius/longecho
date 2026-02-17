"""Test fixtures for longecho tests."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def echo_compliant_dir(temp_dir):
    """Create an ECHO-compliant directory."""
    (temp_dir / "README.md").write_text(
        "# Test Data Archive\n\n"
        "This is a test archive for ECHO compliance testing.\n\n"
        "## Contents\n\n"
        "Contains test data in durable formats.\n"
    )

    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "test.db").touch()
    (data_dir / "test.json").write_text('{"test": true}')
    (data_dir / "notes.md").write_text("# Notes\n\nSome notes.")

    return temp_dir


@pytest.fixture
def non_compliant_dir_no_readme(temp_dir):
    """Create a directory without README."""
    (temp_dir / "data.json").write_text('{}')
    return temp_dir


@pytest.fixture
def non_compliant_dir_no_durable(temp_dir):
    """Create a directory with README but no durable formats."""
    (temp_dir / "README.md").write_text("# Test\n\nThis is a test.")
    (temp_dir / "config.ini").write_text("[section]\nkey=value")
    (temp_dir / "script.sh").write_text("#!/bin/bash\necho hello")

    return temp_dir


@pytest.fixture
def nested_echo_sources(temp_dir):
    """Create a directory structure with multiple ECHO sources."""
    conv_dir = temp_dir / "ctk-export"
    conv_dir.mkdir()
    (conv_dir / "README.md").write_text("# AI Conversations\n\nExported conversation history.\n")
    (conv_dir / "conversations.db").touch()
    (conv_dir / "index.json").write_text("[]")

    btk_dir = temp_dir / "bookmarks"
    btk_dir.mkdir()
    (btk_dir / "README.md").write_text("# Bookmarks Archive\n\nPersonal bookmark collection.\n")
    (btk_dir / "bookmarks.jsonl").write_text("")

    blog_dir = temp_dir / "projects" / "blog"
    blog_dir.mkdir(parents=True)
    (blog_dir / "README.md").write_text("# Personal Blog\n\nMarkdown blog posts.\n")
    posts_dir = blog_dir / "posts"
    posts_dir.mkdir()
    (posts_dir / "2024-01-01-hello.md").write_text("# Hello\n\nFirst post.")

    # Non-compliant directory (should be skipped during discovery)
    other_dir = temp_dir / "other"
    other_dir.mkdir()
    (other_dir / "notes.txt").write_text("some notes")

    return temp_dir


@pytest.fixture
def echo_archive_with_manifest(temp_dir):
    """Create an ECHO archive with a manifest file."""
    import yaml

    (temp_dir / "README.md").write_text("# Test Archive\n\nA test archive with manifest.")
    (temp_dir / "manifest.yaml").write_text(yaml.dump({
        "name": "Test Archive",
        "description": "A comprehensive test archive",
        "sources": [{"path": "data/", "order": 1}],
    }, default_flow_style=False))

    data_dir = temp_dir / "data"
    data_dir.mkdir()
    (data_dir / "README.md").write_text("# Data\n\nTest data.")
    (data_dir / "test.db").touch()

    return temp_dir
