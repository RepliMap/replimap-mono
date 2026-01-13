"""
StateManager - Runtime State Management.

State Storage: ~/.replimap/state.json
Rule: This file should be .gitignore'd

Contents:
- last_profile: Last used AWS profile
- last_region: Last used AWS region
- last_scan_time: Last scan timestamp
- cache_exists: Whether cache exists
- cache_age_hours: Age of cache in hours

Distinction from config.toml:
- config.toml: User's explicit preferences (version controlled)
- state.json: Program's automatic runtime state (gitignored)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class RuntimeState:
    """
    Runtime state that persists across sessions.

    This is automatically updated by the CLI and should NOT be
    manually edited by users. Use config.toml for user preferences.
    """

    # Session tracking
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Last used values (for smart defaults)
    last_profile: str | None = None
    last_region: str | None = None
    last_vpc_filter: str | None = None

    # Scan state
    last_scan_time: str | None = None  # ISO format
    last_scan_account: str | None = None
    last_scan_region: str | None = None
    last_scan_duration_seconds: float | None = None
    last_scan_resource_count: int | None = None

    # Cache state
    cache_exists: bool = False
    cache_age_hours: float = 0.0
    cache_path: str | None = None

    # Error tracking (for debugging)
    last_error_reference: str | None = None
    last_error_time: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to JSON-serializable dict."""
        return {
            "session_id": self.session_id,
            "last_profile": self.last_profile,
            "last_region": self.last_region,
            "last_vpc_filter": self.last_vpc_filter,
            "last_scan_time": self.last_scan_time,
            "last_scan_account": self.last_scan_account,
            "last_scan_region": self.last_scan_region,
            "last_scan_duration_seconds": self.last_scan_duration_seconds,
            "last_scan_resource_count": self.last_scan_resource_count,
            "cache_exists": self.cache_exists,
            "cache_age_hours": self.cache_age_hours,
            "cache_path": self.cache_path,
            "last_error_reference": self.last_error_reference,
            "last_error_time": self.last_error_time,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuntimeState:
        """Create state from dict (loaded from JSON)."""
        return cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            last_profile=data.get("last_profile"),
            last_region=data.get("last_region"),
            last_vpc_filter=data.get("last_vpc_filter"),
            last_scan_time=data.get("last_scan_time"),
            last_scan_account=data.get("last_scan_account"),
            last_scan_region=data.get("last_scan_region"),
            last_scan_duration_seconds=data.get("last_scan_duration_seconds"),
            last_scan_resource_count=data.get("last_scan_resource_count"),
            cache_exists=data.get("cache_exists", False),
            cache_age_hours=data.get("cache_age_hours", 0.0),
            cache_path=data.get("cache_path"),
            last_error_reference=data.get("last_error_reference"),
            last_error_time=data.get("last_error_time"),
        )


class StateManager:
    """
    Manages runtime state persistence.

    State is stored in ~/.replimap/state.json and automatically
    maintained by CLI commands. Users should not edit this file.
    """

    DEFAULT_PATH = Path.home() / ".replimap" / "state.json"

    def __init__(self, state_path: Path | None = None) -> None:
        """
        Initialize state manager.

        Args:
            state_path: Custom path for state file (defaults to ~/.replimap/state.json)
        """
        self._path = state_path or self.DEFAULT_PATH
        self._state: RuntimeState | None = None
        self._ensure_gitignore()

    @property
    def state(self) -> RuntimeState:
        """Get current runtime state (lazy-loaded)."""
        if self._state is None:
            self._state = self._load()
        return self._state

    def update(self, **kwargs: Any) -> None:
        """
        Update state with new values.

        Args:
            **kwargs: State fields to update
        """
        state = self.state
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self._save()

    def record_scan(
        self,
        profile: str | None,
        region: str,
        account_id: str | None = None,
        duration_seconds: float | None = None,
        resource_count: int | None = None,
    ) -> None:
        """
        Record a completed scan.

        Args:
            profile: AWS profile used
            region: AWS region scanned
            account_id: AWS account ID
            duration_seconds: Scan duration
            resource_count: Number of resources found
        """
        now = datetime.now(UTC).isoformat()
        self.update(
            last_profile=profile,
            last_region=region,
            last_scan_time=now,
            last_scan_account=account_id,
            last_scan_region=region,
            last_scan_duration_seconds=duration_seconds,
            last_scan_resource_count=resource_count,
        )

    def update_cache_status(
        self,
        exists: bool,
        age_hours: float = 0.0,
        path: str | None = None,
    ) -> None:
        """
        Update cache status.

        Args:
            exists: Whether cache exists
            age_hours: Age of cache in hours
            path: Path to cache file
        """
        self.update(
            cache_exists=exists,
            cache_age_hours=age_hours,
            cache_path=path,
        )

    def record_error(self, reference: str) -> None:
        """
        Record an error occurrence.

        Args:
            reference: Error reference code (e.g., "ERR-EC2-403-A7X9")
        """
        now = datetime.now(UTC).isoformat()
        self.update(
            last_error_reference=reference,
            last_error_time=now,
        )

    def clear(self) -> None:
        """Clear all state (reset to defaults)."""
        self._state = RuntimeState()
        self._save()

    def get_last_scan_info(self) -> dict[str, Any]:
        """Get information about the last scan."""
        state = self.state
        return {
            "time": state.last_scan_time,
            "account": state.last_scan_account,
            "region": state.last_scan_region,
            "duration_seconds": state.last_scan_duration_seconds,
            "resource_count": state.last_scan_resource_count,
        }

    def get_suggested_defaults(self) -> dict[str, str | None]:
        """
        Get suggested default values based on history.

        Returns:
            Dict with suggested profile, region, vpc_filter
        """
        state = self.state
        return {
            "profile": state.last_profile,
            "region": state.last_region,
            "vpc_filter": state.last_vpc_filter,
        }

    def _load(self) -> RuntimeState:
        """Load state from file."""
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
                return RuntimeState.from_dict(data)
            except (json.JSONDecodeError, OSError):
                # Return fresh state on error
                return RuntimeState()
        return RuntimeState()

    def _save(self) -> None:
        """Save state to file."""
        if self._state is None:
            return

        # Ensure directory exists
        self._path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._state.to_dict(), f, indent=2)
        except OSError:
            # Silently fail on write errors
            pass

    def _ensure_gitignore(self) -> None:
        """Ensure state directory has a .gitignore for state files."""
        create_gitignore_if_missing(self._path.parent)


def create_gitignore_if_missing(directory: Path) -> None:
    """
    Create a .gitignore in the RepliMap directory if missing.

    This prevents runtime state from being accidentally committed.

    Args:
        directory: Directory to create .gitignore in
    """
    gitignore_path = directory / ".gitignore"

    if gitignore_path.exists():
        return

    # Ensure directory exists
    directory.mkdir(parents=True, exist_ok=True)

    content = """# RepliMap runtime files - DO NOT COMMIT
# These files contain session-specific state and should not be version controlled

# Runtime state (auto-generated)
state.json

# Credential cache (sensitive)
cache/credentials.json

# Error logs (may contain sensitive info)
logs/

# Scan cache (large, session-specific)
cache/*.db
cache/*.json
"""

    try:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError:
        pass


def create_state_manager(state_path: Path | None = None) -> StateManager:
    """
    Factory function to create a StateManager.

    Args:
        state_path: Custom path for state file

    Returns:
        Configured StateManager instance
    """
    return StateManager(state_path=state_path)


__all__ = [
    "RuntimeState",
    "StateManager",
    "create_gitignore_if_missing",
    "create_state_manager",
]
