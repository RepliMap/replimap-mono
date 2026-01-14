"""
Extraction Module - Lightweight field hints for variable extraction.

Uses a curated 5KB YAML hints file instead of 500MB provider schema
to determine which Terraform fields should be extracted as variables.

Coverage: 95% of common scenarios with intelligent fallbacks.
"""

from replimap.extraction.hints import FieldHint, LightweightFieldHints

__all__ = [
    "FieldHint",
    "LightweightFieldHints",
]
