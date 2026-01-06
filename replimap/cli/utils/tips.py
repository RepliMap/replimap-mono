"""
Pro Tips for RepliMap CLI.

Shows helpful tips to users occasionally to help them discover features.
"""

from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

# List of pro tips to show users
TIPS = [
    "Visualize your infrastructure: [bold]replimap graph[/bold]",
    "Generate Terraform code: [bold]replimap clone[/bold]",
    "Find security issues: [bold]replimap audit[/bold]",
    "Analyze blast radius: [bold]replimap deps <resource-id>[/bold]",
    "Use [bold]--quiet[/bold] for cleaner output in scripts",
    "Save graph to file: [bold]replimap scan -o graph.db[/bold]",
    "Enable shell completion: [bold]replimap --install-completion[/bold]",
    "Filter by VPC: [bold]replimap scan --vpc vpc-xxx[/bold]",
    "Filter by tag: [bold]replimap scan --tag Environment=prod[/bold]",
    "Show verbose logs: [bold]replimap --verbose scan[/bold]",
]


def show_random_tip(console: Console, probability: float = 0.3) -> None:
    """
    Show a random tip with given probability.

    Args:
        console: Rich console for output
        probability: Chance of showing a tip (0.0 to 1.0)
    """
    # Skip if tips are disabled
    if os.getenv("REPLIMAP_NO_TIPS", "").lower() in ("1", "true", "yes"):
        return

    # Skip if quiet mode
    if os.getenv("REPLIMAP_QUIET", "").lower() in ("1", "true", "yes"):
        return

    if random.random() < probability:  # noqa: S311 - not security-sensitive
        tip = random.choice(TIPS)  # noqa: S311 - not security-sensitive
        console.print(f"\n[dim]Tip: {tip}[/dim]")


def show_tip_for_command(console: Console, command: str) -> None:
    """
    Show a contextual tip based on the command just run.

    Args:
        console: Rich console for output
        command: The command that was just executed
    """
    # Skip if tips are disabled
    if os.getenv("REPLIMAP_NO_TIPS", "").lower() in ("1", "true", "yes"):
        return

    contextual_tips = {
        "scan": [
            "Next: [bold]replimap graph[/bold] to visualize dependencies",
            "Next: [bold]replimap audit[/bold] to check for security issues",
            "Next: [bold]replimap clone[/bold] to generate Terraform",
        ],
        "audit": [
            "Fix findings and re-run to verify",
            "Export report: [bold]replimap audit -o report.html[/bold]",
        ],
        "graph": [
            "Try [bold]--security-view[/bold] to highlight security groups",
            "Use [bold]--show-all[/bold] for complete resource details",
        ],
        "clone": [
            "Review generated Terraform before applying",
            "Use [bold]--downsize[/bold] to reduce instance sizes for staging",
        ],
    }

    tips = contextual_tips.get(command, [])
    if tips and random.random() < 0.3:  # noqa: S311 - not security-sensitive
        tip = random.choice(tips)  # noqa: S311 - not security-sensitive
        console.print(f"\n[dim]Tip: {tip}[/dim]")


__all__ = [
    "TIPS",
    "show_random_tip",
    "show_tip_for_command",
]
