"""
Tests for the cross-platform browser launcher module.

Verifies browser opening behavior across different platforms
including WSL2 detection and fallback handling.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from replimap.core.browser import (
    _open_native,
    _open_url,
    _print_manual_instructions,
    is_wsl,
    open_in_browser,
)


class TestWSLDetection:
    """Test WSL/WSL2 detection."""

    def test_is_wsl_on_non_linux(self) -> None:
        """Returns False on non-Linux platforms."""
        with patch("replimap.core.browser.sys.platform", "darwin"):
            assert is_wsl() is False

        with patch("replimap.core.browser.sys.platform", "win32"):
            assert is_wsl() is False

    def test_is_wsl_on_linux_without_microsoft(self) -> None:
        """Returns False on native Linux."""
        mock_uname = MagicMock()
        mock_uname.release = "5.15.0-generic"

        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch("replimap.core.browser.os.uname", return_value=mock_uname),
        ):
            assert is_wsl() is False

    def test_is_wsl_on_wsl2(self) -> None:
        """Returns True when running in WSL2."""
        mock_uname = MagicMock()
        mock_uname.release = "5.15.90.1-microsoft-standard-WSL2"

        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch("replimap.core.browser.os.uname", return_value=mock_uname),
        ):
            assert is_wsl() is True

    def test_is_wsl_on_wsl1(self) -> None:
        """Returns True when running in WSL1."""
        mock_uname = MagicMock()
        mock_uname.release = "4.4.0-19041-Microsoft"

        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch("replimap.core.browser.os.uname", return_value=mock_uname),
        ):
            assert is_wsl() is True


class TestOpenInBrowser:
    """Test the main open_in_browser function."""

    def test_handles_nonexistent_file(self, tmp_path: Path) -> None:
        """Returns False for nonexistent files."""
        console = MagicMock()
        nonexistent = tmp_path / "nonexistent.html"

        result = open_in_browser(nonexistent, console=console)

        assert result is False
        console.print.assert_called()

    def test_handles_url(self) -> None:
        """Handles HTTP URLs directly."""
        with patch("replimap.core.browser._open_url") as mock_open_url:
            mock_open_url.return_value = True
            result = open_in_browser("https://example.com", console=None)
            mock_open_url.assert_called_once()
            assert result is True

    def test_routes_to_wsl_handler(self, tmp_path: Path) -> None:
        """Routes to WSL handler when in WSL."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        with (
            patch("replimap.core.browser.is_wsl", return_value=True),
            patch("replimap.core.browser._open_wsl") as mock_wsl,
        ):
            mock_wsl.return_value = True
            result = open_in_browser(test_file, console=None)

            mock_wsl.assert_called_once()
            assert result is True

    def test_routes_to_native_handler(self, tmp_path: Path) -> None:
        """Routes to native handler when not in WSL."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        with (
            patch("replimap.core.browser.is_wsl", return_value=False),
            patch("replimap.core.browser._open_native") as mock_native,
        ):
            mock_native.return_value = True
            result = open_in_browser(test_file, console=None)

            mock_native.assert_called_once()
            assert result is True

    def test_shows_opening_message(self, tmp_path: Path) -> None:
        """Shows 'Opening in browser...' message when not quiet."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")
        console = MagicMock()

        with (
            patch("replimap.core.browser.is_wsl", return_value=False),
            patch("replimap.core.browser._open_native", return_value=True),
        ):
            open_in_browser(test_file, console=console, quiet=False)

        # Should have printed the "Opening in browser..." message
        assert any(
            "Opening in browser" in str(call) for call in console.print.call_args_list
        )

    def test_quiet_mode_suppresses_message(self, tmp_path: Path) -> None:
        """Quiet mode suppresses the opening message."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")
        console = MagicMock()

        with (
            patch("replimap.core.browser.is_wsl", return_value=False),
            patch("replimap.core.browser._open_native", return_value=True),
        ):
            open_in_browser(test_file, console=console, quiet=True)

        # Should not have printed the "Opening in browser..." message
        console.print.assert_not_called()


class TestOpenURL:
    """Test URL opening functionality."""

    def test_opens_url_native(self) -> None:
        """Opens URL using webbrowser on non-WSL."""
        with (
            patch("replimap.core.browser.is_wsl", return_value=False),
            patch("webbrowser.open") as mock_open,
        ):
            result = _open_url("https://example.com", console=None)
            mock_open.assert_called_once_with("https://example.com")
            assert result is True

    def test_opens_url_wsl(self) -> None:
        """Opens URL using cmd.exe in WSL."""
        with (
            patch("replimap.core.browser.is_wsl", return_value=True),
            patch("replimap.core.browser.subprocess.run") as mock_run,
        ):
            result = _open_url("https://example.com", console=None)
            mock_run.assert_called_once()
            assert result is True


class TestOpenNative:
    """Test native browser opening."""

    def test_opens_file_url(self, tmp_path: Path) -> None:
        """Opens file using webbrowser module."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")

        with patch("webbrowser.open") as mock_open:
            result = _open_native(test_file, console=None)

            mock_open.assert_called_once()
            assert f"file://{test_file}" in mock_open.call_args[0][0]
            assert result is True

    def test_handles_webbrowser_error(self, tmp_path: Path) -> None:
        """Handles webbrowser errors gracefully."""
        test_file = tmp_path / "test.html"
        test_file.write_text("<html></html>")
        console = MagicMock()

        with patch("webbrowser.open", side_effect=Exception("Failed")):
            result = _open_native(test_file, console=console)

            assert result is False


class TestManualInstructions:
    """Test manual instruction printing."""

    def test_prints_instructions(self, tmp_path: Path) -> None:
        """Prints manual opening instructions."""
        test_file = tmp_path / "test.html"
        console = MagicMock()

        _print_manual_instructions(test_file, console=console)

        # Should have printed multiple lines
        assert console.print.call_count >= 3

    def test_shows_windows_path_in_wsl(self, tmp_path: Path) -> None:
        """Shows Windows path when in WSL."""
        test_file = tmp_path / "test.html"
        console = MagicMock()

        with (
            patch("replimap.core.browser.is_wsl", return_value=True),
            patch("replimap.core.browser.subprocess.run") as mock_run,
        ):
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "\\\\wsl$\\Ubuntu\\home\\user\\test.html"
            mock_run.return_value = mock_result

            _print_manual_instructions(test_file, console=console)

            # Should show Windows path
            assert any("Windows" in str(call) for call in console.print.call_args_list)

    def test_no_output_without_console(self, tmp_path: Path) -> None:
        """Does nothing when console is None."""
        test_file = tmp_path / "test.html"
        # Should not raise
        _print_manual_instructions(test_file, console=None)
