"""ECHO archive HTTP server for local preview."""

import http.server
import socketserver
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .build import build_site


@dataclass
class ServeResult:
    """Result of a serve operation."""

    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that suppresses logging."""

    def log_message(self, format, *args):
        pass


def serve_directory(
    path: Path,
    port: int = 8000,
    open_browser: bool = False,
    quiet: bool = False,
) -> None:
    """Serve a directory via HTTP (blocking)."""
    path = Path(path).resolve()

    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    def make_handler(*args, **kwargs):
        return QuietHTTPHandler(*args, directory=str(path), **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), make_handler) as httpd:
        url = f"http://localhost:{port}"

        if not quiet:
            print(f"Serving at {url}")
            print("Press Ctrl+C to stop")

        if open_browser:
            webbrowser.open(url)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            if not quiet:
                print("\nStopped")


def serve_archive(
    path: Path,
    port: int = 8000,
    build_if_missing: bool = True,
    open_browser: bool = False,
    quiet: bool = False,
) -> ServeResult:
    """Serve an ECHO archive via HTTP, building the site first if needed."""
    path = Path(path).resolve()

    if not path.exists():
        return ServeResult(success=False, error=f"Path does not exist: {path}")

    if not path.is_dir():
        return ServeResult(success=False, error=f"Path is not a directory: {path}")

    site_path = path / "site"
    index_path = site_path / "index.html"

    if not index_path.exists():
        if build_if_missing:
            if not quiet:
                print(f"Building site for: {path}")

            result = build_site(path)
            if not result.success:
                return ServeResult(success=False, error=result.error)

            if not quiet:
                print(f"Built site with {result.sources_count} source(s)")
        else:
            return ServeResult(
                success=False,
                error=f"No site found at {site_path}. Run 'longecho build' first."
            )

    try:
        serve_directory(site_path, port, open_browser, quiet)
        return ServeResult(success=True, url=f"http://localhost:{port}")
    except Exception as e:
        return ServeResult(success=False, error=str(e))


def start_server_background(
    path: Path,
    port: int = 8000,
) -> tuple:
    """Start server in a background thread. Returns (server, thread, url)."""
    path = Path(path).resolve()

    def make_handler(*args, **kwargs):
        return QuietHTTPHandler(*args, directory=str(path), **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("127.0.0.1", port), make_handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    url = f"http://localhost:{port}"
    return server, thread, url
