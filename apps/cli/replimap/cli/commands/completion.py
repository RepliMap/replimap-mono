"""
Shell completion command for RepliMap CLI.

Generate completion scripts for Bash, Zsh, and Fish shells.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Note: print() is used intentionally for shell completion scripts (T201 ignored)

Usage:
    # Generate and install
    eval "$(replimap completion bash)"
    eval "$(replimap completion zsh)"
    replimap completion fish > ~/.config/fish/completions/replimap.fish

    # Show installation instructions
    replimap completion install bash
"""

from __future__ import annotations

import typer

from replimap.cli.completion import (
    generate_bash_completion,
    generate_fish_completion,
    generate_zsh_completion,
    get_install_instructions,
)
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import console


def register(app: typer.Typer) -> None:
    """Register the completion command with the app."""

    completion_app = typer.Typer(
        name="completion",
        help="Generate shell completion scripts",
        no_args_is_help=True,
    )

    @completion_app.command("bash")
    @enhanced_cli_error_handler
    def bash_completion() -> None:
        """Generate Bash completion script.

        Usage:
            eval "$(replimap completion bash)"
        """
        print(generate_bash_completion())  # noqa: T201

    @completion_app.command("zsh")
    @enhanced_cli_error_handler
    def zsh_completion() -> None:
        """Generate Zsh completion script.

        Usage:
            eval "$(replimap completion zsh)"
        """
        print(generate_zsh_completion())  # noqa: T201

    @completion_app.command("fish")
    @enhanced_cli_error_handler
    def fish_completion() -> None:
        """Generate Fish completion script.

        Usage:
            replimap completion fish > ~/.config/fish/completions/replimap.fish
        """
        print(generate_fish_completion())  # noqa: T201

    @completion_app.command("install")
    @enhanced_cli_error_handler
    def install_instructions(
        shell: str = typer.Argument(
            ...,
            help="Shell type: bash, zsh, or fish",
        ),
    ) -> None:
        """Show installation instructions for shell completion.

        \b

        Examples:

            replimap completion install bash

            replimap completion install zsh

            replimap completion install fish
        """
        if shell not in ("bash", "zsh", "fish"):
            console.print(
                f"[red]Error:[/] Unknown shell '{shell}'. Use one of: bash, zsh, fish"
            )
            raise typer.Exit(1)

        instructions = get_install_instructions(shell)
        console.print(instructions)

    app.add_typer(completion_app, name="completion")
