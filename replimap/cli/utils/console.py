"""
Shared Rich console instance for CLI output.

This module provides a centralized console instance used across
all CLI commands for consistent output formatting.
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

# Global console instance
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)

logger = logging.getLogger("replimap")


def get_console() -> Console:
    """Get the shared console instance."""
    return console


def get_logger() -> logging.Logger:
    """Get the shared logger instance."""
    return logger
