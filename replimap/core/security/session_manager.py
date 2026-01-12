"""
Centralized AWS Session and Credential Management.

Provides a singleton SessionManager that:
- Manages a single boto3 session with credential tracking
- Caches clients by (service, region) for efficiency
- Detects credential expiration and triggers refresh
- Supports interactive MFA re-authentication during long scans
- Thread-safe for concurrent scanner access

The "Long Scan vs Short Token Deadlock" Problem:
- User authenticates with MFA, gets 1-hour STS session token
- Large AWS account scan takes 1.5-2 hours
- At 90% completion, token expires → entire scan fails
- User must re-authenticate and restart from zero

Solution:
- SessionManager tracks credential expiration
- RobustPaginator catches ExpiredToken errors
- SessionManager.force_refresh() prompts for MFA
- New credentials propagate to all cached clients
- Scan continues from where it left off

Usage:
    # Initialize once at CLI startup
    SessionManager.initialize(profile='prod', default_region='us-east-1')

    # Get clients anywhere (thread-safe)
    mgr = SessionManager.get_instance()
    ec2 = mgr.get_client('ec2', 'us-east-1')

    # Check expiration proactively
    if mgr.is_expiring_soon(minutes=10):
        mgr.force_refresh()
"""

from __future__ import annotations

import configparser
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Boto3 config for session manager clients
# Disables internal retries (we handle retries at the paginator level)
SESSION_BOTO_CONFIG = Config(
    retries={"max_attempts": 0, "mode": "standard"},
    connect_timeout=10,
    read_timeout=30,
)


