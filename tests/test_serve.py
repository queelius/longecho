"""
Tests for the ECHO serve module.
"""

import pytest
import socket
import urllib.request
from pathlib import Path
from time import sleep

from longecho.serve import (
    serve_directory,
    serve_archive,
    start_server_background,
    ServeResult,
)
from longecho.build import build_site


def find_free_port():
    """Find a free port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class TestServeResult:
    """Tests for ServeResult dataclass."""

    def test_success_result(self):
        result = ServeResult(
            success=True,
            url="http://localhost:8000"
        )
        assert result.success is True
        assert result.url is not None

    def test_failure_result(self):
        result = ServeResult(
            success=False,
            error="Path does not exist"
        )
        assert result.success is False
        assert result.error is not None


class TestStartServerBackground:
    """Tests for start_server_background function."""

    def test_starts_server(self, temp_dir):
        # Create a simple HTML file
        (temp_dir / "index.html").write_text("<html><body>Test</body></html>")

        port = find_free_port()
        server, thread, url = start_server_background(temp_dir, port)

        try:
            # Give server time to start
            sleep(0.1)

            # Try to fetch the page
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read().decode()
            assert "Test" in content
        finally:
            server.shutdown()

    def test_serves_correct_content(self, temp_dir):
        # Create test content
        (temp_dir / "index.html").write_text("<html><body>Custom Content</body></html>")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "page.html").write_text("<html><body>Subpage</body></html>")

        port = find_free_port()
        server, thread, url = start_server_background(temp_dir, port)

        try:
            sleep(0.1)

            # Fetch main page
            response = urllib.request.urlopen(url, timeout=5)
            assert "Custom Content" in response.read().decode()

            # Fetch subpage
            response = urllib.request.urlopen(f"{url}/subdir/page.html", timeout=5)
            assert "Subpage" in response.read().decode()
        finally:
            server.shutdown()


class TestServeDirectory:
    """Tests for serve_directory function."""

    def test_nonexistent_path_raises(self, temp_dir):
        """serve_directory raises ValueError for nonexistent path."""
        with pytest.raises(ValueError, match="does not exist"):
            serve_directory(temp_dir / "nonexistent")

    def test_file_path_raises(self, temp_dir):
        """serve_directory raises ValueError when path is a file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        with pytest.raises(ValueError, match="not a directory"):
            serve_directory(test_file)


class TestServeArchive:
    """Tests for serve_archive function."""

    def test_nonexistent_path(self):
        result = serve_archive(
            Path("/nonexistent/path"),
            build_if_missing=False,
        )
        assert result.success is False
        assert "does not exist" in result.error

    def test_file_path(self, temp_dir):
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        result = serve_archive(test_file, build_if_missing=False)
        assert result.success is False
        assert "not a directory" in result.error

    def test_no_site_without_build(self, echo_compliant_dir):
        # Without building first, no site/ exists
        result = serve_archive(
            echo_compliant_dir,
            build_if_missing=False,
        )
        assert result.success is False
        assert "No site found" in result.error or "site" in result.error.lower()


class TestServeIntegration:
    """Integration tests for serve functionality."""

    def test_build_and_serve(self, echo_compliant_dir):
        # Build the site first
        build_result = build_site(echo_compliant_dir)
        assert build_result.success is True

        # Now start server
        site_path = echo_compliant_dir / "site"
        port = find_free_port()
        server, thread, url = start_server_background(site_path, port)

        try:
            sleep(0.1)

            # Fetch the index
            response = urllib.request.urlopen(url, timeout=5)
            content = response.read().decode()

            # Should have the archive content
            assert "<!DOCTYPE html>" in content or "<html" in content
        finally:
            server.shutdown()
