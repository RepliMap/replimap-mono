"""
Tests for the first-run experience module.

Verifies the first-run privacy message and marker file behavior.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from replimap.core.first_run import (
    FIRST_RUN_MARKER,
    REPLIMAP_DIR,
    check_and_show_first_run_message,
    reset_first_run_marker,
    show_privacy_info,
)


class TestFirstRunMarker:
    """Test first-run marker file management."""

    def test_replimap_dir_location(self) -> None:
        """REPLIMAP_DIR points to ~/.replimap."""
        assert REPLIMAP_DIR == Path.home() / ".replimap"

    def test_first_run_marker_location(self) -> None:
        """Marker file is in the right location."""
        assert FIRST_RUN_MARKER == REPLIMAP_DIR / ".first_run_complete"

    def test_reset_first_run_marker_when_exists(self, tmp_path: Path) -> None:
        """Reset removes marker file when it exists."""
        # Create a temporary marker
        marker = tmp_path / ".first_run_complete"
        marker.touch()

        with patch("replimap.core.first_run.FIRST_RUN_MARKER", marker):
            result = reset_first_run_marker()

        assert result is True
        assert not marker.exists()

    def test_reset_first_run_marker_when_not_exists(self, tmp_path: Path) -> None:
        """Reset returns False when marker doesn't exist."""
        marker = tmp_path / ".first_run_complete"

        with patch("replimap.core.first_run.FIRST_RUN_MARKER", marker):
            result = reset_first_run_marker()

        assert result is False


class TestCheckAndShowFirstRunMessage:
    """Test the first-run message display logic."""

    def test_shows_message_on_first_run(self, tmp_path: Path) -> None:
        """Message is shown when marker doesn't exist."""
        replimap_dir = tmp_path / ".replimap"
        marker = replimap_dir / ".first_run_complete"

        console = MagicMock()

        with (
            patch("replimap.core.first_run.REPLIMAP_DIR", replimap_dir),
            patch("replimap.core.first_run.FIRST_RUN_MARKER", marker),
        ):
            check_and_show_first_run_message(console)

        # Should have printed the welcome panel
        assert console.print.call_count >= 2  # Empty line + panel
        # Marker should now exist
        assert marker.exists()

    def test_skips_message_on_subsequent_run(self, tmp_path: Path) -> None:
        """Message is not shown when marker exists."""
        replimap_dir = tmp_path / ".replimap"
        replimap_dir.mkdir(parents=True)
        marker = replimap_dir / ".first_run_complete"
        marker.touch()

        console = MagicMock()

        with (
            patch("replimap.core.first_run.REPLIMAP_DIR", replimap_dir),
            patch("replimap.core.first_run.FIRST_RUN_MARKER", marker),
        ):
            check_and_show_first_run_message(console)

        # Should not have printed anything
        console.print.assert_not_called()

    def test_creates_replimap_dir_if_missing(self, tmp_path: Path) -> None:
        """Creates ~/.replimap directory if it doesn't exist."""
        replimap_dir = tmp_path / ".replimap"
        marker = replimap_dir / ".first_run_complete"

        console = MagicMock()

        with (
            patch("replimap.core.first_run.REPLIMAP_DIR", replimap_dir),
            patch("replimap.core.first_run.FIRST_RUN_MARKER", marker),
        ):
            check_and_show_first_run_message(console)

        assert replimap_dir.exists()


class TestShowPrivacyInfo:
    """Test the privacy info display."""

    def test_shows_privacy_panel(self) -> None:
        """Privacy info is displayed as a panel."""
        console = MagicMock()

        show_privacy_info(console)

        # Should have called console.print with a Panel
        console.print.assert_called_once()
        call_args = console.print.call_args
        # The first positional argument should be a Panel
        from rich.panel import Panel

        assert isinstance(call_args[0][0], Panel)

    def test_privacy_panel_has_correct_title(self) -> None:
        """Privacy panel has the correct title."""
        console = MagicMock()

        show_privacy_info(console)

        call_args = console.print.call_args
        panel = call_args[0][0]
        assert panel.title == "RepliMap Privacy"

    def test_privacy_panel_mentions_local(self) -> None:
        """Privacy info mentions local operation."""
        console = MagicMock()

        show_privacy_info(console)

        call_args = console.print.call_args
        panel = call_args[0][0]
        # The panel's renderable should contain "100% Local"
        content = str(panel.renderable)
        assert "100% Local" in content
