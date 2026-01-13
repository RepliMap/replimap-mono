"""
OutputManager - Unified output layer with stdout/stderr separation.

Key Design Principles:
1. JSON mode: stdout receives ONLY the final JSON, all other output to stderr
2. Text mode: stdout uses Rich formatting
3. Commands MUST use ctx.obj.output methods, never print() directly

Usage:
    output = ctx.obj.output
    output.progress("Scanning...")    # → stderr
    output.log("Found 5 VPCs")        # → stderr
    output.present(result)            # → stdout (formatted)

This enforces CI/CD pipeline compatibility by ensuring JSON output is parseable.
"""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterator

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

if TYPE_CHECKING:
    from collections.abc import Sequence


class OutputFormat(str, Enum):
    """Output format options."""

    TEXT = "text"
    JSON = "json"
    TABLE = "table"
    QUIET = "quiet"


@dataclass
class OutputManager:
    """
    Unified output manager for CLI commands.

    Ensures stdout hygiene by separating presentational output (stdout)
    from operational output (stderr).

    Attributes:
        format: The output format (text, json, table, quiet)
        verbose: Verbosity level (0=normal, 1=verbose, 2=debug)
        _stdout_written: Tracks if stdout has been written in JSON mode
        _stderr_console: Rich console for stderr output
        _stdout_console: Rich console for stdout output
    """

    format: OutputFormat = OutputFormat.TEXT
    verbose: int = 0
    _stdout_written: bool = field(default=False, init=False, repr=False)
    _stderr_console: Console = field(
        default_factory=lambda: Console(stderr=True, force_terminal=True),
        init=False,
        repr=False,
    )
    _stdout_console: Console = field(
        default_factory=lambda: Console(force_terminal=True),
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        """Convert string format to enum if needed."""
        if isinstance(self.format, str):
            self.format = OutputFormat(self.format)

    # ========================================================================
    # PRESENTATION METHODS (stdout)
    # ========================================================================

    def present(
        self,
        data: Any,
        title: str | None = None,
        columns: Sequence[str] | None = None,
    ) -> None:
        """
        Present final output to stdout.

        In JSON mode, this writes raw JSON and can only be called ONCE.
        In TEXT mode, this renders a Rich Panel or Table.
        In QUIET mode, this is a no-op.

        Args:
            data: The data to present (dict, list, or any JSON-serializable)
            title: Optional title for Panel/Table rendering
            columns: Optional column headers for table rendering

        Raises:
            RuntimeError: If called twice in JSON mode
        """
        if self.format == OutputFormat.QUIET:
            return

        if self.format == OutputFormat.JSON:
            if self._stdout_written:
                raise RuntimeError(
                    "stdout already written in JSON mode. "
                    "JSON mode allows only ONE write to stdout."
                )
            # Write pure JSON to stdout - no Rich formatting
            json_str = json.dumps(data, indent=2, default=str)
            sys.stdout.write(json_str)
            sys.stdout.write("\n")
            sys.stdout.flush()
            self._stdout_written = True
            return

        if self.format == OutputFormat.TABLE:
            self._present_as_table(data, title, columns)
            return

        # TEXT format - use Rich Panel
        self._present_as_text(data, title)

    def _present_as_text(self, data: Any, title: str | None = None) -> None:
        """Present data as formatted Rich text to stdout."""
        if isinstance(data, dict):
            # Format dict as key-value pairs
            content_lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    content_lines.append(f"[bold]{key}:[/]")
                    for k, v in value.items():
                        content_lines.append(f"  {k}: {v}")
                elif isinstance(value, list):
                    content_lines.append(f"[bold]{key}:[/] {len(value)} items")
                else:
                    content_lines.append(f"[bold]{key}:[/] {value}")
            content = "\n".join(content_lines)
        elif isinstance(data, list):
            content = "\n".join(str(item) for item in data)
        else:
            content = str(data)

        if title:
            self._stdout_console.print(
                Panel(content, title=f"[bold]{title}[/]", border_style="cyan")
            )
        else:
            self._stdout_console.print(content)

    def _present_as_table(
        self,
        data: Any,
        title: str | None = None,
        columns: Sequence[str] | None = None,
    ) -> None:
        """Present data as a Rich table to stdout."""
        table = Table(title=title, show_header=True, header_style="bold cyan")

        if isinstance(data, list) and data:
            # Infer columns from first item if not provided
            first_item = data[0]
            if isinstance(first_item, dict):
                cols = list(columns) if columns else list(first_item.keys())
                for col in cols:
                    table.add_column(col)
                for item in data:
                    if isinstance(item, dict):
                        table.add_row(*[str(item.get(c, "")) for c in cols])
            else:
                table.add_column("Value")
                for item in data:
                    table.add_row(str(item))
        elif isinstance(data, dict):
            table.add_column("Key")
            table.add_column("Value")
            for key, value in data.items():
                table.add_row(str(key), str(value))

        self._stdout_console.print(table)

    # ========================================================================
    # LOGGING METHODS (stderr)
    # ========================================================================

    def log(self, message: str, level: int = 0) -> None:
        """
        Log a message to stderr.

        Args:
            message: The message to log
            level: Required verbosity level (0=always, 1=verbose, 2=debug)
        """
        if self.format == OutputFormat.QUIET and level < 2:
            return
        if level <= self.verbose:
            self._stderr_console.print(message)

    def debug(self, message: str) -> None:
        """Log debug message (requires -vv)."""
        if self.verbose >= 2:
            self._stderr_console.print(f"[dim][DEBUG][/] {message}")

    def info(self, message: str) -> None:
        """Log info message (requires -v)."""
        if self.verbose >= 1:
            self._stderr_console.print(f"[dim][INFO][/] {message}")

    def warn(self, message: str) -> None:
        """Log warning message (always shown)."""
        self._stderr_console.print(f"[yellow][WARN][/] {message}")

    def error(self, message: str) -> None:
        """Log error message (always shown)."""
        self._stderr_console.print(f"[red][ERROR][/] {message}")

    def success(self, message: str) -> None:
        """Log success message (always shown unless quiet)."""
        if self.format != OutputFormat.QUIET:
            self._stderr_console.print(f"[green]✓[/] {message}")

    def progress(self, message: str) -> None:
        """Log progress message to stderr."""
        if self.format != OutputFormat.QUIET:
            self._stderr_console.print(f"[dim]{message}[/]")

    # ========================================================================
    # INTERACTIVE METHODS (stderr prompt, stdin input)
    # ========================================================================

    @contextmanager
    def spinner(self, message: str) -> Iterator[None]:
        """
        Show a spinner while performing an operation.

        Usage:
            with output.spinner("Loading..."):
                do_something()
        """
        if self.format == OutputFormat.QUIET:
            yield
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            console=self._stderr_console,
            transient=True,
        ) as progress:
            progress.add_task(message, total=None)
            yield

    def prompt(self, message: str, default: str | None = None) -> str:
        """
        Prompt user for input.

        Args:
            message: The prompt message
            default: Default value if user presses Enter

        Returns:
            User's input or default value
        """
        return Prompt.ask(message, default=default, console=self._stderr_console)

    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask user for confirmation.

        Args:
            message: The confirmation message
            default: Default value if user presses Enter

        Returns:
            True if user confirms, False otherwise
        """
        return Confirm.ask(message, default=default, console=self._stderr_console)

    def select(
        self,
        message: str,
        choices: Sequence[str],
        default: str | None = None,
    ) -> str:
        """
        Prompt user to select from choices.

        Args:
            message: The prompt message
            choices: Available choices
            default: Default selection

        Returns:
            Selected choice
        """
        return Prompt.ask(
            message,
            choices=list(choices),
            default=default,
            console=self._stderr_console,
        )

    # ========================================================================
    # RICH DISPLAY HELPERS (stderr)
    # ========================================================================

    def panel(
        self,
        content: str,
        title: str | None = None,
        border_style: str = "cyan",
    ) -> None:
        """Display a panel to stderr."""
        if self.format != OutputFormat.QUIET:
            self._stderr_console.print(
                Panel(content, title=title, border_style=border_style)
            )

    def table(
        self,
        data: list[dict[str, Any]],
        title: str | None = None,
        columns: Sequence[str] | None = None,
    ) -> None:
        """Display a table to stderr."""
        if self.format == OutputFormat.QUIET:
            return

        table = Table(title=title, show_header=True, header_style="bold cyan")

        if data:
            cols = list(columns) if columns else list(data[0].keys())
            for col in cols:
                table.add_column(col)
            for row in data:
                table.add_row(*[str(row.get(c, "")) for c in cols])

        self._stderr_console.print(table)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    @property
    def is_json(self) -> bool:
        """Check if output format is JSON."""
        return self.format == OutputFormat.JSON

    @property
    def is_quiet(self) -> bool:
        """Check if output format is QUIET."""
        return self.format == OutputFormat.QUIET

    @property
    def is_interactive(self) -> bool:
        """Check if running in interactive mode (TTY)."""
        return sys.stdin.isatty() and self.format != OutputFormat.JSON

    def reset(self) -> None:
        """Reset the output state (mainly for testing)."""
        self._stdout_written = False


def create_output_manager(
    format: str = "text",
    verbose: int = 0,
) -> OutputManager:
    """
    Factory function to create an OutputManager.

    Args:
        format: Output format string (text, json, table, quiet)
        verbose: Verbosity level (0, 1, or 2)

    Returns:
        Configured OutputManager instance
    """
    return OutputManager(
        format=OutputFormat(format),
        verbose=verbose,
    )


__all__ = [
    "OutputFormat",
    "OutputManager",
    "create_output_manager",
]
