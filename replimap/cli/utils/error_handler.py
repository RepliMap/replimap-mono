"""
User-friendly error handling for CLI.

Converts AWS exceptions and other errors into helpful, actionable messages
instead of raw Python tracebacks.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any

from rich.panel import Panel

from replimap.cli.utils.console import console
from replimap.core.constants import EMAIL_SUPPORT, URL_ISSUES

if TYPE_CHECKING:
    pass


# Map AWS error codes to user-friendly messages
ERROR_MESSAGES: dict[str, dict[str, str]] = {
    # Credential errors
    "AccessDenied": {
        "title": "Permission Denied",
        "message": "Your IAM credentials lack required permissions.",
        "fix": "Ensure your IAM role has the required policies attached.",
        "docs": "https://docs.replimap.com/iam-policy",
    },
    "AccessDeniedException": {
        "title": "Permission Denied",
        "message": "Your IAM credentials lack required permissions.",
        "fix": "Ensure your IAM role has the required policies attached.",
        "docs": "https://docs.replimap.com/iam-policy",
    },
    "ExpiredToken": {
        "title": "Session Expired",
        "message": "Your AWS session token has expired.",
        "fix": "Run 'aws sso login' or refresh your credentials.",
    },
    "ExpiredTokenException": {
        "title": "Session Expired",
        "message": "Your AWS session token has expired.",
        "fix": "Run 'aws sso login' or refresh your credentials.",
    },
    "NoCredentialProviders": {
        "title": "No AWS Credentials",
        "message": "RepliMap could not find AWS credentials.",
        "fix": "Run 'aws configure' or set AWS_PROFILE environment variable.",
    },
    "InvalidClientTokenId": {
        "title": "Invalid Credentials",
        "message": "Your AWS access key is invalid or inactive.",
        "fix": "Check your ~/.aws/credentials file or regenerate keys in IAM.",
    },
    "SignatureDoesNotMatch": {
        "title": "Invalid Credentials",
        "message": "Your AWS secret key appears to be incorrect.",
        "fix": "Check your ~/.aws/credentials file for typos.",
    },
    "UnrecognizedClientException": {
        "title": "Invalid Credentials",
        "message": "AWS did not recognize your credentials.",
        "fix": "Verify your access key ID and secret key are correct.",
    },
    # Network errors
    "EndpointConnectionError": {
        "title": "Connection Failed",
        "message": "Could not connect to AWS API.",
        "fix": "Check your internet connection and VPN settings.",
    },
    "ConnectTimeoutError": {
        "title": "Connection Timeout",
        "message": "Connection to AWS timed out.",
        "fix": "Check your network connection and try again.",
    },
    "ReadTimeoutError": {
        "title": "Read Timeout",
        "message": "AWS API response timed out.",
        "fix": "Try again. If persistent, check network latency.",
    },
    # Rate limiting
    "Throttling": {
        "title": "Rate Limited",
        "message": "AWS API rate limit exceeded.",
        "fix": "Wait a few minutes and try again, or request a limit increase.",
    },
    "ThrottlingException": {
        "title": "Rate Limited",
        "message": "AWS API rate limit exceeded.",
        "fix": "Wait a few minutes and try again, or request a limit increase.",
    },
    "RequestLimitExceeded": {
        "title": "Rate Limited",
        "message": "AWS API request limit exceeded.",
        "fix": "Wait a few minutes and try again.",
    },
    "TooManyRequestsException": {
        "title": "Too Many Requests",
        "message": "AWS API is receiving too many requests.",
        "fix": "Wait a few minutes and try again.",
    },
    # Service errors
    "ServiceUnavailable": {
        "title": "Service Unavailable",
        "message": "AWS service is temporarily unavailable.",
        "fix": "Check AWS Service Health Dashboard and try again later.",
    },
    "InternalError": {
        "title": "AWS Internal Error",
        "message": "AWS experienced an internal error.",
        "fix": "Try again. If persistent, check AWS Service Health Dashboard.",
    },
    # Region errors
    "AuthFailure": {
        "title": "Region/Credentials Mismatch",
        "message": "Authentication failed. This may be a region issue.",
        "fix": "Verify the region is correct and credentials are valid for it.",
    },
}

# Special handling for exception types (not error codes)
EXCEPTION_HANDLERS: dict[str, dict[str, str]] = {
    "NoCredentialsError": {
        "title": "No AWS Credentials",
        "message": "RepliMap could not find AWS credentials.",
        "fix": "Run 'aws configure' or set AWS_PROFILE environment variable.",
    },
    "PartialCredentialsError": {
        "title": "Incomplete Credentials",
        "message": "AWS credentials are incomplete.",
        "fix": "Check your ~/.aws/credentials file has both access key and secret.",
    },
    "ProfileNotFound": {
        "title": "Profile Not Found",
        "message": "The specified AWS profile does not exist.",
        "fix": "Check your ~/.aws/config and ~/.aws/credentials files.",
    },
    "SSLError": {
        "title": "SSL/TLS Error",
        "message": "Secure connection to AWS failed.",
        "fix": "Check your network settings and proxy configuration.",
    },
    "EndpointConnectionError": {
        "title": "Connection Failed",
        "message": "Could not connect to AWS API.",
        "fix": "Check your internet connection and VPN settings.",
    },
}


def _get_error_code(error: Exception) -> str:
    """Extract error code from various exception types."""
    # botocore.exceptions.ClientError
    if hasattr(error, "response"):
        response = getattr(error, "response", {})
        if isinstance(response, dict):
            return response.get("Error", {}).get("Code", "")

    return ""


def _get_error_info(error: Exception) -> dict[str, str]:
    """Get user-friendly error info for an exception."""
    # Try to match by error code first
    error_code = _get_error_code(error)
    if error_code and error_code in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_code]

    # Try to match by exception type name
    exception_name = type(error).__name__
    if exception_name in EXCEPTION_HANDLERS:
        return EXCEPTION_HANDLERS[exception_name]

    # Check parent classes
    for parent in type(error).__mro__:
        if parent.__name__ in EXCEPTION_HANDLERS:
            return EXCEPTION_HANDLERS[parent.__name__]

    # Default error info
    return {
        "title": "AWS Error",
        "message": str(error),
        "fix": "Check AWS documentation or run with --debug for details.",
    }


def handle_aws_error(error: Exception, operation: str | None = None) -> None:
    """
    Convert AWS exception to user-friendly output and exit.

    Args:
        error: The AWS exception
        operation: Optional operation description for context
    """
    error_info = _get_error_info(error)
    error_code = _get_error_code(error)

    content = f"[bold red]{error_info['title']}[/bold red]\n\n"
    content += f"{error_info['message']}\n"

    if operation:
        content += f"\n[dim]Operation: {operation}[/dim]\n"

    if error_code:
        content += f"[dim]Error code: {error_code}[/dim]\n"

    content += f"\n[bold]Fix:[/bold] {error_info['fix']}"

    if "docs" in error_info:
        content += f"\n[dim]Docs: {error_info['docs']}[/dim]"

    console.print()
    console.print(Panel(content, title="[red]Error[/red]", border_style="red"))
    sys.exit(1)


def handle_generic_error(error: Exception, debug: bool = False) -> None:
    """
    Handle non-AWS errors gracefully.

    Args:
        error: The exception
        debug: If True, print full traceback
    """
    content = "[bold red]Unexpected Error[/bold red]\n\n"
    content += f"{type(error).__name__}: {error}\n\n"
    content += (
        f"[bold]Need help?[/bold] "
        f"[link=mailto:{EMAIL_SUPPORT}]{EMAIL_SUPPORT}[/link] or "
        f"[link={URL_ISSUES}]open an issue[/link]"
    )

    console.print()
    console.print(Panel(content, title="[red]Error[/red]", border_style="red"))

    if debug:
        console.print()
        console.print("[dim]Debug traceback:[/dim]")
        console.print_exception()

    sys.exit(1)


def setup_error_handling() -> None:
    """
    Set up global exception handling for the CLI.

    This should be called early in the CLI startup to catch unhandled exceptions.
    """
    import botocore.exceptions

    def excepthook(exc_type: type, exc_value: BaseException, exc_tb: Any) -> None:
        """Custom exception hook for unhandled exceptions."""
        # Check if debug mode
        debug = os.getenv("REPLIMAP_DEBUG", "").lower() in ("1", "true", "yes")

        # Handle KeyboardInterrupt specially
        if issubclass(exc_type, KeyboardInterrupt):
            console.print("\n[yellow]Cancelled by user[/yellow]")
            sys.exit(130)

        # Handle AWS/boto exceptions
        if issubclass(exc_type, botocore.exceptions.BotoCoreError):
            handle_aws_error(exc_value)
            return

        if issubclass(exc_type, botocore.exceptions.ClientError):
            handle_aws_error(exc_value)
            return

        # Handle generic exceptions
        handle_generic_error(exc_value, debug=debug)

    sys.excepthook = excepthook


def wrap_command(func: Any) -> Any:
    """
    Decorator to wrap a CLI command with error handling.

    Usage:
        @app.command()
        @wrap_command
        def my_command():
            ...
    """
    import functools

    import botocore.exceptions

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        debug = os.getenv("REPLIMAP_DEBUG", "").lower() in ("1", "true", "yes")

        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled by user[/yellow]")
            sys.exit(130)
        except botocore.exceptions.BotoCoreError as e:
            handle_aws_error(e)
        except botocore.exceptions.ClientError as e:
            handle_aws_error(e)
        except Exception as e:
            handle_generic_error(e, debug=debug)

    return wrapper


__all__ = [
    "handle_aws_error",
    "handle_generic_error",
    "setup_error_handling",
    "wrap_command",
    "ERROR_MESSAGES",
]
