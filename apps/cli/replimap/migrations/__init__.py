"""
Migration scripts for RepliMap.

This module contains migration scripts for:
- Cache sanitization (v0.4.0)
- Schema upgrades
- Data migrations
"""

from .sanitize_cache import (
    check_cache_needs_migration,
    register_migration_check,
    run_migration,
)

__all__ = [
    "check_cache_needs_migration",
    "run_migration",
    "register_migration_check",
]
