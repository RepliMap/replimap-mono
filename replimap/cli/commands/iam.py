"""
IAM policy generation CLI commands.

Generates least-privilege IAM policies by analyzing the dependency graph
with intelligent boundary control.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from replimap.core.cache_manager import get_or_load_graph
from replimap.core.security.iam_generator import (
    GraphAwareIAMGenerator,
    PolicyScope,
)

console = Console()


def create_iam_app() -> typer.Typer:
    """Create the iam sub-command group."""
    iam_app = typer.Typer(
        name="iam",
        help="Generate least-privilege IAM policies from graph analysis",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @iam_app.command("for-resource")
    def generate_for_resource(
        profile: str = typer.Option(
            "default",
            "--profile",
            "-p",
            help="AWS profile name",
        ),
        resource_id: str = typer.Option(
            ...,
            "--resource",
            "-r",
            help="Resource ID (Lambda function name, EC2 instance ID, etc.)",
        ),
        scope: str = typer.Option(
            "runtime_read",
            "--scope",
            "-s",
            help="Scope: runtime_read, runtime_write, runtime_full, infra_deploy",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file path",
        ),
        output_format: str = typer.Option(
            "json",
            "--format",
            "-f",
            help="Output format: json, terraform",
        ),
        max_depth: int = typer.Option(
            3,
            "--depth",
            help="Maximum traversal depth",
        ),
        include_networking: bool = typer.Option(
            False,
            "--include-networking",
            help="Include networking resources (VPC, Subnet, etc.)",
        ),
        create_role: bool = typer.Option(
            False,
            "--create-role",
            help="Generate IAM role in Terraform output",
        ),
        role_name: str | None = typer.Option(
            None,
            "--role-name",
            help="Role name for Terraform output",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            help="AWS region (auto-detected from cache if not specified)",
        ),
        account_id: str | None = typer.Option(
            None,
            "--account-id",
            help="AWS account ID (auto-detected from resources if not specified)",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            "-R",
            help="Force fresh AWS scan (ignore cached graph)",
        ),
        enrich: bool = typer.Option(
            False,
            "--enrich",
            "-E",
            help="Run graph enrichment to discover implicit dependencies",
        ),
        no_baseline: bool = typer.Option(
            False,
            "--no-baseline",
            help="Don't generate baseline policy when no dependencies found",
        ),
    ) -> None:
        """Generate IAM policy for a specific compute resource.

        \b

        Uses graph analysis to find connected resources and generates
        permissions ONLY for those specific resources with precise ARNs.

        \b

        This prevents over-permissioning by using boundary-aware traversal:

        - TERMINAL resources (other Lambda/EC2) block traversal

        - DATA resources (S3, SQS, DynamoDB) grant permissions but don't continue

        - SECURITY resources (KMS, Secrets) always include encryption deps

        - TRANSITIVE resources (VPC, Subnet) pass through without permissions

        \b

        Examples:

            # Read-only policy for Lambda
            replimap iam for-resource -p prod -r my-lambda -s runtime_read

            # Full access policy
            replimap iam for-resource -p prod -r my-lambda -s runtime_full

            # Generate Terraform with role
            replimap iam for-resource -r func -f terraform --create-role

            # Save to file
            replimap iam for-resource -p prod -r my-lambda -o policy.json

            # With graph enrichment (discovers implicit dependencies)
            replimap iam for-resource -p prod -r i-abc123 -E

            # Without baseline fallback (fail if no deps found)
            replimap iam for-resource -p prod -r i-abc123 --no-baseline
        """
        # Parse scope
        scope_map = {
            "runtime_read": PolicyScope.RUNTIME_READ,
            "runtime_write": PolicyScope.RUNTIME_WRITE,
            "runtime_full": PolicyScope.RUNTIME_FULL,
            "infra_read": PolicyScope.INFRA_READ,
            "infra_deploy": PolicyScope.INFRA_DEPLOY,
        }

        policy_scope = scope_map.get(scope.lower())
        if not policy_scope:
            valid_scopes = ", ".join(scope_map.keys())
            console.print(f"[red]Invalid scope: {scope}[/red]")
            console.print(f"[dim]Valid scopes: {valid_scopes}[/dim]")
            raise typer.Exit(1)

        # Determine region from cache or flag
        effective_region = region or "us-east-1"
        if not region:
            from replimap.cli.utils import get_profile_region

            profile_region = get_profile_region(profile)
            if profile_region:
                effective_region = profile_region

        # Load graph from cache
        console.print()
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile,
            region=effective_region,
            console=console,
            refresh=refresh,
        )

        if not cached_graph:
            console.print(
                "[red]No cached scan found.[/red] [dim]Run 'replimap scan' first.[/dim]"
            )
            raise typer.Exit(1)

        # Auto-detect account ID if not provided
        effective_account = account_id or _detect_account_id(cached_graph)

        console.print(
            f"[dim]Analyzing dependencies for: [cyan]{resource_id}[/cyan][/dim]"
        )

        # Find resource - try by ID first, then by name
        resource = cached_graph.get_resource(resource_id)
        if not resource:
            resource = _find_by_name(cached_graph, resource_id)
            if resource:
                resource_id = resource.id
                console.print(f"[dim]Found as: {resource.id}[/dim]")
            else:
                console.print(f"[red]Resource not found: {resource_id}[/red]")
                console.print()
                _suggest_resources(cached_graph, resource_id)
                raise typer.Exit(1)

        # Generate policy
        try:
            generator = GraphAwareIAMGenerator(
                cached_graph,
                effective_account,
                effective_region,
                strict_mode=True,
            )

            policies = generator.generate_for_principal(
                resource_id,
                policy_scope,
                max_depth,
                include_networking,
                use_baseline_fallback=not no_baseline,
                enrich_graph=enrich,
            )
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

        # Output
        console.print()
        if output_format.lower() == "terraform":
            role = role_name or f"{resource.original_name or resource_id}-role"
            tf = generator.generate_terraform_output(
                policies, role, create_role, str(resource.resource_type)
            )
            if output:
                output.write_text(tf)
                console.print(f"[green]Saved to {output}[/green]")
            else:
                console.print(
                    Panel(
                        Syntax(tf, "hcl", theme="monokai", word_wrap=True),
                        title="Terraform Output",
                        border_style="cyan",
                    )
                )
        else:
            for policy in policies:
                json_str = policy.to_json()
                if output:
                    output.write_text(json_str)
                    console.print(f"[green]Saved to {output}[/green]")
                else:
                    console.print(
                        Panel(
                            Syntax(json_str, "json", theme="monokai", word_wrap=True),
                            title=policy.name,
                            border_style="cyan",
                        )
                    )

        # Summary
        _print_summary(policies)

    @iam_app.command("list-compute")
    def list_compute(
        profile: str = typer.Option(
            "default",
            "--profile",
            "-p",
            help="AWS profile name",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            help="AWS region",
        ),
    ) -> None:
        """List compute resources that can have IAM policies generated.

        \b

        Shows Lambda functions, EC2 instances, ECS tasks, etc. that can be used
        with 'replimap iam for-resource'.

        \b

        Examples:

            replimap iam list-compute -p prod
        """
        # Determine region
        effective_region = region or "us-east-1"
        if not region:
            from replimap.cli.utils import get_profile_region

            profile_region = get_profile_region(profile)
            if profile_region:
                effective_region = profile_region

        # Load graph
        console.print()
        cached_graph, _ = get_or_load_graph(
            profile=profile,
            region=effective_region,
            console=console,
        )

        if not cached_graph:
            console.print(
                "[red]No cached scan found.[/red] [dim]Run 'replimap scan' first.[/dim]"
            )
            raise typer.Exit(1)

        # Find compute resources
        compute_types = {
            "aws_lambda_function",
            "aws_instance",
            "aws_ecs_service",
            "aws_ecs_task_definition",
            "aws_eks_node_group",
        }

        table = Table(
            title="Compute Resources",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("ID")
        table.add_column("Dependencies", justify="right")

        count = 0
        for resource in cached_graph.get_all_resources():
            rtype = str(resource.resource_type)
            if rtype in compute_types:
                dep_count = len(resource.dependencies)
                table.add_row(
                    rtype.replace("aws_", ""),
                    resource.original_name or "-",
                    resource.id,
                    str(dep_count),
                )
                count += 1

        if count == 0:
            console.print("[dim]No compute resources found in cached scan.[/dim]")
        else:
            console.print(table)
            console.print()
            console.print(
                f"[dim]Found {count} compute resources. "
                f"Use 'replimap iam for-resource -r <id>' to generate policy.[/dim]"
            )

    return iam_app


def _detect_account_id(graph) -> str:
    """Auto-detect AWS account ID from resources in graph."""
    for node in graph.get_all_resources():
        arn = node.arn or node.config.get("arn", "")
        if arn:
            parts = arn.split(":")
            if len(parts) > 4 and parts[4] and parts[4].isdigit():
                return parts[4]
    return "123456789012"


def _detect_region(graph) -> str:
    """Auto-detect AWS region from resources in graph."""
    for node in graph.get_all_resources():
        if node.region and node.region != "unknown":
            return node.region
        arn = node.arn or node.config.get("arn", "")
        if arn:
            parts = arn.split(":")
            if len(parts) > 3 and parts[3]:
                return parts[3]
    return "us-east-1"


def _find_by_name(graph, name: str):
    """Find a resource by name attribute."""
    for node in graph.get_all_resources():
        if node.original_name == name:
            return node
        # Check common name attributes
        for key in ("function_name", "FunctionName", "name", "Name", "id"):
            if node.config.get(key) == name:
                return node
    return None


def _suggest_resources(graph, query: str) -> None:
    """Suggest similar resources when not found."""
    compute_types = {
        "aws_lambda_function",
        "aws_instance",
        "aws_ecs_service",
        "aws_ecs_task_definition",
    }

    suggestions = []
    query_lower = query.lower()
    for node in graph.get_all_resources():
        rtype = str(node.resource_type)
        if rtype in compute_types:
            name = (node.original_name or "").lower()
            node_id = node.id.lower()
            if query_lower in name or query_lower in node_id:
                suggestions.append((rtype, node.original_name, node.id))

    if suggestions:
        console.print("[dim]Did you mean one of these?[/dim]")
        for rtype, name, rid in suggestions[:5]:
            console.print(f"  - {name or rid} [dim]({rtype})[/dim]")
    else:
        # Show available compute resources
        console.print("[dim]Available compute resources:[/dim]")
        count = 0
        for node in graph.get_all_resources():
            rtype = str(node.resource_type)
            if rtype in compute_types and count < 10:
                console.print(
                    f"  - {node.original_name or node.id} [dim]({rtype})[/dim]"
                )
                count += 1
        if count == 10:
            console.print(
                "  [dim]... (use 'replimap iam list-compute' for full list)[/dim]"
            )


def _print_summary(policies) -> None:
    """Print policy summary."""
    console.print()
    console.print("[bold]Summary[/bold]")
    for p in policies:
        console.print(f"  [cyan]{p.name}[/cyan]:")
        console.print(f"    Statements: {len(p.statements)}")
        console.print(f"    Actions: {p.action_count()}")
        console.print(f"    Resources: {p.resource_count()}")
        console.print(f"    Size: {p.estimated_size()} bytes")
        lp_status = "[green]Yes[/green]" if p.is_least_privilege() else "[red]No[/red]"
        console.print(f"    Least Privilege: {lp_status}")
    console.print()


def register(app: typer.Typer) -> None:
    """Register iam commands with the app."""
    app.add_typer(create_iam_app(), name="iam")
