"""
Cross-platform browser launcher with WSL2 support.

Handles opening files in browser across:
- WSL2 (Windows Subsystem for Linux)
- macOS
- Linux Desktop
- Windows Native

The WSL2 implementation uses wslpath + cmd.exe to convert Linux paths
to Windows paths and open them in the default Windows browser.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)


def is_wsl() -> bool:
    """
    Detect if running inside WSL/WSL2.

    Returns:
        True if running in WSL, False otherwise
    """
    if sys.platform != "linux":
        return False
    try:
        release = os.uname().release.lower()
        return "microsoft" in release or "wsl" in release
    except Exception:
        return False


def open_in_browser(
    file_path: str | Path,
    console: Console | None = None,
    quiet: bool = False,
) -> bool:
    """
    Open a file in the default browser, with smart WSL2 handling.

    Args:
        file_path: Path to the file to open (can be file path or URL)
        console: Optional Rich Console for output
        quiet: If True, suppress "Opening in browser" message

    Returns:
        True if successfully opened, False otherwise
    """
    # Handle URLs directly
    if isinstance(file_path, str) and file_path.startswith(("http://", "https://")):
        return _open_url(file_path, console)

    path = Path(file_path).resolve()

    if not path.exists():
        if console:
            console.print(f"[red]File not found: {path}[/red]")
        return False

    if not quiet and console:
        console.print("[dim]Opening in browser...[/dim]")

    if is_wsl():
        return _open_wsl(path, console)
    else:
        return _open_native(path, console)


def _open_url(url: str, console: Console | None = None) -> bool:
    """
    Open a URL in the default browser.

    Args:
        url: The URL to open
        console: Optional Rich Console for output

    Returns:
        True if successfully opened, False otherwise
    """
    import webbrowser

    try:
        if is_wsl():
            # In WSL, use cmd.exe to open URLs
            # S603: subprocess with fixed command, not user input
            subprocess.run(  # noqa: S603
                ["cmd.exe", "/C", "start", "", url],
                check=True,
                cwd="/mnt/c/",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        else:
            webbrowser.open(url)
            return True
    except Exception as e:
        logger.error(f"Failed to open URL: {e}")
        if console:
            console.print(f"[yellow]Could not open URL: {url}[/yellow]")
        return False


def _open_wsl(path: Path, console: Console | None = None) -> bool:
    """
    Open file in Windows browser from WSL2.

    Strategy:
    1. Try wslview (requires wslu package, best compatibility)
    2. Fallback to wslpath + cmd.exe (zero dependencies)

    Args:
        path: The file path to open
        console: Optional Rich Console for output

    Returns:
        True if successfully opened, False otherwise
    """
    # Method 1: Try wslview (if wslu is installed)
    if shutil.which("wslview"):
        try:
            logger.debug("Using wslview to open browser")
            # S603: wslview is a known WSL utility
            subprocess.run(  # noqa: S603
                ["wslview", str(path)],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.debug(f"wslview failed: {e}")
            # Fall through to method 2

    # Method 2: Use wslpath + cmd.exe (always available in WSL)
    try:
        logger.debug("Using wslpath + cmd.exe to open browser")

        # Convert Linux path to Windows UNC path
        # /home/user/file.html → \\wsl$\Ubuntu\home\user\file.html
        # S603: wslpath is a known WSL utility
        result = subprocess.run(  # noqa: S603
            ["wslpath", "-w", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
        win_path = result.stdout.strip()

        # Use Windows 'start' command
        # Key optimizations:
        # - cwd="/mnt/c/" eliminates "UNC paths not supported" warning
        # - Empty "" is required as window title when path has spaces
        # - DEVNULL silences any cmd.exe output
        # S603: subprocess with fixed command, not user input
        subprocess.run(  # noqa: S603
            ["cmd.exe", "/C", "start", "", win_path],
            check=True,
            cwd="/mnt/c/",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open browser via cmd.exe: {e}")
        _print_manual_instructions(path, console)
        return False
    except FileNotFoundError:
        logger.error("cmd.exe not found")
        _print_manual_instructions(path, console)
        return False


def _open_native(path: Path, console: Console | None = None) -> bool:
    """
    Open file in browser on native OS (macOS, Linux, Windows).

    Args:
        path: The file path to open
        console: Optional Rich Console for output

    Returns:
        True if successfully opened, False otherwise
    """
    import webbrowser

    try:
        # Use file:// URL format for webbrowser
        file_url = f"file://{path}"
        webbrowser.open(file_url)
        return True
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        _print_manual_instructions(path, console)
        return False


def _print_manual_instructions(path: Path, console: Console | None = None) -> None:
    """
    Print instructions for manual opening when auto-open fails.

    Args:
        path: The file path that couldn't be opened
        console: Optional Rich Console for output
    """
    if console is None:
        return

    console.print()
    console.print("[yellow]Could not open browser automatically.[/yellow]")
    console.print("Please open this file manually:")
    console.print(f"  [cyan]{path}[/cyan]")

    if is_wsl():
        # Also show Windows-accessible path for WSL users
        try:
            # S603: wslpath is a known WSL utility
            result = subprocess.run(  # noqa: S603
                ["wslpath", "-w", str(path)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                win_path = result.stdout.strip()
                console.print(f"  [dim]Windows: {win_path}[/dim]")
        except Exception:  # noqa: S110
            # Silently ignore errors when showing optional Windows path
            pass
