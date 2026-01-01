"""
Global signal handling for graceful shutdown.

Install handlers once at CLI startup to ensure clean Ctrl-C handling
across all commands without ugly threading tracebacks.
"""

from __future__ import annotations

import logging
import os
import signal
from types import FrameType
from typing import TYPE_CHECKING, Any

from replimap.core.concurrency import shutdown_all_executors

if TYPE_CHECKING:
    from rich.console import Console

logger = logging.getLogger(__name__)

_console: Console | None = None
# Saved original handler for potential restoration (unused currently)
_original_sigint_handler: Any = None


def setup_signal_handlers(console: Console) -> None:
    """
    Install global signal handlers.

    Call this once at CLI startup (in main.py).

    Args:
        console: Rich console for output (needed to restore cursor)
    """
    global _console, _original_sigint_handler
    _console = console

    # Save original handler (in case we need to restore)
    _original_sigint_handler = signal.getsignal(signal.SIGINT)

    # Install our handlers
    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigterm)


def _handle_sigint(signum: int, frame: FrameType | None) -> None:
    """
    Handle Ctrl-C (SIGINT).

    Strategy:
    1. Show user feedback
    2. Shutdown all thread pools
    3. Hard exit (skip Python cleanup to avoid threading tracebacks)
    """
    if _console:
        # Restore cursor (spinners may have hidden it)
        _console.show_cursor()
        _console.print("\n[yellow]Cancelled by user[/yellow]")

    # Shutdown all tracked executors
    count = shutdown_all_executors(wait=False)
    logger.debug(f"Shut down {count} executor(s)")

    # Hard exit - skip Python's cleanup to avoid threading exceptions
    # Exit code 130 = 128 + SIGINT(2), standard Unix convention
    os._exit(130)


def _handle_sigterm(signum: int, frame: FrameType | None) -> None:
    """Handle SIGTERM (kill command, Docker stop, etc.)."""
    if _console:
        _console.show_cursor()
        _console.print("\n[yellow]Terminated[/yellow]")

    shutdown_all_executors(wait=False)
    os._exit(143)  # 128 + SIGTERM(15)
