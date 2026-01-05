"""
Output formatters for RepliMap.

Provides converters to various output formats like SARIF for GitHub Security.
"""

from .sarif import SARIFGenerator

__all__ = [
    "SARIFGenerator",
]
