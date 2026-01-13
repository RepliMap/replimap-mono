"""
Shared Rich console instance for CLI output.

This module provides a centralized console instance used across
all CLI commands for consistent output formatting.

V3 Architecture Note:
- Stdout hygiene is enforced via OutputManager (not console)
- For JSON mode, OutputManager.present() is the only stdout writer
- Console is used for progress/status in text mode (goes to stdout)
- New commands should prefer OutputManager over direct console usage
"""

from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

# Global console instance for Rich output
# Note: For JSON mode stdout hygiene, use OutputManager.present() for final output
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
