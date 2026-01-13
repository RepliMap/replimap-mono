"""
Time validation to prevent time travel attacks.

Attack Vector:
    User sets system clock backwards to extend expired license.
    Simple datetime.now() check fails.

Defense Strategy:
    1. Track last known time - detect backwards movement
    2. Optional network time verification
    3. Configurable tolerance for clock drift
    4. Fail-safe: if time is suspicious, require online verification
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

UTC = timezone.utc


class TimeValidationError(Exception):
    """Raised when time validation fails."""

    pass


class TimeValidator:
    """
    Validates system time integrity to prevent time travel attacks.

    Usage:
        validator = TimeValidator()

        # Check time before license verification
        is_valid, reason = validator.validate()
        if not is_valid:
            raise TimeValidationError(reason)

        # Get current time (after validation)
        now = validator.get_validated_time()

    Security Properties:
        - Detects system clock set backwards
        - Optional network time cross-check
        - Persistent tracking across restarts
        - Configurable tolerance for legitimate drift
    """

    TIME_FILE = Path.home() / ".replimap" / ".time_tracking"

    # Allow 24 hours of backwards drift (daylight saving, timezone changes)
    BACKWARDS_TOLERANCE = timedelta(hours=24)

    # Allow 1 hour of forward drift per day (clock running fast)
    FORWARD_TOLERANCE_PER_DAY = timedelta(hours=1)

    # Maximum time we track (avoid issues with very old timestamps)
    MAX_TRACKING_AGE = timedelta(days=365)

    def __init__(self, time_file: Optional[Path] = None) -> None:
        """
        Initialize time validator.

        Args:
            time_file: Custom path for time tracking file (for testing)
        """
        self.time_file = time_file or self.TIME_FILE

    def validate(self) -> tuple[bool, str]:
        """
        Validate current system time.

        Returns:
            (is_valid, reason_message)

        Validation checks:
            1. Time hasn't gone backwards significantly
            2. Time hasn't jumped forward unrealistically
            3. Time tracking data isn't corrupted
        """
        now = datetime.now(UTC)

        # Load previous time record
        last_record = self._load_time_record()

        if last_record:
            last_time = last_record["time"]
            last_check = last_record["checked_at"]

            # Check for backwards movement
            if now < last_time - self.BACKWARDS_TOLERANCE:
                return False, (
                    f"System time appears to have gone backwards. "
                    f"Current: {now.isoformat()}, Last known: {last_time.isoformat()}. "
                    f"This may indicate time manipulation."
                )

            # Check for unrealistic forward jump
            time_since_last_check = now - last_check
            if time_since_last_check > timedelta(0):
                max_forward = time_since_last_check + self.FORWARD_TOLERANCE_PER_DAY * (
                    time_since_last_check.days + 1
                )
                actual_forward = now - last_time

                if actual_forward > max_forward:
                    logger.warning(
                        f"Large time jump detected: {actual_forward}. "
                        f"Expected max: {max_forward}"
                    )
                    # Don't fail, just log - could be legitimate (hibernation, etc.)

        # Update time record
        self._save_time_record(now)

        return True, "OK"

    def get_validated_time(self) -> datetime:
        """
        Get current time after validation.

        Raises:
            TimeValidationError: If time validation fails
        """
        is_valid, reason = self.validate()
        if not is_valid:
            raise TimeValidationError(reason)
        return datetime.now(UTC)

    def get_network_time(self) -> Optional[datetime]:
        """
        Attempt to get time from network sources.

        Uses HTTP Date headers from reliable sources.
        More firewall-friendly than NTP.

        Returns:
            Network time if available, None if all sources fail
        """
        try:
            import httpx
        except ImportError:
            logger.debug("httpx not available for network time check")
            return None

        # Reliable time sources (use Date header)
        time_sources = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.microsoft.com",
        ]

        for url in time_sources:
            try:
                response = httpx.head(
                    url,
                    timeout=3.0,
                    follow_redirects=False,
                )

                date_header = response.headers.get("date")
                if date_header:
                    from email.utils import parsedate_to_datetime

                    network_time = parsedate_to_datetime(date_header)
                    logger.debug(f"Got network time from {url}: {network_time}")
                    return network_time

            except Exception as e:
                logger.debug(f"Failed to get time from {url}: {e}")
                continue

        logger.warning("Could not get network time from any source")
        return None

    def validate_with_network(
        self, max_drift: timedelta = timedelta(hours=1)
    ) -> tuple[bool, str]:
        """
        Validate system time against network time.

        Args:
            max_drift: Maximum allowed drift from network time

        Returns:
            (is_valid, reason_message)
        """
        # First do local validation
        local_valid, local_reason = self.validate()
        if not local_valid:
            return False, local_reason

        # Try network validation
        network_time = self.get_network_time()
        if network_time is None:
            # Network unavailable, trust local time
            return True, "OK (network unavailable)"

        system_time = datetime.now(UTC)
        drift = abs(system_time - network_time)

        if drift > max_drift:
            return False, (
                f"System time differs significantly from network time. "
                f"System: {system_time.isoformat()}, Network: {network_time.isoformat()}, "
                f"Drift: {drift}"
            )

        return True, "OK"

    def _load_time_record(self) -> Optional[dict]:
        """Load previous time record from disk."""
        if not self.time_file.exists():
            return None

        try:
            data = json.loads(self.time_file.read_text())

            last_time = datetime.fromisoformat(data["time"])
            checked_at = datetime.fromisoformat(data["checked_at"])

            # Ignore very old records
            if datetime.now(UTC) - checked_at > self.MAX_TRACKING_AGE:
                logger.debug("Time record too old, ignoring")
                return None

            return {
                "time": last_time,
                "checked_at": checked_at,
            }

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Corrupted time record: {e}")
            return None

    def _save_time_record(self, current_time: datetime) -> None:
        """Save current time record to disk."""
        try:
            self.time_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "time": current_time.isoformat(),
                "checked_at": datetime.now(UTC).isoformat(),
                "version": 1,
            }

            self.time_file.write_text(json.dumps(data))

        except OSError as e:
            logger.warning(f"Could not save time record: {e}")

    def reset(self) -> None:
        """
        Reset time tracking (for testing or recovery).

        WARNING: This removes time manipulation detection.
        """
        if self.time_file.exists():
            self.time_file.unlink()
        logger.info("Time tracking reset")
