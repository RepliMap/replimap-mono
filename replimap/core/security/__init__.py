"""
Security module for RepliMap.

Provides tools for detecting and preventing sensitive data leakage
in generated Infrastructure-as-Code.
"""

from .scrubber import SecretScrubber

__all__ = ["SecretScrubber"]
