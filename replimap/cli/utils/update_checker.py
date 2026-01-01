"""
Non-blocking version update checker for RepliMap CLI.

Checks PyPI for new versions in the background and shows a notice
at the end of command execution if an update is available.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

# Configuration
CACHE_FILE = Path.home() / ".cache" / "replimap" / "version_check.json"
CACHE_TTL = 86400  # 24 hours
PYPI_URL = "https://pypi.org/pypi/replimap/json"
REQUEST_TIMEOUT = 2  # seconds

# Module state
_update_result: str | None = None
_check_thread: threading.Thread | None = None
_current_version: str = ""


def _parse_version(version_str: str) -> tuple[int, ...]:
    """
    Parse a version string into a tuple for comparison.

    Handles versions like "0.1.29", "1.0.0", "0.2.0-beta1".
    """
    # Remove any pre-release suffix
    base_version = version_str.split("-")[0].split("+")[0]

    parts = []
    for part in base_version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            # Handle non-numeric parts (e.g., "0.1.29a")
            numeric = "".join(c for c in part if c.isdigit())
            parts.append(int(numeric) if numeric else 0)

    return tuple(parts)


def _is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    try:
        return _parse_version(latest) > _parse_version(current)
    except Exception:
        # If parsing fails, fall back to string comparison
        return latest != current


def _do_check(current_version: str) -> None:
    """Background thread function to check for updates."""
    global _update_result

    try:
        # Check cache first
        if CACHE_FILE.exists():
            try:
                cache = json.loads(CACHE_FILE.read_text())
                if time.time() - cache.get("timestamp", 0) < CACHE_TTL:
                    latest = cache.get("latest_version")
                    if latest and _is_newer_version(latest, current_version):
                        _update_result = latest
                    return
            except (json.JSONDecodeError, OSError):
                pass  # Cache corrupted, continue to fetch

        # Fetch from PyPI (with short timeout)
        req = urllib.request.Request(
            PYPI_URL,
            headers={
                "Accept": "application/json",
                "User-Agent": f"replimap/{current_version}",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest = data["info"]["version"]

        # Cache result
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            CACHE_FILE.write_text(
                json.dumps({"latest_version": latest, "timestamp": time.time()})
            )
        except OSError:
            pass  # Cache write failure is non-critical

        if _is_newer_version(latest, current_version):
            _update_result = latest

    except Exception:
        pass  # Silently fail - never interrupt user


def start_update_check(current_version: str) -> None:
    """
    Start background version check (non-blocking).

    Args:
        current_version: Current installed version of replimap
    """
    global _check_thread, _current_version

    # Skip if update checking is disabled
    if os.getenv("REPLIMAP_NO_UPDATE_CHECK", "").lower() in ("1", "true", "yes"):
        return

    _current_version = current_version
    _check_thread = threading.Thread(
        target=_do_check,
        args=(current_version,),
        daemon=True,
    )
    _check_thread.start()


def show_update_notice(console: Console) -> None:
    """
    Show update notice if a new version is available.

    Call this at the end of command execution.

    Args:
        console: Rich console for output
    """
    global _check_thread, _update_result, _current_version

    # Skip if update checking is disabled
    if os.getenv("REPLIMAP_NO_UPDATE_CHECK", "").lower() in ("1", "true", "yes"):
        return

    if _check_thread:
        _check_thread.join(timeout=0.5)  # Wait max 0.5s

    if _update_result:
        from rich.panel import Panel

        console.print()
        console.print(
            Panel(
                f"[bold cyan]Update available:[/bold cyan] {_current_version} → {_update_result}\n"
                f"   Run: [bold]pip install --upgrade replimap[/bold]",
                border_style="cyan",
            )
        )


def clear_cache() -> None:
    """Clear the version check cache."""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
    except OSError:
        pass


__all__ = [
    "start_update_check",
    "show_update_notice",
    "clear_cache",
]
