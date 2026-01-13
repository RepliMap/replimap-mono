"""
Doctor Command - Environment health check.

Checks:
1. Python version
2. Execution environment (CI vs interactive)
3. AWS credentials
4. AWS permissions
5. Terraform installation
6. Network connectivity
7. Disk space
8. Decision status
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import boto3
import typer
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from rich.panel import Panel
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import console, get_profile_region


class CheckStatus(Enum):
    """Health check status."""

    PASS = "✅"
    WARN = "⚠️"
    FAIL = "❌"
    SKIP = "⏭️"


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    status: CheckStatus
    message: str
    fix_command: str | None = None
    details: str | None = None


class DoctorCommand:
    """
    Environment health check implementation.

    Runs a series of checks to verify the environment is properly
    configured for RepliMap.
    """

    def __init__(self, profile: str | None, region: str | None):
        """
        Initialize DoctorCommand.

        Args:
            profile: AWS profile to check
            region: AWS region to check
        """
        # Lazy imports to avoid circular dependencies
        from replimap.core.context import EnvironmentDetector

        self.profile = profile
        self.region = region or get_profile_region(profile) or "us-east-1"
        self.results: list[CheckResult] = []
        self._env_detector = EnvironmentDetector

    def run(self) -> int:
        """
        Run all checks.

        Returns:
            Exit code (0 = all passed, 1 = failures)
        """
        # Header
        console.print(
            Panel(
                f"[bold blue]RepliMap Environment Doctor[/bold blue]\n"
                f"Profile: {self.profile or 'default'}\n"
                f"Region: {self.region}\n"
                f"Environment: {self._env_detector.detect().value}",
                expand=False,
            )
        )

        # Run all checks
        self._check_python()
        self._check_environment()
        self._check_credentials()
        self._check_permissions()
        self._check_terraform()
        self._check_network()
        self._check_disk()
        self._check_decisions()

        # Display results
        self._display_results()

        # Return exit code
        failures = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        return 1 if failures > 0 else 0

    def _check_python(self) -> None:
        """Check Python version."""
        version = sys.version_info

        if version >= (3, 10):
            self.results.append(
                CheckResult(
                    name="Python Version",
                    status=CheckStatus.PASS,
                    message=f"Python {version.major}.{version.minor}.{version.micro}",
                )
            )
        elif version >= (3, 9):
            self.results.append(
                CheckResult(
                    name="Python Version",
                    status=CheckStatus.WARN,
                    message=f"Python {version.major}.{version.minor} (3.10+ recommended)",
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="Python Version",
                    status=CheckStatus.FAIL,
                    message=f"Python {version.major}.{version.minor} (requires 3.9+)",
                    fix_command="pyenv install 3.11 && pyenv global 3.11",
                )
            )

    def _check_environment(self) -> None:
        """Check execution environment."""
        env = self._env_detector.detect()
        ci_name = self._env_detector.get_ci_name()

        if env.value == "ci":
            self.results.append(
                CheckResult(
                    name="Environment",
                    status=CheckStatus.WARN,
                    message=f"CI Mode ({ci_name})",
                    details="Sensitive operations will fail fast",
                )
            )
        elif env.value == "non_interactive":
            self.results.append(
                CheckResult(
                    name="Environment",
                    status=CheckStatus.WARN,
                    message="Non-interactive (no TTY)",
                    details="Interactive prompts disabled",
                )
            )
        else:
            self.results.append(
                CheckResult(
                    name="Environment",
                    status=CheckStatus.PASS,
                    message="Interactive",
                )
            )

    def _check_credentials(self) -> None:
        """Check AWS credentials."""
        try:
            session = boto3.Session(profile_name=self.profile)
            sts = session.client("sts", region_name=self.region)
            identity = sts.get_caller_identity()

            arn = identity.get("Arn", "Unknown")
            # Truncate long ARNs
            if len(arn) > 50:
                arn = arn[:47] + "..."

            self.results.append(
                CheckResult(
                    name="AWS Credentials",
                    status=CheckStatus.PASS,
                    message=f"Profile: {self.profile or 'default'}",
                    details=f"Identity: {arn}",
                )
            )
        except ProfileNotFound:
            self.results.append(
                CheckResult(
                    name="AWS Credentials",
                    status=CheckStatus.FAIL,
                    message=f"Profile '{self.profile}' not found",
                    fix_command=f"aws configure --profile {self.profile}",
                )
            )
        except NoCredentialsError:
            self.results.append(
                CheckResult(
                    name="AWS Credentials",
                    status=CheckStatus.FAIL,
                    message="No credentials configured",
                    fix_command="aws configure",
                )
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ExpiredToken":
                self.results.append(
                    CheckResult(
                        name="AWS Credentials",
                        status=CheckStatus.FAIL,
                        message="Session token expired",
                        fix_command="replimap cache clear && aws sso login",
                    )
                )
            else:
                self.results.append(
                    CheckResult(
                        name="AWS Credentials",
                        status=CheckStatus.FAIL,
                        message=f"Credential error: {error_code}",
                        details=str(e)[:80],
                    )
                )
        except Exception as e:
            self.results.append(
                CheckResult(
                    name="AWS Credentials",
                    status=CheckStatus.FAIL,
                    message="Credential check failed",
                    details=str(e)[:80],
                )
            )

    def _check_permissions(self) -> None:
        """Check AWS permissions."""
        # Skip if credentials check failed
        cred_check = next(
            (r for r in self.results if r.name == "AWS Credentials"), None
        )
        if cred_check and cred_check.status == CheckStatus.FAIL:
            self.results.append(
                CheckResult(
                    name="AWS Permissions",
                    status=CheckStatus.SKIP,
                    message="Skipped (credentials check failed)",
                )
            )
            return

        try:
            session = boto3.Session(
                profile_name=self.profile,
                region_name=self.region,
            )
            ec2 = session.client("ec2")
            ec2.describe_vpcs(MaxResults=1)

            self.results.append(
                CheckResult(
                    name="AWS Permissions",
                    status=CheckStatus.PASS,
                    message="EC2 read access verified",
                )
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("AccessDenied", "UnauthorizedOperation"):
                self.results.append(
                    CheckResult(
                        name="AWS Permissions",
                        status=CheckStatus.FAIL,
                        message="Missing EC2 read permissions",
                        fix_command="replimap iam --generate-policy > policy.json",
                    )
                )
            else:
                self.results.append(
                    CheckResult(
                        name="AWS Permissions",
                        status=CheckStatus.WARN,
                        message=f"Could not verify: {error_code}",
                    )
                )
        except Exception as e:
            self.results.append(
                CheckResult(
                    name="AWS Permissions",
                    status=CheckStatus.WARN,
                    message="Could not verify permissions",
                    details=str(e)[:50],
                )
            )

    def _check_terraform(self) -> None:
        """Check Terraform installation."""
        tf_path = shutil.which("terraform")

        if tf_path:
            try:
                result = subprocess.run(
                    ["terraform", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                version_line = result.stdout.split("\n")[0]
                self.results.append(
                    CheckResult(
                        name="Terraform",
                        status=CheckStatus.PASS,
                        message=version_line,
                    )
                )
            except (subprocess.TimeoutExpired, OSError):
                self.results.append(
                    CheckResult(
                        name="Terraform",
                        status=CheckStatus.WARN,
                        message="Installed but version check failed",
                    )
                )
        else:
            self.results.append(
                CheckResult(
                    name="Terraform",
                    status=CheckStatus.WARN,
                    message="Not installed (optional)",
                    fix_command="brew install terraform",
                    details="Only needed for `validate` command",
                )
            )

    def _check_network(self) -> None:
        """Check network connectivity to AWS."""
        try:
            socket.create_connection(("sts.amazonaws.com", 443), timeout=5)
            self.results.append(
                CheckResult(
                    name="Network",
                    status=CheckStatus.PASS,
                    message="AWS endpoints reachable",
                )
            )
        except socket.timeout:
            self.results.append(
                CheckResult(
                    name="Network",
                    status=CheckStatus.FAIL,
                    message="Connection timeout to AWS",
                    details="Check firewall/proxy settings",
                )
            )
        except OSError as e:
            self.results.append(
                CheckResult(
                    name="Network",
                    status=CheckStatus.FAIL,
                    message="Cannot reach AWS endpoints",
                    details=str(e)[:50],
                )
            )

    def _check_disk(self) -> None:
        """Check available disk space."""
        try:
            total, used, free = shutil.disk_usage(".")
            free_gb = free // (1024**3)

            if free_gb >= 5:
                self.results.append(
                    CheckResult(
                        name="Disk Space",
                        status=CheckStatus.PASS,
                        message=f"{free_gb} GB free",
                    )
                )
            elif free_gb >= 1:
                self.results.append(
                    CheckResult(
                        name="Disk Space",
                        status=CheckStatus.WARN,
                        message=f"Only {free_gb} GB free",
                        details="Large scans may need more space",
                    )
                )
            else:
                self.results.append(
                    CheckResult(
                        name="Disk Space",
                        status=CheckStatus.FAIL,
                        message=f"Only {free_gb} GB free",
                        details="Insufficient disk space",
                    )
                )
        except OSError:
            self.results.append(
                CheckResult(
                    name="Disk Space",
                    status=CheckStatus.WARN,
                    message="Could not check disk space",
                )
            )

    def _check_decisions(self) -> None:
        """Check decision file status."""
        from replimap.decisions.manager import DecisionManager

        try:
            manager = DecisionManager()
            counts = manager.count()

            if counts["total"] == 0:
                self.results.append(
                    CheckResult(
                        name="Decisions",
                        status=CheckStatus.PASS,
                        message="No saved decisions",
                    )
                )
            elif counts["expired"] > 0:
                self.results.append(
                    CheckResult(
                        name="Decisions",
                        status=CheckStatus.WARN,
                        message=f"{counts['expired']} expired decisions",
                        fix_command="replimap decisions clear --expired",
                    )
                )
            elif counts["expiring_soon"] > 0:
                self.results.append(
                    CheckResult(
                        name="Decisions",
                        status=CheckStatus.WARN,
                        message=f"{counts['expiring_soon']} decisions expiring soon",
                        details="Use 'replimap decisions list' to review",
                    )
                )
            else:
                self.results.append(
                    CheckResult(
                        name="Decisions",
                        status=CheckStatus.PASS,
                        message=f"{counts['valid']} active decisions",
                    )
                )
        except Exception:
            self.results.append(
                CheckResult(
                    name="Decisions",
                    status=CheckStatus.PASS,
                    message="No decision file",
                )
            )

    def _display_results(self) -> None:
        """Display results in a table."""
        table = Table(title="Health Check Results", show_header=True)
        table.add_column("Check", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Message")
        table.add_column("Fix", style="dim")

        for r in self.results:
            table.add_row(
                r.name,
                r.status.value,
                r.message,
                r.fix_command or "",
            )

        console.print()
        console.print(table)

        # Show failures with details
        failures = [r for r in self.results if r.status == CheckStatus.FAIL]
        if failures:
            console.print()
            console.print("[bold red]Issues Found:[/bold red]")
            for f in failures:
                console.print(f"\n[red]• {f.name}[/red]")
                if f.details:
                    console.print(f"  {f.details}")
                if f.fix_command:
                    console.print(f"  Fix: [green]{f.fix_command}[/green]")

        # Summary
        console.print()
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        console.print(
            f"[dim]Summary: {passed} passed, {warned} warnings, {failed} failed[/dim]"
        )


def register(app: typer.Typer) -> None:
    """Register the doctor command with the main app."""

    @app.command()
    @enhanced_cli_error_handler
    def doctor(
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS profile to check",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to check",
        ),
    ) -> None:
        """
        Run environment health checks.

        Verifies Python version, AWS credentials, permissions,
        network connectivity, and more.

        Examples:
            replimap doctor
            replimap doctor --profile prod
            replimap doctor --profile prod --region us-west-2
        """
        cmd = DoctorCommand(profile, region)
        exit_code = cmd.run()
        raise typer.Exit(exit_code)


__all__ = ["DoctorCommand", "register"]
