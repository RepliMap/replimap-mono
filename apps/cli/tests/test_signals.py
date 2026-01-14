"""Tests for global signal handling."""

from __future__ import annotations

import signal
from unittest.mock import MagicMock, patch

from replimap.core.concurrency import reset_shutdown_state
from replimap.core.signals import (
    _handle_sigint,
    _handle_sigterm,
    setup_signal_handlers,
)


class TestSetupSignalHandlers:
    """Tests for setup_signal_handlers()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_installs_sigint_handler(self) -> None:
        """Should install SIGINT handler."""
        mock_console = MagicMock()

        with patch("signal.signal") as mock_signal:
            setup_signal_handlers(mock_console)

            # Check SIGINT handler was installed
            sigint_calls = [
                call
                for call in mock_signal.call_args_list
                if call[0][0] == signal.SIGINT
            ]
            assert len(sigint_calls) == 1
            assert sigint_calls[0][0][1] == _handle_sigint

    def test_installs_sigterm_handler(self) -> None:
        """Should install SIGTERM handler."""
        mock_console = MagicMock()

        with patch("signal.signal") as mock_signal:
            setup_signal_handlers(mock_console)

            # Check SIGTERM handler was installed
            sigterm_calls = [
                call
                for call in mock_signal.call_args_list
                if call[0][0] == signal.SIGTERM
            ]
            assert len(sigterm_calls) == 1
            assert sigterm_calls[0][0][1] == _handle_sigterm

    def test_saves_original_sigint_handler(self) -> None:
        """Should save original SIGINT handler."""
        mock_console = MagicMock()
        original_handler = signal.getsignal(signal.SIGINT)

        with patch("signal.signal"):
            with patch(
                "signal.getsignal", return_value=original_handler
            ) as mock_getsignal:
                setup_signal_handlers(mock_console)
                mock_getsignal.assert_called_with(signal.SIGINT)


class TestHandleSigint:
    """Tests for _handle_sigint()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_shows_cancelled_message(self) -> None:
        """Should show 'Cancelled by user' message."""
        mock_console = MagicMock()

        # Setup the global console
        with patch("replimap.core.signals._console", mock_console):
            with patch("os._exit"):
                _handle_sigint(signal.SIGINT, None)

                mock_console.show_cursor.assert_called_once()
                mock_console.print.assert_called_once()
                call_args = mock_console.print.call_args[0][0]
                assert "Cancelled" in call_args

    def test_calls_shutdown_all_executors(self) -> None:
        """Should call shutdown_all_executors."""
        mock_console = MagicMock()

        with patch("replimap.core.signals._console", mock_console):
            with patch("replimap.core.signals.shutdown_all_executors") as mock_shutdown:
                with patch("os._exit"):
                    _handle_sigint(signal.SIGINT, None)

                    mock_shutdown.assert_called_once_with(wait=False)

    def test_exits_with_code_130(self) -> None:
        """Should exit with code 130 (128 + SIGINT)."""
        mock_console = MagicMock()

        with patch("replimap.core.signals._console", mock_console):
            with patch("os._exit") as mock_exit:
                _handle_sigint(signal.SIGINT, None)

                mock_exit.assert_called_once_with(130)

    def test_handles_no_console(self) -> None:
        """Should not crash when console is None."""
        with patch("replimap.core.signals._console", None):
            with patch("os._exit") as mock_exit:
                # Should not raise
                _handle_sigint(signal.SIGINT, None)

                mock_exit.assert_called_once_with(130)


class TestHandleSigterm:
    """Tests for _handle_sigterm()."""

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_shutdown_state()

    def test_shows_terminated_message(self) -> None:
        """Should show 'Terminated' message."""
        mock_console = MagicMock()

        with patch("replimap.core.signals._console", mock_console):
            with patch("os._exit"):
                _handle_sigterm(signal.SIGTERM, None)

                mock_console.show_cursor.assert_called_once()
                mock_console.print.assert_called_once()
                call_args = mock_console.print.call_args[0][0]
                assert "Terminated" in call_args

    def test_calls_shutdown_all_executors(self) -> None:
        """Should call shutdown_all_executors."""
        mock_console = MagicMock()

        with patch("replimap.core.signals._console", mock_console):
            with patch("replimap.core.signals.shutdown_all_executors") as mock_shutdown:
                with patch("os._exit"):
                    _handle_sigterm(signal.SIGTERM, None)

                    mock_shutdown.assert_called_once_with(wait=False)

    def test_exits_with_code_143(self) -> None:
        """Should exit with code 143 (128 + SIGTERM)."""
        mock_console = MagicMock()

        with patch("replimap.core.signals._console", mock_console):
            with patch("os._exit") as mock_exit:
                _handle_sigterm(signal.SIGTERM, None)

                mock_exit.assert_called_once_with(143)

    def test_handles_no_console(self) -> None:
        """Should not crash when console is None."""
        with patch("replimap.core.signals._console", None):
            with patch("os._exit") as mock_exit:
                # Should not raise
                _handle_sigterm(signal.SIGTERM, None)

                mock_exit.assert_called_once_with(143)
