"""
Credential Health Checker.

Provides proactive security warnings for AWS credential hygiene:
- Access key age detection (90 day warning, 180 day critical)
- Root account usage warning
- MFA enablement status (future)

These checks help organizations maintain compliance with:
- AWS Security Best Practices
- SOC2 access control requirements
- PCI-DSS credential rotation policies
- CIS AWS Foundations Benchmark

Usage:
    from replimap.core.security.credential_checker import CredentialChecker

    checker = CredentialChecker(session)
    checker.check_and_warn()  # Displays warnings if issues found

    # Skip checks (for CI/CD or automation)
    checker.check_and_warn(skip_check=True)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Optional

from botocore.exceptions import ClientError

if TYPE_CHECKING:
    import boto3

logger = logging.getLogger(__name__)


class CredentialChecker:
    """
    Check credential health and provide security recommendations.

    Performs non-blocking security checks at scan startup to warn users
    about potential credential security issues. All checks are advisory
    and do not prevent scanning.

    Checks performed:
    - Access key age (warns at 90 days, critical at 180 days)
    - Root account usage (always warns)

    All checks gracefully handle permission denials and continue silently.
    """

    # Access key age thresholds (AWS recommends 90 day rotation)
    WARNING_AGE_DAYS = 90
    CRITICAL_AGE_DAYS = 180

    def __init__(self, session: boto3.Session) -> None:
        """
        Initialize the credential checker.

        Args:
            session: Configured boto3 session to check
        """
        self.session = session

    def check_and_warn(self, skip_check: bool = False) -> None:
        """
        Run all credential health checks and display warnings.

        Checks are advisory only - errors during checking are logged
        at debug level and do not interrupt the program.

        Args:
            skip_check: If True, skip all checks (for --skip-credential-check flag)
        """
        if skip_check:
            logger.debug("Credential checks skipped by user request")
            return

        try:
            # Get caller identity first
            sts = self.session.client("sts")
            identity = sts.get_caller_identity()

            arn = identity["Arn"]

            # Check for root account usage (always dangerous)
            if ":root" in arn:
                self._warn_root_usage()
                return  # Don't check key age for root

            # Check if using long-term credentials (IAM User)
            # Only long-term credentials have access key age concerns
            credentials = self.session.get_credentials()
            if credentials:
                frozen = credentials.get_frozen_credentials()

                # Only check key age for long-term credentials (no session token)
                # Temporary credentials (roles, STS) don't have this concern
                if not frozen.token:
                    self._check_access_key_age(identity)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ExpiredToken", "InvalidClientTokenId"):
                # Credentials are already expired - this will be handled
                # by the SessionManager during scanning
                logger.debug(f"Credential check skipped: {error_code}")
            else:
                logger.debug(f"Could not perform credential checks: {e}")

        except Exception as e:
            # Never crash on credential checks
            logger.debug(f"Unexpected error in credential checks: {e}")

    def _check_access_key_age(self, identity: dict) -> None:
        """
        Check IAM access key age and warn if old.

        Queries IAM for access key metadata and warns if the key
        is older than recommended rotation period.

        Args:
            identity: STS caller identity response
        """
        try:
            from rich.console import Console
            from rich.panel import Panel
        except ImportError:
            logger.debug("Rich not available for credential warnings")
            return

        console = Console()

        try:
            # Extract username from ARN
            arn = identity["Arn"]
            if ":user/" not in arn:
                # Not an IAM user (could be a role or federated user)
                return

            user_name = arn.split(":user/")[-1]

            # Query IAM for access key metadata
            iam = self.session.client("iam")
            response = iam.list_access_keys(UserName=user_name)

            for key in response.get("AccessKeyMetadata", []):
                if key["Status"] != "Active":
                    continue

                create_date = key["CreateDate"]
                if create_date.tzinfo is None:
                    create_date = create_date.replace(tzinfo=UTC)

                age_days = (datetime.now(UTC) - create_date).days

                # Mask access key ID for display (show first 8 chars)
                key_id_masked = key["AccessKeyId"][:8] + "..."

                if age_days >= self.CRITICAL_AGE_DAYS:
                    self._display_critical_key_warning(
                        console, key, key_id_masked, age_days, user_name
                    )

                elif age_days >= self.WARNING_AGE_DAYS:
                    self._display_key_warning(
                        console, key_id_masked, age_days, create_date
                    )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                # User doesn't have IAM permissions - that's fine
                logger.debug(
                    "No IAM permissions to check access key age "
                    "(iam:ListAccessKeys required)"
                )
            else:
                logger.debug(f"Could not check access key age: {e}")

        except Exception as e:
            logger.debug(f"Unexpected error checking access key age: {e}")

    def _display_critical_key_warning(
        self,
        console: any,
        key: dict,
        key_id_masked: str,
        age_days: int,
        user_name: str,
    ) -> None:
        """Display critical warning for very old access keys."""
        from rich.panel import Panel

        create_date = key["CreateDate"]
        if create_date.tzinfo is None:
            create_date = create_date.replace(tzinfo=UTC)

        console.print(
            Panel(
                f"[red bold]Access Key Critically Old[/]\n\n"
                f"Access Key: [bold]{key_id_masked}[/]\n"
                f"Age: [bold red]{age_days} days[/]\n"
                f"Created: {create_date.strftime('%Y-%m-%d')}\n\n"
                f"[red]This significantly increases security risk![/]\n"
                f"AWS recommends rotating access keys every 90 days.\n\n"
                f"[dim]To rotate:\n"
                f"  1. aws iam create-access-key --user-name {user_name}\n"
                f"  2. Update ~/.aws/credentials with new key\n"
                f"  3. aws iam delete-access-key --access-key-id {key['AccessKeyId']}[/]",
                title="Critical Security Warning",
                border_style="red",
            )
        )

    def _display_key_warning(
        self,
        console: any,
        key_id_masked: str,
        age_days: int,
        create_date: datetime,
    ) -> None:
        """Display warning for access keys past recommended rotation age."""
        from rich.panel import Panel

        console.print(
            Panel(
                f"[yellow]Access Key Rotation Recommended[/]\n\n"
                f"Access Key: [bold]{key_id_masked}[/]\n"
                f"Age: [bold yellow]{age_days} days[/]\n"
                f"Created: {create_date.strftime('%Y-%m-%d')}\n\n"
                f"AWS recommends rotating access keys every 90 days.\n\n"
                f"[dim]Use --skip-credential-check to suppress this warning.[/]",
                title="Security Recommendation",
                border_style="yellow",
            )
        )

    def _warn_root_usage(self) -> None:
        """Warn about root account usage."""
        try:
            from rich.console import Console
            from rich.panel import Panel
        except ImportError:
            logger.warning("Root account detected - this is strongly discouraged")
            return

        console = Console()
        console.print(
            Panel(
                "[red bold]Root Account Detected[/]\n\n"
                "You are using AWS root account credentials.\n"
                "This is [bold]strongly discouraged[/] for security reasons.\n\n"
                "Risks:\n"
                "  - Root has unrestricted access to all resources\n"
                "  - Root credentials cannot be scoped or limited\n"
                "  - Compromise of root = total account takeover\n\n"
                "Recommendations:\n"
                "  - Create an IAM user with required permissions\n"
                "  - Enable MFA on the root account\n"
                "  - Delete root access keys if they exist\n"
                "  - Use IAM roles for applications and services",
                title="Root Account Warning",
                border_style="red",
            )
        )

    def get_credential_summary(self) -> Optional[dict]:
        """
        Get a summary of credential information.

        Returns:
            Dictionary with credential info, or None if unavailable.
            Keys: account_id, user_arn, credential_type, access_key_age_days
        """
        try:
            sts = self.session.client("sts")
            identity = sts.get_caller_identity()

            summary = {
                "account_id": identity["Account"],
                "user_arn": identity["Arn"],
                "user_id": identity["UserId"],
            }

            # Determine credential type
            arn = identity["Arn"]
            if ":root" in arn:
                summary["credential_type"] = "root"
            elif ":assumed-role/" in arn:
                summary["credential_type"] = "assumed_role"
            elif ":user/" in arn:
                summary["credential_type"] = "iam_user"
            elif ":federated-user/" in arn:
                summary["credential_type"] = "federated_user"
            else:
                summary["credential_type"] = "unknown"

            # Try to get access key age for IAM users
            if summary["credential_type"] == "iam_user":
                try:
                    user_name = arn.split(":user/")[-1]
                    iam = self.session.client("iam")
                    response = iam.list_access_keys(UserName=user_name)

                    for key in response.get("AccessKeyMetadata", []):
                        if key["Status"] == "Active":
                            create_date = key["CreateDate"]
                            if create_date.tzinfo is None:
                                create_date = create_date.replace(tzinfo=UTC)
                            age = datetime.now(UTC) - create_date
                            summary["access_key_age_days"] = age.days
                            break

                except ClientError:
                    pass  # No IAM permissions

            return summary

        except Exception as e:
            logger.debug(f"Could not get credential summary: {e}")
            return None
