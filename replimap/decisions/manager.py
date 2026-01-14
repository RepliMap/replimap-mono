"""
Decision Manager with TTL - Tracks user decisions with expiration.

Key Features:
1. All suppression decisions (skip/ignore) expire in 30 days
2. Extraction decisions expire in 90 days
3. Permanent decisions require explicit --permanent flag
4. Expired decisions trigger re-confirmation

File Location: ~/.replimap/decisions.yaml
"""

from __future__ import annotations

import fcntl
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from replimap.decisions.models import (
    DEFAULT_TTL_DAYS,
    Decision,
    DecisionManifest,
    DecisionType,
)


class DecisionManager:
    """
    Manages user decisions with TTL support.

    Decisions are stored in a YAML file (~/.replimap/decisions.yaml)
    that is human-readable and can be version-controlled.

    Usage:
        manager = DecisionManager()

        # Record a decision
        manager.set_decision(
            scope="scan.permissions",
            rule="skip_s3",
            value=True,
            reason="User chose to skip due to permission issues",
            decision_type=DecisionType.SUPPRESS
        )

        # Check a decision
        decision = manager.get_decision("scan.permissions", "skip_s3")
        if decision and not decision.is_expired():
            # Decision is valid, use it
            pass

        # List expiring decisions
        expiring = manager.get_expiring_soon(days=7)
        for d in expiring:
            print(f"Decision {d.scope}.{d.rule} expires in {d.days_until_expiry()} days")
    """

    DEFAULT_PATH = Path.home() / ".replimap" / "decisions.yaml"

    def __init__(self, path: Path | None = None):
        """
        Initialize DecisionManager.

        Args:
            path: Path to decisions file (defaults to ~/.replimap/decisions.yaml)
        """
        self.path = path or self.DEFAULT_PATH
        self._manifest: DecisionManifest = DecisionManifest()
        self._load()

    def _load(self) -> None:
        """Load decisions from file."""
        if not self.path.exists():
            return

        try:
            with open(self.path) as f:
                data = yaml.safe_load(f) or {}

            self._manifest = DecisionManifest.from_dict(data)
        except (yaml.YAMLError, KeyError, TypeError):
            # Invalid file, start fresh
            self._manifest = DecisionManifest()

    def _save(self) -> None:
        """
        Save decisions to file.

        Uses atomic write pattern with file locking for safety.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._manifest.last_modified = datetime.now().isoformat()

        data = self._manifest.to_dict()

        # Atomic write: write to temp file, then rename
        fd, temp_path = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".decisions_",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "w") as f:
                # Acquire exclusive lock
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    yaml.dump(
                        data,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            os.chmod(temp_path, 0o600)
            os.rename(temp_path, self.path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def get_decision(
        self,
        scope: str,
        rule: str,
        check_expiry: bool = True,
    ) -> Decision | None:
        """
        Get a decision by scope and rule.

        Args:
            scope: Decision scope (e.g., "scan.permissions")
            rule: Decision rule (e.g., "skip_s3")
            check_expiry: If True, return None for expired decisions

        Returns:
            Decision if found and valid, None otherwise
        """
        for d in self._manifest.decisions:
            if d.scope == scope and d.rule == rule:
                if check_expiry and d.is_expired():
                    return None
                return d
        return None

    def has_decision(self, scope: str, rule: str) -> bool:
        """Check if a valid (non-expired) decision exists."""
        return self.get_decision(scope, rule) is not None

    def set_decision(
        self,
        scope: str,
        rule: str,
        value: Any,
        reason: str,
        decision_type: DecisionType,
        permanent: bool = False,
        custom_ttl_days: int | None = None,
        created_by: str = "user",
    ) -> Decision:
        """
        Record a decision.

        Args:
            scope: Decision scope (e.g., "scan.permissions")
            rule: Decision rule (e.g., "skip_s3")
            value: The decision value
            reason: Why this decision was made
            decision_type: Type of decision
            permanent: If True, no expiration
            custom_ttl_days: Override default TTL
            created_by: Who made the decision ("user" or "auto")

        Returns:
            The created Decision object
        """
        # Remove existing decision with same scope/rule
        self._manifest.decisions = [
            d
            for d in self._manifest.decisions
            if not (d.scope == scope and d.rule == rule)
        ]

        # Calculate expiration
        expires_at = None
        ttl_days = None

        if not permanent:
            ttl_days = custom_ttl_days or DEFAULT_TTL_DAYS.get(decision_type)
            if ttl_days:
                expires_at = (datetime.now() + timedelta(days=ttl_days)).isoformat()

        decision = Decision(
            scope=scope,
            rule=rule,
            value=value,
            reason=reason,
            decision_type=decision_type.value,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            expires_at=expires_at,
            ttl_days=ttl_days,
        )

        self._manifest.decisions.append(decision)
        self._save()

        return decision

    def renew_decision(self, scope: str, rule: str) -> bool:
        """
        Renew a decision's TTL.

        Extends the expiration by the original TTL period.

        Args:
            scope: Decision scope
            rule: Decision rule

        Returns:
            True if renewed, False if decision not found or permanent
        """
        decision = self.get_decision(scope, rule, check_expiry=False)
        if not decision or not decision.ttl_days:
            return False

        decision.expires_at = (
            datetime.now() + timedelta(days=decision.ttl_days)
        ).isoformat()
        self._save()
        return True

    def delete_decision(self, scope: str, rule: str) -> bool:
        """
        Delete a specific decision.

        Args:
            scope: Decision scope
            rule: Decision rule

        Returns:
            True if deleted, False if not found
        """
        original_count = len(self._manifest.decisions)
        self._manifest.decisions = [
            d
            for d in self._manifest.decisions
            if not (d.scope == scope and d.rule == rule)
        ]
        deleted = len(self._manifest.decisions) < original_count
        if deleted:
            self._save()
        return deleted

    def get_expired(self) -> list[Decision]:
        """Get all expired decisions."""
        return [d for d in self._manifest.decisions if d.is_expired()]

    def get_expiring_soon(self, days: int = 7) -> list[Decision]:
        """
        Get decisions expiring soon.

        Args:
            days: Threshold in days

        Returns:
            List of decisions expiring within threshold
        """
        return [d for d in self._manifest.decisions if d.is_expiring_soon(days)]

    def get_by_scope(self, scope: str) -> list[Decision]:
        """
        Get all decisions for a scope.

        Args:
            scope: Decision scope

        Returns:
            List of decisions in scope (may include expired)
        """
        return [d for d in self._manifest.decisions if d.scope == scope]

    def get_by_type(self, decision_type: DecisionType) -> list[Decision]:
        """
        Get all decisions of a type.

        Args:
            decision_type: Type to filter by

        Returns:
            List of decisions of that type
        """
        return [
            d
            for d in self._manifest.decisions
            if d.decision_type == decision_type.value
        ]

    def remove_expired(self) -> int:
        """
        Remove all expired decisions.

        Returns:
            Number of decisions removed
        """
        original = len(self._manifest.decisions)
        self._manifest.decisions = [
            d for d in self._manifest.decisions if not d.is_expired()
        ]
        removed = original - len(self._manifest.decisions)
        if removed > 0:
            self._save()
        return removed

    def clear(self, scope: str | None = None) -> int:
        """
        Clear decisions, optionally by scope.

        Args:
            scope: If provided, only clear decisions in this scope

        Returns:
            Number of decisions cleared
        """
        original = len(self._manifest.decisions)
        if scope:
            self._manifest.decisions = [
                d for d in self._manifest.decisions if d.scope != scope
            ]
        else:
            self._manifest.decisions = []
        removed = original - len(self._manifest.decisions)
        if removed > 0:
            self._save()
        return removed

    def list_all(self) -> list[Decision]:
        """List all decisions (including expired)."""
        return list(self._manifest.decisions)

    def list_valid(self) -> list[Decision]:
        """List all non-expired decisions."""
        return [d for d in self._manifest.decisions if not d.is_expired()]

    def count(self) -> dict[str, int]:
        """
        Get decision counts by status.

        Returns:
            Dict with counts for total, valid, expired, expiring_soon
        """
        all_decisions = self._manifest.decisions
        return {
            "total": len(all_decisions),
            "valid": len([d for d in all_decisions if not d.is_expired()]),
            "expired": len([d for d in all_decisions if d.is_expired()]),
            "expiring_soon": len([d for d in all_decisions if d.is_expiring_soon()]),
            "permanent": len([d for d in all_decisions if d.is_permanent()]),
        }

    def export_shareable(self) -> dict[str, Any]:
        """
        Export decisions for team sharing.

        Excludes machine-specific data and expired decisions.

        Returns:
            Dict suitable for sharing/importing
        """
        return {
            "version": self._manifest.version,
            "exported_at": datetime.now().isoformat(),
            "decisions": [
                {
                    "scope": d.scope,
                    "rule": d.rule,
                    "value": d.value,
                    "reason": d.reason,
                    "decision_type": d.decision_type,
                }
                for d in self._manifest.decisions
                if d.created_by == "user" and not d.is_expired()
            ],
        }

    def import_shared(
        self,
        data: dict[str, Any],
        overwrite: bool = False,
    ) -> int:
        """
        Import shared decisions.

        Args:
            data: Exported decision data
            overwrite: If True, overwrite existing decisions

        Returns:
            Number of decisions imported
        """
        imported = 0
        for item in data.get("decisions", []):
            scope = item["scope"]
            rule = item["rule"]

            # Check if exists
            existing = self.get_decision(scope, rule, check_expiry=False)
            if existing and not overwrite:
                continue

            # Import with appropriate TTL
            decision_type = DecisionType(item["decision_type"])
            self.set_decision(
                scope=scope,
                rule=rule,
                value=item["value"],
                reason=item["reason"],
                decision_type=decision_type,
                created_by="imported",
            )
            imported += 1

        return imported


def create_decision_manager(path: Path | None = None) -> DecisionManager:
    """
    Factory function to create a DecisionManager.

    Args:
        path: Optional custom path for decisions file

    Returns:
        Configured DecisionManager instance
    """
    return DecisionManager(path)


__all__ = [
    "DecisionManager",
    "create_decision_manager",
]
