"""
Progressive Error Renderer - Shows errors with increasing detail levels.

Progressive Disclosure Levels:
1. One-line summary (always shown)
2. Fix command (default)
3. Detailed explanation (--verbose)
4. Debug info (--debug)

This provides a better user experience by showing just enough
information at each level without overwhelming the user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from rich.console import Console


@dataclass
class ErrorInfo:
    """
    Structured error information for progressive rendering.

    This contains all the information needed to render an error
    at any detail level.
    """

    # Level 1: Summary (always shown)
    code: str  # e.g., "RM-E001"
    summary: str  # One-line description

    # Level 2: Fix
    fix_command: str
    fix_description: str = ""

    # Level 3: Explanation
    root_cause: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    related_docs: list[str] = field(default_factory=list)

    # Level 4: Debug
    stack_trace: str = ""
    aws_request_id: str | None = None
    raw_error: str = ""


class ProgressiveErrorRenderer:
    """
    Renders errors with progressive disclosure.

    Usage:
        renderer = ProgressiveErrorRenderer(console)
        error_info = ErrorInfo(
            code="RM-E001",
            summary="Missing AWS credentials",
            fix_command="aws configure",
            ...
        )
        renderer.render(error_info, level=2)  # Default
        renderer.render(error_info, level=3)  # With --verbose
        renderer.render(error_info, level=4)  # With --debug
    """

    def __init__(self, console: Console):
        """
        Initialize ProgressiveErrorRenderer.

        Args:
            console: Rich console for output
        """
        self.console = console

    def render(
        self,
        error: ErrorInfo,
        level: int = 2,
        show_expand_hint: bool = True,
    ) -> None:
        """
        Render error at specified detail level.

        Args:
            error: Error information
            level: Detail level (1-4)
            show_expand_hint: Show hint about getting more details
        """
        content = Text()

        # Level 1: Summary (always shown)
        content.append(f"❌ [{error.code}] ", style="bold red")
        content.append(f"{error.summary}\n", style="red")

        # Level 2: Fix command
        if level >= 2 and error.fix_command:
            content.append("\n")
            content.append("🔧 Fix: ", style="bold green")
            content.append(f"{error.fix_command}\n", style="cyan")
            if error.fix_description:
                content.append(f"   {error.fix_description}\n", style="dim")

        # Level 3: Explanation
        if level >= 3 and error.root_cause:
            content.append("\n")
            content.append("📖 Why: ", style="bold yellow")
            content.append(f"{error.root_cause}\n", style="yellow")

            if error.context:
                content.append("\n   Context:\n", style="dim")
                for key, value in error.context.items():
                    content.append(f"   • {key}: {value}\n", style="dim")

            if error.related_docs:
                content.append("\n   📚 Docs:\n", style="dim")
                for doc in error.related_docs:
                    content.append(f"   • {doc}\n", style="dim blue underline")

        # Level 4: Debug
        if level >= 4:
            content.append("\n")
            content.append("🔍 Debug:\n", style="bold magenta")
            if error.aws_request_id:
                content.append(f"   Request ID: {error.aws_request_id}\n", style="dim")
            if error.raw_error:
                # Truncate if too long
                raw = error.raw_error[:500]
                if len(error.raw_error) > 500:
                    raw += "..."
                content.append(f"   Raw: {raw}\n", style="dim")
            if error.stack_trace:
                content.append(f"\n   Stack trace:\n{error.stack_trace}\n", style="dim")

        # Render panel
        self.console.print(
            Panel(
                content,
                border_style="red",
                expand=False,
            )
        )

        # Expansion hint
        if show_expand_hint and level < 4:
            hints = {
                1: "💡 Run with default options for fix command",
                2: "💡 Run with --verbose for detailed explanation",
                3: "💡 Run with --debug for full debug info",
            }
            hint = hints.get(level, "")
            if hint:
                self.console.print(hint, style="dim")

    def render_simple(self, error: ErrorInfo) -> None:
        """
        Render minimal error for CI environments.

        Just shows the essential information without formatting.
        """
        self.console.print(f"❌ [{error.code}] {error.summary}")
        if error.fix_command:
            self.console.print(f"   Fix: {error.fix_command}")
        self.console.print(f"   [?] Run 'replimap explain {error.code}' for details")

    def render_inline(self, error: ErrorInfo) -> str:
        """
        Render error as a single line for logging.

        Returns:
            Single-line error string
        """
        return f"[{error.code}] {error.summary}"


def create_error_info_from_exception(
    exception: Exception,
    code: str,
    context: dict[str, Any] | None = None,
) -> ErrorInfo:
    """
    Create ErrorInfo from an exception.

    Args:
        exception: The exception that occurred
        code: Error code to assign
        context: Additional context

    Returns:
        ErrorInfo populated from exception
    """
    import traceback

    # Import catalog to get error details
    from replimap.cli.error_catalog import ERROR_CATALOG

    # Look up error in catalog
    catalog_entry = ERROR_CATALOG.get(code)

    if catalog_entry:
        return ErrorInfo(
            code=code,
            summary=catalog_entry.get("summary", str(exception)),
            fix_command=catalog_entry.get("fix_command", ""),
            fix_description=catalog_entry.get("fix_description", ""),
            root_cause=catalog_entry.get("root_cause", ""),
            context=context or {},
            related_docs=catalog_entry.get("docs", []),
            raw_error=str(exception),
            stack_trace=traceback.format_exc(),
        )

    # Fallback for unknown errors
    return ErrorInfo(
        code=code,
        summary=str(exception),
        fix_command="replimap doctor",
        fix_description="Run diagnostics to identify the issue",
        root_cause="An unexpected error occurred",
        context=context or {},
        raw_error=str(exception),
        stack_trace=traceback.format_exc(),
    )


__all__ = [
    "ErrorInfo",
    "ProgressiveErrorRenderer",
    "create_error_info_from_exception",
]
