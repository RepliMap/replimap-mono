"""
Tests for the cross-platform browser launcher module.

Verifies browser opening behavior across different platforms
including WSL2 detection and fallback handling.

NOTE: WSL detection now uses cross-platform platform.release() instead
of os.uname() which is not available on all platforms.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from replimap.core.browser import (
    _open_native,
    _open_url,
    _print_manual_instructions,
    can_open_browser,
    is_container,
    is_remote_ssh,
    is_wsl,
    open_in_browser,
)


class TestWSLDetection:
    """Test WSL/WSL2 detection using cross-platform platform.release()."""

    def test_is_wsl_on_non_linux(self) -> None:
        """Returns False on non-Linux platforms."""
        with patch("replimap.core.browser.sys.platform", "darwin"):
            assert is_wsl() is False

        with patch("replimap.core.browser.sys.platform", "win32"):
            assert is_wsl() is False

    def test_is_wsl_on_linux_without_microsoft(self) -> None:
        """Returns False on native Linux."""
        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch(
                "replimap.core.browser.platform.release", return_value="5.15.0-generic"
            ),
            patch("pathlib.Path.exists", return_value=False),
        ):
            assert is_wsl() is False

    def test_is_wsl_on_wsl2(self) -> None:
        """Returns True when running in WSL2."""
        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch(
                "replimap.core.browser.platform.release",
                return_value="5.15.90.1-microsoft-standard-WSL2",
            ),
        ):
            assert is_wsl() is True

    def test_is_wsl_on_wsl1(self) -> None:
        """Returns True when running in WSL1."""
        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch(
                "replimap.core.browser.platform.release",
                return_value="4.4.0-19041-Microsoft",
            ),
        ):
            assert is_wsl() is True

    def test_is_wsl_via_proc_version_fallback(self) -> None:
        """Returns True via /proc/version fallback."""
        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch(
                "replimap.core.browser.platform.release", return_value="5.15.0-generic"
            ),
        ):
            # Create a mock Path that simulates /proc/version
            with patch("replimap.core.browser.Path") as MockPath:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path_instance.read_text.return_value = (
                    "Linux version 5.4.72-microsoft-standard-WSL2"
                )
                MockPath.return_value = mock_path_instance

                assert is_wsl() is True

    def test_is_wsl_handles_exception(self) -> None:
        """WSL check handles exceptions gracefully."""
        with (
            patch("replimap.core.browser.sys.platform", "linux"),
            patch(
                "replimap.core.browser.platform.release",
                side_effect=Exception("error"),
            ),
        ):
            assert is_wsl() is False


class TestRemoteSSHDetection:
    """Test SSH session detection."""

    def test_is_remote_ssh_with_ssh_client(self) -> None:
        """SSH detected when SSH_CLIENT is set."""
        with patch.dict("os.environ", {"SSH_CLIENT": "192.168.1.1 12345 22"}):
            assert is_remote_ssh() is True

    def test_is_remote_ssh_with_ssh_tty(self) -> None:
        """SSH detected when SSH_TTY is set."""
        with patch.dict("os.environ", {"SSH_TTY": "/dev/pts/0"}):
            assert is_remote_ssh() is True

    def test_is_remote_ssh_not_detected(self) -> None:
        """SSH not detected when no env vars set."""
        with patch.dict("os.environ", {}, clear=True):
            assert is_remote_ssh() is False


class TestContainerDetection:
    """Test container environment detection."""

    def test_is_container_not_detected(self) -> None:
        """Container not detected in normal environment."""
        with patch("pathlib.Path.exists", return_value=False):
            assert is_container() is False


class TestCanOpenBrowser:
    """Test browser opening capability check."""

    def test_can_open_browser_remote_ssh_no_display(self) -> None:
        """Cannot open browser in SSH without DISPLAY."""
        with (
            patch("replimap.core.browser.is_remote_ssh", return_value=True),
            patch.dict("os.environ", {}, clear=True),
        ):
            assert can_open_browser() is False

    def test_can_open_browser_remote_ssh_with_display(self) -> None:
        """Can open browser in SSH with X forwarding."""
        with (
            patch("replimap.core.browser.is_remote_ssh", return_value=True),
            patch("replimap.core.browser.is_container", return_value=False),
            patch.dict("os.environ", {"DISPLAY": ":0"}),
        ):
            assert can_open_browser() is True

    def test_can_open_browser_normal_environment(self) -> None:
        """Can open browser in normal environment."""
        with (
            patch("replimap.core.browser.is_remote_ssh", return_value=False),
            patch("replimap.core.browser.is_container", return_value=False),
        ):
            assert can_open_browser() is True


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility specifically."""

    def test_platform_release_used_instead_of_uname(self) -> None:
        """Verify platform.release() is used, not os.uname()."""
        with patch("replimap.core.browser.sys.platform", "linux"):
            with patch("replimap.core.browser.platform.release") as mock_release:
                mock_release.return_value = "5.4.0-generic"
                with patch("pathlib.Path.exists", return_value=False):
                    is_wsl()

                # platform.release should have been called
                mock_release.assert_called()

    def test_no_os_uname_call_in_source(self) -> None:
        """Ensure os.uname() is not called (would fail on Windows)."""
        import inspect

        import replimap.core.browser as browser_module

        source = inspect.getsource(browser_module.is_wsl)
        # Check for actual calls to os.uname, not mentions in docstrings
        # The docstring mentions it for documentation, but the code shouldn't call it
        assert "os.uname()" not in source


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
