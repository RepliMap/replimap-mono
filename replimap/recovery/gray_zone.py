"""
Gray Zone Resolver - Handles ambiguous cases requiring user decision.

When the system encounters a situation where it cannot automatically
determine the correct action, it uses the GrayZoneResolver to:
1. Ask the user for a decision (interactive mode)
2. Use a default/conservative choice (CI mode)
3. Record the decision for future reference
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

from replimap.cli.utils.console import console
from replimap.core.context import ExecutionEnvironment, GlobalContext
from replimap.decisions.manager import DecisionManager
from replimap.decisions.models import DecisionType

if TYPE_CHECKING:
    from rich.console import Console


class GrayZoneCategory(Enum):
    """Categories of gray zone decisions."""

    EXTRACTION = "extraction"  # What to extract as variables
    PERMISSION = "permission"  # How to handle permission errors
    FORMAT = "format"  # Output format choices
    SCOPE = "scope"  # Scan scope decisions
    CONFLICT = "conflict"  # Resource conflicts


@dataclass
class GrayZoneQuestion:
    """
    A question for the user about an ambiguous situation.

    Attributes:
        category: Category of the question
        scope: Decision scope for storage
        rule: Decision rule for storage
        question: The question text
        options: List of (value, label) tuples
        default: Default option value
        context: Additional context for the question
        reason: Why this decision is needed
    """

    category: GrayZoneCategory
    scope: str
    rule: str
    question: str
    options: list[tuple[Any, str]]
    default: Any
    context: dict[str, Any]
    reason: str


@dataclass
class GrayZoneAnswer:
    """
    The user's answer to a gray zone question.

    Attributes:
        value: The chosen value
        remember: Whether to remember this decision
        permanent: Whether the decision should be permanent
        source: Where the answer came from (user, cached, default)
    """

    value: Any
    remember: bool
    permanent: bool
    source: str  # "user", "cached", "default"


class GrayZoneResolver:
    """
    Resolves ambiguous situations requiring user input.

    Behavior:
    - Interactive: Ask user, optionally remember decision
    - CI: Use default, log the choice
    - Non-Interactive: Use default, log warning

    Usage:
        resolver = GrayZoneResolver(ctx, decision_manager)

        question = GrayZoneQuestion(
            category=GrayZoneCategory.EXTRACTION,
            scope="extraction.fields",
            rule="cidr_block_aws_vpc",
            question="Should VPC CIDR blocks be extracted as variables?",
            options=[(True, "Yes - extract as variable"), (False, "No - keep hardcoded")],
            default=True,
            context={"resource_type": "aws_vpc", "field": "cidr_block"},
            reason="VPC CIDR blocks typically vary between environments"
        )

        answer = resolver.resolve(question)
    """

    def __init__(
        self,
        ctx: GlobalContext,
        decision_manager: DecisionManager,
        output_console: Console | None = None,
    ):
        """
        Initialize GrayZoneResolver.

        Args:
            ctx: Global context
            decision_manager: Decision manager for caching decisions
            output_console: Optional console for output
        """
        self.ctx = ctx
        self.decisions = decision_manager
        self.console = output_console or console

    def resolve(self, question: GrayZoneQuestion) -> GrayZoneAnswer:
        """
        Resolve a gray zone question.

        Args:
            question: The question to resolve

        Returns:
            GrayZoneAnswer with the decision
        """
        # Check for cached decision first
        cached = self.decisions.get_decision(question.scope, question.rule)
        if cached:
            return GrayZoneAnswer(
                value=cached.value,
                remember=True,
                permanent=cached.is_permanent(),
                source="cached",
            )

        # In CI or non-interactive mode, use default
        if not self.ctx.is_interactive():
            self._log_default_used(question)
            return GrayZoneAnswer(
                value=question.default,
                remember=False,
                permanent=False,
                source="default",
            )

        # Interactive mode - ask the user
        return self._ask_user(question)

    def _ask_user(self, question: GrayZoneQuestion) -> GrayZoneAnswer:
        """Ask the user for a decision."""
        self.console.print()
        self.console.print(f"[yellow bold]❓ Decision Required[/yellow bold]")
        self.console.print(f"   {question.question}")
        self.console.print()

        # Show context
        if question.context:
            self.console.print("[dim]Context:[/dim]")
            for key, value in question.context.items():
                self.console.print(f"   {key}: {value}")
            self.console.print()

        # Show reason
        self.console.print(f"[dim]Why: {question.reason}[/dim]")
        self.console.print()

        # Show options
        for i, (value, label) in enumerate(question.options, 1):
            default_marker = " [default]" if value == question.default else ""
            self.console.print(f"   [{i}] {label}{default_marker}")

        self.console.print()

        # Get choice
        try:
            choice_str = self.console.input(
                f"   Choose [1-{len(question.options)}] or Enter for default: "
            ).strip()

            if not choice_str:
                choice_idx = None
            else:
                choice_idx = int(choice_str) - 1

            if choice_idx is None or not (0 <= choice_idx < len(question.options)):
                value = question.default
            else:
                value = question.options[choice_idx][0]

        except (ValueError, EOFError, KeyboardInterrupt):
            self.console.print("\n   [dim]Using default[/dim]")
            value = question.default

        # Ask about remembering
        remember = False
        permanent = False

        try:
            remember_str = self.console.input(
                "   Remember this decision? [y/N/p(ermanent)]: "
            ).strip().lower()

            if remember_str == "y":
                remember = True
            elif remember_str == "p":
                remember = True
                permanent = True

        except (EOFError, KeyboardInterrupt):
            pass

        # Record decision if requested
        if remember:
            decision_type = self._map_category_to_type(question.category)
            self.decisions.set_decision(
                scope=question.scope,
                rule=question.rule,
                value=value,
                reason=question.reason,
                decision_type=decision_type,
                permanent=permanent,
            )
            self.console.print("   [green]Decision saved.[/green]")

        return GrayZoneAnswer(
            value=value,
            remember=remember,
            permanent=permanent,
            source="user",
        )

    def _log_default_used(self, question: GrayZoneQuestion) -> None:
        """Log that a default was used in non-interactive mode."""
        if self.ctx.is_ci():
            # In CI, we might want to log this more visibly
            pass  # Could log to a summary file
        else:
            self.console.print(
                f"[dim]Using default for {question.scope}.{question.rule}[/dim]"
            )

    def _map_category_to_type(self, category: GrayZoneCategory) -> DecisionType:
        """Map category to decision type."""
        mapping = {
            GrayZoneCategory.EXTRACTION: DecisionType.EXTRACTION,
            GrayZoneCategory.PERMISSION: DecisionType.SUPPRESS,
            GrayZoneCategory.FORMAT: DecisionType.PREFERENCE,
            GrayZoneCategory.SCOPE: DecisionType.SUPPRESS,
            GrayZoneCategory.CONFLICT: DecisionType.SUPPRESS,
        }
        return mapping.get(category, DecisionType.SUPPRESS)


# Pre-built questions for common gray zones
def create_extraction_question(
    resource_type: str,
    field_name: str,
    current_value: Any,
) -> GrayZoneQuestion:
    """Create a question about field extraction."""
    return GrayZoneQuestion(
        category=GrayZoneCategory.EXTRACTION,
        scope="extraction.fields",
        rule=f"{field_name}_{resource_type.replace('aws_', '')}",
        question=f"Should '{field_name}' be extracted as a variable?",
        options=[
            (True, f"Yes - extract as var.{field_name}"),
            (False, f"No - keep hardcoded as {current_value}"),
        ],
        default=True,
        context={
            "resource_type": resource_type,
            "field": field_name,
            "current_value": str(current_value)[:50],
        },
        reason=f"Field '{field_name}' may vary between environments",
    )


def create_permission_question(
    service: str,
    action: str,
    error_message: str,
) -> GrayZoneQuestion:
    """Create a question about permission handling."""
    return GrayZoneQuestion(
        category=GrayZoneCategory.PERMISSION,
        scope="scan.permissions",
        rule=f"skip_{service}",
        question=f"Skip {service} due to permission error?",
        options=[
            (True, f"Yes - skip {service} and continue"),
            (False, "No - abort scan"),
        ],
        default=True,
        context={
            "service": service,
            "action": action,
            "error": error_message[:100],
        },
        reason=f"Missing permission for {service}:{action}",
    )


__all__ = [
    "GrayZoneAnswer",
    "GrayZoneCategory",
    "GrayZoneQuestion",
    "GrayZoneResolver",
    "create_extraction_question",
    "create_permission_question",
]
