"""
Decision Models - Data structures for decision tracking.

Defines the core data models used by the DecisionManager for
tracking user decisions with TTL support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class DecisionType(Enum):
    """
    Decision type with default TTL.

    Each type has a semantic meaning and default expiration:
    - SUPPRESS: User chose to ignore/skip something (30 days)
    - EXTRACTION: User chose what to extract as variables (90 days)
    - PREFERENCE: User style preference (permanent)
    - PERMANENT: Explicitly marked permanent (never expires)
    """

    SUPPRESS = "suppress"  # Skip/ignore - expires in 30 days
    EXTRACTION = "extraction"  # Extract/keep - expires in 90 days
    PREFERENCE = "preference"  # Format/style - permanent
    PERMANENT = "permanent"  # Explicit permanent - never expires


# Default TTL in days by decision type
DEFAULT_TTL_DAYS: dict[DecisionType, int | None] = {
    DecisionType.SUPPRESS: 30,
    DecisionType.EXTRACTION: 90,
    DecisionType.PREFERENCE: None,  # Permanent
    DecisionType.PERMANENT: None,  # Permanent
}


@dataclass
class Decision:
    """
    A recorded user decision.

    Attributes:
        scope: Decision scope (e.g., "scan.permissions", "extraction.fields")
        rule: Specific rule identifier (e.g., "skip_s3", "extract_vpc_id")
        value: The decision value (typically True/False or a string)
        reason: Human-readable reason for the decision
        decision_type: Type of decision (affects TTL)
        created_at: ISO timestamp when decision was made
        created_by: Who made the decision ("user" or "auto")
        expires_at: ISO timestamp when decision expires (None = permanent)
        ttl_days: TTL in days (for renewals)
    """

    scope: str
    rule: str
    value: Any
    reason: str
    decision_type: str  # DecisionType.value
    created_at: str  # ISO timestamp
    created_by: str = "user"
    expires_at: str | None = None
    ttl_days: int | None = None

    def is_expired(self) -> bool:
        """Check if decision has expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            return expiry < datetime.now()
        except ValueError:
            return False

    def days_until_expiry(self) -> int | None:
        """
        Days until expiration.

        Returns:
            Number of days until expiry, or None if permanent
        """
        if not self.expires_at:
            return None
        try:
            expiry = datetime.fromisoformat(self.expires_at)
            delta = expiry - datetime.now()
            return max(0, delta.days)
        except ValueError:
            return None

    def is_expiring_soon(self, days: int = 7) -> bool:
        """
        Check if expiring within given days.

        Args:
            days: Threshold in days

        Returns:
            True if expiring within threshold, False otherwise
        """
        remaining = self.days_until_expiry()
        return remaining is not None and 0 < remaining <= days

    def is_permanent(self) -> bool:
        """Check if decision is permanent (never expires)."""
        return self.expires_at is None

    def get_type(self) -> DecisionType:
        """Get the DecisionType enum value."""
        try:
            return DecisionType(self.decision_type)
        except ValueError:
            return DecisionType.SUPPRESS

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scope": self.scope,
            "rule": self.rule,
            "value": self.value,
            "reason": self.reason,
            "decision_type": self.decision_type,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "expires_at": self.expires_at,
            "ttl_days": self.ttl_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decision:
        """Create Decision from dictionary."""
        return cls(
            scope=data["scope"],
            rule=data["rule"],
            value=data["value"],
            reason=data["reason"],
            decision_type=data["decision_type"],
            created_at=data["created_at"],
            created_by=data.get("created_by", "user"),
            expires_at=data.get("expires_at"),
            ttl_days=data.get("ttl_days"),
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        expiry_info = ""
        if self.expires_at:
            days = self.days_until_expiry()
            if days is not None:
                if days == 0:
                    expiry_info = " [EXPIRED]"
                elif days <= 7:
                    expiry_info = f" [expires in {days}d]"
        else:
            expiry_info = " [permanent]"

        return f"{self.scope}.{self.rule} = {self.value}{expiry_info}"


@dataclass
class DecisionManifest:
    """
    Collection of decisions with metadata.

    This is the root object stored in decisions.yaml.
    """

    version: str = "1.0"
    decisions: list[Decision] = field(default_factory=list)
    last_modified: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "last_modified": self.last_modified,
            "decisions": [d.to_dict() for d in self.decisions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionManifest:
        """Create DecisionManifest from dictionary."""
        return cls(
            version=data.get("version", "1.0"),
            last_modified=data.get("last_modified"),
            decisions=[Decision.from_dict(d) for d in data.get("decisions", [])],
        )


__all__ = [
    "DEFAULT_TTL_DAYS",
    "Decision",
    "DecisionManifest",
    "DecisionType",
]
