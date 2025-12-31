"""
AWS session management utilities.

Provides functions for creating boto3 sessions with MFA support,
credential caching, and profile management.
"""

from __future__ import annotations

import configparser
import fcntl
import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import typer
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from rich.panel import Panel

from replimap.cli.utils.console import console

# Credential cache directory - exported for use by cache status command
CACHE_DIR = Path.home() / ".replimap" / "cache"
CREDENTIAL_CACHE_FILE = CACHE_DIR / "credentials.json"
CREDENTIAL_CACHE_TTL = timedelta(hours=12)  # Cache MFA credentials for 12 hours

__all__ = [
    "CACHE_DIR",
    "CREDENTIAL_CACHE_FILE",
    "CREDENTIAL_CACHE_TTL",
    "get_available_profiles",
    "get_profile_region",
    "get_credential_cache_key",
    "get_cached_credentials",
    "save_cached_credentials",
    "clear_credential_cache",
    "get_aws_session",
]


def get_available_profiles() -> list[str]:
    """Get list of available AWS profiles from config."""
    profiles = ["default"]
    config_path = Path.home() / ".aws" / "config"
    credentials_path = Path.home() / ".aws" / "credentials"

    for path in [config_path, credentials_path]:
        if path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            for section in config.sections():
                # Config file uses "profile xxx" format, credentials uses just "xxx"
                if section.startswith("profile "):
                    profiles.append(section.replace("profile ", ""))
                elif section != "default":
                    profiles.append(section)

    return sorted(set(profiles))


def get_profile_region(profile: str | None) -> str | None:
    """
    Get the default region for a profile from AWS config.

    Args:
        profile: AWS profile name

    Returns:
        Region string if found, None otherwise
    """
    config_path = Path.home() / ".aws" / "config"
    if not config_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(config_path)

    # Determine section name
    if profile and profile != "default":
        section = f"profile {profile}"
    else:
        section = "default"

    if section in config and "region" in config[section]:
        return config[section]["region"]

    # Also check environment variable
    return os.environ.get("AWS_DEFAULT_REGION")


def get_credential_cache_key(profile: str | None) -> str:
    """Generate a cache key for credentials."""
    key = f"profile:{profile or 'default'}"
    return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()


