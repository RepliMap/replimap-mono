"""
Clone command - Generate Infrastructure-as-Code from AWS resources.
"""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from replimap import __version__
from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_aws_session,
    get_profile_region,
)
from replimap.core import GraphEngine
from replimap.licensing.manager import get_license_manager
from replimap.renderers import TerraformRenderer
from replimap.scanners.base import run_all_scanners
from replimap.transformers import create_default_pipeline


def register(app: typer.Typer) -> None:
    """Register the clone command with the app."""

    @app.command()
    def clone(
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS source profile name",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to scan (uses profile's region or us-east-1)",
        ),
        output_dir: Path = typer.Option(
            Path("./terraform"),
            "--output-dir",
            "-o",
            help="Output directory for generated files",
        ),
        output_format: str = typer.Option(
            "terraform",
            "--format",
            "-f",
            help="Output format: 'terraform' (Free+), 'cloudformation' (Solo+), "
            "'pulumi' (Pro+)",
        ),
        mode: str = typer.Option(
            "dry-run",
            "--mode",
            "-m",
            help="Mode: 'dry-run' (preview) or 'generate' (create files)",
        ),
        downsize: bool = typer.Option(
            True,
            "--downsize/--no-downsize",
            help="Enable instance downsizing for cost savings",
        ),
        rename_pattern: str | None = typer.Option(
            None,
            "--rename-pattern",
            help="Renaming pattern, e.g., 'prod:stage'",
        ),
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Interactive mode - prompt for missing options",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials (re-authenticate)",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            "-R",
            help="Force fresh AWS scan (ignore cached graph)",
        ),
        dev_mode: bool = typer.Option(
            False,
            "--dev-mode",
            "--dev",
            help="[SOLO+] Optimize resources for dev/staging "
            "(generates right-sizer.auto.tfvars)",
        ),
        dev_strategy: str = typer.Option(
            "conservative",
            "--dev-strategy",
            help="Right-Sizer strategy: 'conservative' (default) or 'aggressive'",
        ),
        # Backend options
        backend: str = typer.Option(
            "local",
            "--backend",
            "-b",
            help="Terraform backend type: 'local' (default) or 's3'",
        ),
        backend_bucket: str | None = typer.Option(
            None,
            "--backend-bucket",
            help="S3 bucket for state (required if --backend=s3)",
        ),
        backend_key: str = typer.Option(
            "replimap/terraform.tfstate",
            "--backend-key",
            help="S3 key for state file",
        ),
        backend_region: str | None = typer.Option(
            None,
            "--backend-region",
            help="S3 bucket region (defaults to scan region)",
        ),
        backend_dynamodb: str | None = typer.Option(
            None,
            "--backend-dynamodb",
            help="DynamoDB table for state locking",
        ),
        backend_bootstrap: bool = typer.Option(
            False,
            "--backend-bootstrap",
            help="Generate bootstrap Terraform to create S3 backend infrastructure",
        ),
    ) -> None:
        """Clone AWS environment to Infrastructure-as-Code.

        \b

        The region is determined in this order:

        1. --region flag (if provided)

        2. Profile's configured region (from ~/.aws/config)

        3. AWS_DEFAULT_REGION environment variable

        4. us-east-1 (fallback)

        \b

        Output formats:

        - terraform: Terraform HCL (Free tier and above)

        - cloudformation: AWS CloudFormation YAML (Solo plan and above)

        - pulumi: Pulumi Python (Pro plan and above)

        \b

        Backend types (Terraform only):

        - local: State stored locally (default)

        - s3: State stored in S3 for team collaboration

        \b

        Examples:

            replimap clone --profile prod --mode dry-run

            replimap clone --profile prod --format terraform --mode generate

            replimap clone -i  # Interactive mode

            replimap clone --profile prod --format cloudformation -o ./cfn

        \b

        S3 Backend Examples:

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state --backend-dynamodb locks

            replimap clone -p prod -o ./tf --backend s3 --backend-bucket my-state --backend-bootstrap
        """
        from replimap.licensing.gates import FeatureNotAvailableError
        from replimap.renderers import CloudFormationRenderer, PulumiRenderer

        # Interactive mode - prompt for missing options
        if interactive:
            if not profile:
                available = get_available_profiles()
                console.print("\n[bold]Available AWS Profiles:[/]")
                for i, p in enumerate(available, 1):
                    console.print(f"  {i}. {p}")
                console.print()
                profile = Prompt.ask(
                    "Select profile",
                    default="default",
                    choices=available,
                )

        # Determine region: flag > profile config > env var > default
        effective_region = region
        region_source = "flag"

        if not effective_region:
            profile_region = get_profile_region(profile)
            if profile_region:
                effective_region = profile_region
                region_source = f"profile '{profile or 'default'}'"
            else:
                effective_region = "us-east-1"
                region_source = "default"

        if interactive and not region:
            console.print(
                f"\n[dim]Detected region: {effective_region} (from {region_source})[/]"
            )
            if not Confirm.ask("Use this region?", default=True):
                effective_region = Prompt.ask("Enter region", default=effective_region)

        # Validate output format
        valid_formats = ("terraform", "cloudformation", "pulumi")
        if output_format not in valid_formats:
            console.print(
                f"[red]Error:[/] Invalid format '{output_format}'. "
                f"Use one of: {', '.join(valid_formats)}"
            )
            raise typer.Exit(1)

        # Validate backend options
        valid_backends = ("local", "s3")
        if backend not in valid_backends:
            console.print(
                f"[red]Error:[/] Invalid backend '{backend}'. "
                f"Use one of: {', '.join(valid_backends)}"
            )
            raise typer.Exit(1)

        if backend == "s3" and not backend_bucket:
            console.print(
                "[red]Error:[/] --backend-bucket is required when using S3 backend"
            )
            raise typer.Exit(1)

        # Backend is only applicable for Terraform format
        if backend == "s3" and output_format != "terraform":
            console.print(
                f"[yellow]Warning:[/] Backend options only apply to Terraform format. "
                f"Ignoring --backend for {output_format}."
            )
            backend = "local"

        if interactive:
            console.print(f"\n[dim]Current format: {output_format}[/]")
            if not Confirm.ask("Use this format?", default=True):
                output_format = Prompt.ask(
                    "Select format",
                    default="terraform",
                    choices=list(valid_formats),
                )

        # Get the appropriate renderer
        format_info = {
            "terraform": ("Terraform HCL", "Free+"),
            "cloudformation": ("CloudFormation YAML", "Solo+"),
            "pulumi": ("Pulumi Python", "Pro+"),
        }
        format_name, plan_required = format_info[output_format]

        manager = get_license_manager()
        plan_badge = f"[dim]({manager.current_plan.value})[/]"

        console.print(
            Panel(
                f"[bold]RepliMap Clone[/] v{__version__} {plan_badge}\n"
                f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
                f"Profile: [cyan]{profile or 'default'}[/]\n"
                f"Format: [cyan]{format_name}[/] ({plan_required})\n"
                f"Mode: [cyan]{mode}[/]\n"
                f"Output: [cyan]{output_dir}[/]\n"
                f"Downsize: [cyan]{downsize}[/]"
                + (f"\nRename: [cyan]{rename_pattern}[/]" if rename_pattern else ""),
                title="Configuration",
                border_style="cyan",
            )
        )

        if mode not in ("dry-run", "generate"):
            console.print(
                f"[red]Error:[/] Invalid mode '{mode}'. Use 'dry-run' or 'generate'."
            )
            raise typer.Exit(1)

        # Get AWS session
        session = get_aws_session(profile, effective_region, use_cache=not no_cache)

        # Try to load from cache first (global signal handler handles Ctrl-C)
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

        console.print()
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=console,
            refresh=refresh,
        )

        # Use cached graph or scan
        if cached_graph is not None:
            graph = cached_graph
        else:
            # Initialize graph
            graph = GraphEngine()

            # Run all scanners with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Scanning AWS resources...", total=None)
                run_all_scanners(session, effective_region, graph)
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=profile or "default",
                region=effective_region,
                console=console,
            )

        stats = graph.statistics()
        console.print(
            f"[green]Found[/] {stats['total_resources']} resources "
            f"with {stats['total_dependencies']} dependencies"
        )

        # Apply transformations
        console.print()

        # Determine if Right-Sizer will handle optimization
        effective_downsize = downsize
        if dev_mode and output_format == "terraform":
            from replimap.licensing.gates import check_right_sizer_allowed

            rightsizer_result = check_right_sizer_allowed()
            if rightsizer_result.allowed:
                # Right-Sizer will handle optimization - skip DownsizeTransformer
                effective_downsize = False
                console.print(
                    "[dim]DownsizeTransformer skipped "
                    "(Right-Sizer will handle optimization)[/dim]"
                )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Applying transformations...", total=None)
            pipeline = create_default_pipeline(
                downsize=effective_downsize,
                rename_pattern=rename_pattern,
                sanitize=True,
            )
            graph = pipeline.execute(graph)
            progress.update(task, completed=True)

        console.print(f"[green]Applied[/] {len(pipeline)} transformers")

        # Select renderer based on format
        if output_format == "terraform":
            renderer = TerraformRenderer()
        elif output_format == "cloudformation":
            renderer = CloudFormationRenderer()
        else:  # pulumi
            renderer = PulumiRenderer()

        # Preview
        preview = renderer.preview(graph)

        # Show output files table
        console.print()
        table = Table(title="Output Files", show_header=True, header_style="bold cyan")
        table.add_column("File", style="dim")
        table.add_column("Resources", justify="right")

        for filename, resources in sorted(preview.items()):
            table.add_row(filename, str(len(resources)))

        console.print(table)

        if mode == "dry-run":
            console.print()
            console.print(
                Panel(
                    "[yellow]This is a dry-run.[/]\n"
                    "Use [bold]--mode generate[/] to create files.",
                    border_style="yellow",
                )
            )
        else:
            console.print()
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        f"Generating {format_name} files...", total=None
                    )
                    written = renderer.render(graph, output_dir)
                    progress.update(task, completed=True)

                # Print summary of skipped resource types (if any)
                if hasattr(renderer, "print_summary"):
                    renderer.print_summary(console)

                # Print warning about redacted secrets (if any)
                if hasattr(renderer, "scrubber") and renderer.scrubber.has_findings():
                    renderer.scrubber.print_warnings(console)

                console.print(
                    Panel(
                        f"[green]Generated {len(written)} files[/] "
                        f"in [bold]{output_dir}[/]",
                        border_style="green",
                    )
                )

                # BACKEND GENERATION (After Terraform files, before Right-Sizer)
                if output_format == "terraform":
                    from replimap.renderers.backend import (
                        BackendGenerator,
                        LocalBackendConfig,
                        S3BackendConfig,
                    )

                    backend_generator = BackendGenerator()

                    if backend == "s3":
                        s3_config = S3BackendConfig(
                            bucket=backend_bucket,  # type: ignore[arg-type]
                            key=backend_key,
                            region=backend_region or effective_region,
                            encrypt=True,
                            dynamodb_table=backend_dynamodb,
                        )

                        # Generate backend.tf
                        backend_file = backend_generator.generate_s3_backend(
                            s3_config, output_dir
                        )
                        console.print(
                            f"[green]✓ Generated S3 backend:[/] {backend_file}"
                        )

                        # Generate bootstrap if requested
                        if backend_bootstrap:
                            bootstrap_file = (
                                backend_generator.generate_backend_bootstrap(
                                    s3_config, output_dir
                                )
                            )
                            console.print(
                                f"[green]✓ Generated backend bootstrap:[/] {bootstrap_file}"
                            )
                            console.print()
                            console.print(
                                "[yellow]To create the backend infrastructure:[/]"
                            )
                            console.print(f"  cd {output_dir}/bootstrap")
                            console.print("  terraform init")
                            console.print("  terraform apply")
                            console.print()

                    else:
                        # Local backend (explicit generation is optional)
                        local_config = LocalBackendConfig()
                        backend_file = backend_generator.generate_local_backend(
                            local_config, output_dir
                        )
                        console.print(f"[dim]Using local backend: {backend_file}[/dim]")

                # RIGHT-SIZER INTEGRATION (After Terraform generation)
                if dev_mode and output_format == "terraform":
                    from replimap.cost.rightsizer import (
                        DowngradeStrategy,
                        RightSizerClient,
                        check_and_prompt_upgrade,
                        right_sizer_success_panel,
                    )

                    # Check license first
                    if not check_and_prompt_upgrade():
                        console.print(
                            "\n[yellow]Right-Sizer skipped. "
                            "Continuing with production defaults.[/yellow]"
                        )
                    else:
                        console.print(
                            "\n[cyan]Analyzing resources for "
                            "Right-Sizer optimization...[/cyan]\n"
                        )

                        try:
                            # Initialize client
                            rightsizer = RightSizerClient()

                            # Extract resource metadata from graph
                            all_resources = graph.get_all_resources()
                            summaries = rightsizer.extract_resources(
                                all_resources, effective_region
                            )

                            if not summaries:
                                console.print(
                                    "[yellow]No rightsizable resources found "
                                    "(EC2, RDS, ElastiCache).[/yellow]"
                                )
                            else:
                                console.print(
                                    f"[dim]Analyzing {len(summaries)} "
                                    f"resources...[/dim]\n"
                                )

                                # Get suggestions from API
                                strategy = DowngradeStrategy(dev_strategy.lower())
                                result = rightsizer.get_suggestions(summaries, strategy)

                                if result.success and result.suggestions:
                                    # 1. Display recommendations table
                                    rightsizer.display_suggestions_table(result)

                                    # 2. Generate and write tfvars file
                                    tfvars_content = rightsizer.generate_tfvars_content(
                                        result.suggestions
                                    )
                                    tfvars_path = rightsizer.write_tfvars_file(
                                        str(output_dir), tfvars_content
                                    )

                                    # 3. Display success panel
                                    console.print(
                                        right_sizer_success_panel(
                                            original_monthly=(
                                                result.total_current_monthly
                                            ),
                                            recommended_monthly=(
                                                result.total_recommended_monthly
                                            ),
                                            suggestions_count=(
                                                result.resources_with_suggestions
                                            ),
                                            skipped_count=result.resources_skipped,
                                            tfvars_filename=os.path.basename(
                                                tfvars_path
                                            ),
                                        )
                                    )

                                elif result.error_message:
                                    console.print(
                                        f"\n[red]Right-Sizer error: "
                                        f"{result.error_message}[/red]"
                                    )
                                    console.print(
                                        "[yellow]Continuing with "
                                        "production defaults.[/yellow]"
                                    )

                                else:
                                    console.print(
                                        "[green]All resources are "
                                        "already optimally sized![/green]"
                                    )

                        except Exception as e:
                            # Graceful degradation - don't crash the whole clone
                            console.print(f"\n[red]Right-Sizer error: {e}[/red]")
                            console.print(
                                "[yellow]Continuing with production defaults.[/yellow]"
                            )

            except FeatureNotAvailableError as e:
                console.print()
                console.print(
                    Panel(
                        f"[red]Feature not available:[/] {e}\n\n"
                        f"Upgrade your plan to use {format_name} output:\n"
                        f"[bold]https://replimap.com/pricing[/]",
                        title="Upgrade Required",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

        console.print()