class SessionManager:
    """
    Centralized AWS session and credential management.

    Thread-safe singleton that manages:
    - A single boto3 session with tracked credentials
    - Client cache by (service, region) for efficiency
    - Credential expiration detection and refresh
    - Interactive MFA re-authentication flow

    Lifecycle:
    1. Initialize() at startup with profile/region
    2. get_client() anywhere to get cached clients
    3. force_refresh() when credentials expire
    4. Clients auto-refresh after force_refresh()
    """

    _instance: Optional[SessionManager] = None
    _lock: Lock = Lock()

    # Credential expiration buffer (refresh before actual expiry)
    EXPIRY_BUFFER_MINUTES = 5

    # Default session duration for MFA (1 hour)
    MFA_SESSION_DURATION_SECONDS = 3600

    def __init__(
        self,
        profile: Optional[str] = None,
        default_region: Optional[str] = None,
    ) -> None:
        """
        Initialize SessionManager.

        Use initialize() classmethod instead of direct construction.

        Args:
            profile: AWS profile name (None for default)
            default_region: Default AWS region for clients
        """
        self.profile = profile
        self.default_region = default_region

        self._base_session: boto3.Session = boto3.Session(
            profile_name=profile,
            region_name=default_region,
        )
        self._clients: dict[tuple[str, str], Any] = {}  # (service, region) -> client
        self._credentials_expire_at: Optional[datetime] = None
        self._mfa_serial: Optional[str] = None
        self._refresh_lock = Lock()

        # Try to determine credential expiration
        self._detect_credential_expiration()

    @classmethod
    def initialize(
        cls,
        profile: Optional[str] = None,
        default_region: Optional[str] = None,
    ) -> SessionManager:
        """
        Initialize the singleton instance.

        Call once at application startup. Subsequent calls return the
        existing instance with a warning.

        Args:
            profile: AWS profile name (None for default)
            default_region: Default AWS region

        Returns:
            The SessionManager instance
        """
        with cls._lock:
            if cls._instance is not None:
                logger.warning(
                    "SessionManager already initialized. Returning existing instance."
                )
            else:
                cls._instance = cls(profile, default_region)
                logger.debug(
                    f"SessionManager initialized: profile={profile}, "
                    f"region={default_region}"
                )
            return cls._instance

    @classmethod
    def get_instance(cls) -> SessionManager:
        """
        Get the singleton instance.

        Raises:
            RuntimeError: If not initialized
        """
        if cls._instance is None:
            raise RuntimeError(
                "SessionManager not initialized. "
                "Call SessionManager.initialize() first."
            )
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if SessionManager has been initialized."""
        return cls._instance is not None

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton.

        Primarily for testing. Clears the instance and all cached clients.
        """
        with cls._lock:
            if cls._instance is not None:
                cls._instance._clients.clear()
                cls._instance = None
                logger.debug("SessionManager reset")

    def get_client(self, service: str, region: Optional[str] = None) -> Any:
        """
        Get boto3 client for service and region.

        Clients are cached by (service, region). After force_refresh(),
        the cache is cleared and new clients are created with fresh
        credentials on next access.

        Args:
            service: AWS service name (e.g., 'ec2', 'rds', 's3')
            region: AWS region (defaults to default_region)

        Returns:
            Configured boto3 client

        Raises:
            ValueError: If region not specified and no default_region
        """
        region = region or self.default_region
        if not region:
            raise ValueError(
                "Region must be specified or set as default_region during initialize()"
            )

        key = (service, region)

        if key not in self._clients:
            self._clients[key] = self._base_session.client(
                service,
                region_name=region,
                config=SESSION_BOTO_CONFIG,
            )
            logger.debug(f"Created client: {service}/{region}")

        return self._clients[key]

    def get_session(self) -> boto3.Session:
        """
        Get the underlying boto3 session.

        Useful for operations that need the session directly
        (e.g., creating resources, transfer managers).
        """
        return self._base_session

    def is_expiring_soon(self, minutes: int = 10) -> bool:
        """
        Check if credentials will expire within the given minutes.

        Returns False if:
        - Using long-term credentials (no expiration)
        - Expiration time unknown

        Args:
            minutes: Check if expiring within this many minutes

        Returns:
            True if credentials will expire soon, False otherwise
        """
        if self._credentials_expire_at is None:
            return False

        buffer = timedelta(minutes=minutes)
        expires_soon = datetime.now(UTC) + buffer >= self._credentials_expire_at

        if expires_soon:
            time_left = self._credentials_expire_at - datetime.now(UTC)
            logger.debug(
                f"Credentials expiring soon: {time_left.total_seconds():.0f}s remaining"
            )

        return expires_soon

    def get_expiration_time(self) -> Optional[datetime]:
        """Get credential expiration time, or None if not tracked."""
        return self._credentials_expire_at

    def force_refresh(self) -> bool:
        """
        Force credential refresh.

        For temporary credentials (STS/MFA):
        - Attempts automatic refresh first (works for IAM roles, instance profiles)
        - Falls back to interactive MFA if needed

        For long-term credentials:
        - Just recreates the session (effectively a no-op)

        Returns:
            True if refresh successful, False otherwise

        Note:
            This method may block for user input (MFA token).
            Callers should handle UI considerations (pause progress bars, etc.)
        """
        with self._refresh_lock:
            logger.info("Attempting credential refresh...")

            # Clear client cache regardless of outcome
            # New clients will be created with fresh credentials
            self._clients.clear()

            # Try 1: Simple session recreation
            # Works for IAM roles, instance profiles, SSO, and profiles
            # that don't require MFA for every call
            try:
                self._base_session = boto3.Session(
                    profile_name=self.profile,
                    region_name=self.default_region,
                )

                # Validate new credentials work
                sts = self._base_session.client("sts")
                sts.get_caller_identity()

                self._detect_credential_expiration()
                logger.info("Session refreshed automatically")
                return True

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                if error_code in (
                    "ExpiredToken",
                    "InvalidClientTokenId",
                    "RequestExpired",
                ):
                    # Automatic refresh failed - need MFA
                    logger.info(
                        "Automatic refresh failed (expired token). "
                        "Attempting MFA refresh..."
                    )
                    return self._refresh_with_mfa()
                else:
                    logger.error(f"Credential refresh failed: {e}")
                    return False

            except Exception as e:
                logger.error(f"Unexpected error during credential refresh: {e}")
                return False

    def _refresh_with_mfa(self) -> bool:
        """
        Interactive MFA refresh flow.

        Prompts user for MFA token via CLI and obtains new session credentials.

        Returns:
            True if MFA authentication successful, False otherwise
        """
        # Import Rich here to avoid import at module level
        try:
            from rich.console import Console
            from rich.panel import Panel
        except ImportError:
            logger.error("Rich library required for MFA prompt")
            return False

        console = Console()

        console.print()
        console.print(
            Panel(
                "[yellow]AWS session expired[/]\n\n"
                "Your temporary credentials have expired.\n"
                "MFA re-authentication is required to continue the scan.",
                title="Session Expired",
                border_style="yellow",
            )
        )

        # Get MFA serial ARN
        mfa_serial = self._get_mfa_serial()
        if not mfa_serial:
            console.print("[red]Error: Cannot determine MFA device ARN.[/]")
            console.print(
                "[dim]Ensure your AWS profile has 'mfa_serial' configured in "
                "~/.aws/config[/]"
            )
            console.print()
            console.print("[dim]Example ~/.aws/config:[/]")
            console.print(
                f"[dim]  [profile {self.profile or 'default'}]\n"
                "  mfa_serial = arn:aws:iam::123456789012:mfa/username[/]"
            )
            return False

        console.print(f"MFA Device: [cyan]{mfa_serial}[/]")

        try:
            # Prompt for MFA token
            mfa_token = console.input("[bold]Enter MFA token: [/]").strip()

            if not mfa_token:
                console.print("[red]No MFA token provided.[/]")
                return False

            if not mfa_token.isdigit() or len(mfa_token) != 6:
                console.print("[red]Invalid MFA token. Expected 6 digits.[/]")
                return False

            # Get base credentials for STS call
            base_credentials = self._get_base_credentials()

            if not base_credentials.get("access_key"):
                console.print(
                    "[red]Error: Cannot find base credentials for MFA.[/]"
                )
                console.print(
                    "[dim]Ensure aws_access_key_id is set in "
                    "~/.aws/credentials[/]"
                )
                return False

            # Create STS client with base credentials (not the expired session)
            sts = boto3.client(
                "sts",
                aws_access_key_id=base_credentials.get("access_key"),
                aws_secret_access_key=base_credentials.get("secret_key"),
                region_name=self.default_region or "us-east-1",
            )

            # Get new session token with MFA
            response = sts.get_session_token(
                SerialNumber=mfa_serial,
                TokenCode=mfa_token,
                DurationSeconds=self.MFA_SESSION_DURATION_SECONDS,
            )

            # Extract credentials from response
            creds = response["Credentials"]

            # Create new session with temporary credentials
            self._base_session = boto3.Session(
                aws_access_key_id=creds["AccessKeyId"],
                aws_secret_access_key=creds["SecretAccessKey"],
                aws_session_token=creds["SessionToken"],
                region_name=self.default_region,
            )

            # Track expiration
            self._credentials_expire_at = creds["Expiration"]
            if self._credentials_expire_at.tzinfo is None:
                self._credentials_expire_at = self._credentials_expire_at.replace(
                    tzinfo=UTC
                )

            console.print("[green]Session refreshed successfully.[/]")
            console.print(
                f"  New credentials expire at: "
                f"{self._credentials_expire_at.strftime('%H:%M:%S %Z')}"
            )
            console.print()

            logger.info(
                f"MFA refresh successful. Credentials valid until "
                f"{self._credentials_expire_at}"
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                console.print(
                    "[red]MFA authentication failed. Invalid token or expired.[/]"
                )
            else:
                console.print(f"[red]Authentication error: {e}[/]")
            return False

        except KeyboardInterrupt:
            console.print("\n[yellow]Authentication cancelled.[/]")
            return False

        except Exception as e:
            console.print(f"[red]Unexpected error during MFA: {e}[/]")
            return False

    def _detect_credential_expiration(self) -> None:
        """
        Detect credential expiration from current session.

        Sets _credentials_expire_at if temporary credentials are detected.
        """
        try:
            credentials = self._base_session.get_credentials()
            if credentials is None:
                self._credentials_expire_at = None
                return

            frozen = credentials.get_frozen_credentials()

            # Check if temporary credentials (has session token)
            if frozen.token:
                # Boto3 doesn't always expose the exact expiration time
                # For STS credentials from get_session_token, we estimate
                # For assumed roles, the credential provider may know
                #
                # Conservative estimate: 50 minutes from now
                # (gives us buffer before the typical 1-hour session expires)
                self._credentials_expire_at = datetime.now(UTC) + timedelta(minutes=50)
                logger.debug(
                    f"Detected temporary credentials. "
                    f"Estimated expiration: {self._credentials_expire_at}"
                )
            else:
                # Long-term credentials, no expiration
                self._credentials_expire_at = None
                logger.debug("Detected long-term credentials (no expiration)")

        except Exception as e:
            logger.debug(f"Could not detect credential expiration: {e}")
            self._credentials_expire_at = None

    def _get_mfa_serial(self) -> Optional[str]:
        """
        Get MFA serial ARN from profile config or cached value.

        Reads mfa_serial from ~/.aws/config for the current profile.
        """
        if self._mfa_serial:
            return self._mfa_serial

        try:
            config_path = Path.home() / ".aws" / "config"
            if not config_path.exists():
                return None

            config = configparser.ConfigParser()
            config.read(config_path)

            # AWS config uses "profile <name>" for non-default profiles
            section = f"profile {self.profile}" if self.profile else "default"

            if config.has_option(section, "mfa_serial"):
                self._mfa_serial = config.get(section, "mfa_serial")
                return self._mfa_serial

        except Exception as e:
            logger.debug(f"Could not read MFA serial from config: {e}")

        return None

    def _get_base_credentials(self) -> dict[str, Optional[str]]:
        """
        Get base (non-session) credentials for MFA flow.

        Reads aws_access_key_id and aws_secret_access_key from
        ~/.aws/credentials for the current profile.

        These are the long-term credentials used to call STS
        get_session_token with MFA.
        """
        try:
            creds_path = Path.home() / ".aws" / "credentials"
            if not creds_path.exists():
                return {}

            config = configparser.ConfigParser()
            config.read(creds_path)

            section = self.profile or "default"

            if config.has_section(section):
                return {
                    "access_key": config.get(
                        section, "aws_access_key_id", fallback=None
                    ),
                    "secret_key": config.get(
                        section, "aws_secret_access_key", fallback=None
                    ),
                }

        except Exception as e:
            logger.debug(f"Could not read base credentials: {e}")

        return {}

    def invalidate_clients(self) -> None:
        """
        Clear all cached clients.

        Call after credential refresh to ensure new clients
        use fresh credentials.
        """
        client_count = len(self._clients)
        self._clients.clear()
        logger.debug(f"Invalidated {client_count} cached clients")