def get_cached_credentials(profile: str | None) -> dict | None:
    """
    Get cached credentials if valid.

    Returns cached session credentials to avoid repeated MFA prompts.
    Thread-safe with file locking.
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        return None

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            # Acquire shared lock for reading
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                cache = json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        cache_key = get_credential_cache_key(profile)
        if cache_key not in cache:
            return None

        entry = cache[cache_key]
        expires_at = datetime.fromisoformat(entry["expires_at"])

        if datetime.now() >= expires_at:
            return None

        return entry["credentials"]
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        return None


def save_cached_credentials(
    profile: str | None,
    credentials: dict,
    expiration: datetime | None = None,
) -> None:
    """
    Save credentials to cache.

    Thread-safe with file locking and atomic write pattern.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Use exclusive lock for read-modify-write operation
    # Open in append mode to create file if it doesn't exist
    with open(CREDENTIAL_CACHE_FILE, "a+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            # Read existing cache
            f.seek(0)
            content = f.read()
            try:
                cache = json.loads(content) if content.strip() else {}
            except json.JSONDecodeError:
                cache = {}

            cache_key = get_credential_cache_key(profile)

            # Use provided expiration or default TTL
            if expiration:
                expires_at = expiration
            else:
                expires_at = datetime.now() + CREDENTIAL_CACHE_TTL

            cache[cache_key] = {
                "credentials": credentials,
                "expires_at": expires_at.isoformat(),
                "profile": profile,
            }

            # Atomic write: write to temp file, then rename
            fd, temp_path = tempfile.mkstemp(
                dir=CACHE_DIR, prefix=".credentials_", suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w") as temp_f:
                    json.dump(cache, temp_f, indent=2)
                os.chmod(temp_path, 0o600)
                os.rename(temp_path, CREDENTIAL_CACHE_FILE)
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def clear_credential_cache(profile: str | None = None) -> None:
    """
    Clear credential cache for a profile or all profiles.

    Thread-safe with file locking.
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        return

    if profile is None:
        # Clear all - atomic operation
        try:
            CREDENTIAL_CACHE_FILE.unlink()
        except FileNotFoundError:
            pass
        return

    try:
        with open(CREDENTIAL_CACHE_FILE, "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                content = f.read()
                cache = json.loads(content) if content.strip() else {}

                cache_key = get_credential_cache_key(profile)
                if cache_key in cache:
                    del cache[cache_key]

                # Atomic write
                fd, temp_path = tempfile.mkstemp(
                    dir=CACHE_DIR, prefix=".credentials_", suffix=".tmp"
                )
                try:
                    with os.fdopen(fd, "w") as temp_f:
                        json.dump(cache, temp_f, indent=2)
                    os.rename(temp_path, CREDENTIAL_CACHE_FILE)
                except Exception:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    raise
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (json.JSONDecodeError, KeyError, OSError):
        pass


def get_aws_session(
    profile: str | None, region: str, use_cache: bool = True
) -> boto3.Session:
    """
    Create a boto3 session with the specified profile and region.

    Supports credential caching to avoid repeated MFA prompts.

    Args:
        profile: AWS profile name (optional)
        region: AWS region
        use_cache: Whether to use credential caching (default: True)

    Returns:
        Configured boto3 Session

    Raises:
        typer.Exit: If credentials are invalid
    """
    # Try cached credentials first (for MFA sessions)
    if use_cache:
        cached = get_cached_credentials(profile)
        if cached:
            try:
                session = boto3.Session(
                    aws_access_key_id=cached["access_key"],
                    aws_secret_access_key=cached["secret_key"],
                    aws_session_token=cached.get("session_token"),
                    region_name=region,
                )
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](cached credentials)[/]"
                )
                return session
            except (ClientError, NoCredentialsError):
                # Cache invalid, continue with normal auth
                clear_credential_cache(profile)

    try:
        session = boto3.Session(profile_name=profile, region_name=region)

        # Verify credentials work
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        # Cache the credentials if they're temporary (MFA)
        credentials = session.get_credentials()
        if credentials and use_cache:
            frozen = credentials.get_frozen_credentials()
            if frozen.token:  # Has session token = temporary credentials
                save_cached_credentials(
                    profile,
                    {
                        "access_key": frozen.access_key,
                        "secret_key": frozen.secret_key,
                        "session_token": frozen.token,
                    },
                )
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](credentials cached for 12h)[/]"
                )
            else:
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"(Account: {identity['Account']})"
                )
        else:
            console.print(
                f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                f"(Account: {identity['Account']})"
            )

        return session

    except ProfileNotFound:
        available = get_available_profiles()
        console.print(
            Panel(
                f"[red]Profile '{profile}' not found.[/]\n\n"
                f"Available profiles: [cyan]{', '.join(available)}[/]\n\n"
                "Configure a new profile with: [bold]aws configure --profile <name>[/]",
                title="Profile Not Found",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except NoCredentialsError:
        console.print(
            Panel(
                "[red]No AWS credentials found.[/]\n\n"
                "Configure credentials with:\n"
                "  [bold]aws configure[/] (for default profile)\n"
                "  [bold]aws configure --profile <name>[/] (for named profile)\n\n"
                "Or set environment variables:\n"
                "  [dim]AWS_ACCESS_KEY_ID[/]\n"
                "  [dim]AWS_SECRET_ACCESS_KEY[/]\n"
                "  [dim]AWS_SESSION_TOKEN[/] (optional)",
                title="Authentication Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ExpiredToken":
            clear_credential_cache(profile)
            console.print(
                Panel(
                    "[yellow]Session token expired.[/]\n\n"
                    "Please re-authenticate. Your cached credentials have been cleared.",
                    title="Session Expired",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel(
                    f"[red]AWS authentication failed:[/]\n{e}",
                    title="Authentication Error",
                    border_style="red",
                )
            )
        raise typer.Exit(1)
