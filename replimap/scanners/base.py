"""
Base Scanner for RepliMap.

All resource scanners inherit from BaseScanner and implement the scan() method
to extract resources from AWS and add them to the graph.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


class ScannerError(Exception):
    """Base exception for scanner errors."""

    pass


class PermissionError(ScannerError):
    """Raised when AWS permissions are insufficient."""

    pass


class BaseScanner(ABC):
    """
    Abstract base class for AWS resource scanners.

    Each scanner is responsible for:
    1. Calling AWS APIs to retrieve resources
    2. Converting AWS responses to ResourceNodes
    3. Adding nodes and dependencies to the graph

    Subclasses must implement:
    - resource_types: List of Terraform resource types this scanner handles
    - scan(): The main scanning logic
    """

    # Terraform resource types this scanner handles
    resource_types: ClassVar[list[str]] = []

    def __init__(self, session: boto3.Session, region: str) -> None:
        """
        Initialize the scanner with AWS credentials.

        Args:
            session: Configured boto3 session
            region: AWS region to scan
        """
        self.session = session
        self.region = region
        self._clients: dict[str, object] = {}

    def get_client(self, service_name: str) -> object:
        """
        Get or create a boto3 client for the specified service.

        Clients are cached for reuse within the scanner.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')

        Returns:
            Configured boto3 client
        """
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name, region_name=self.region
            )
        return self._clients[service_name]

    @abstractmethod
    def scan(self, graph: GraphEngine) -> None:
        """
        Scan AWS resources and add them to the graph.

        This method should:
        1. Call AWS APIs to list resources
        2. Create ResourceNode instances for each resource
        3. Add nodes to the graph
        4. Establish dependency edges

        Args:
            graph: The GraphEngine to populate

        Raises:
            ScannerError: If scanning fails
            PermissionError: If AWS permissions are insufficient
        """
        pass

    def _extract_tags(self, tag_list: list[dict] | None) -> dict[str, str]:
        """
        Convert AWS tag list to dictionary.

        AWS returns tags as [{"Key": "Name", "Value": "my-resource"}, ...].
        This converts to {"Name": "my-resource", ...}.

        Args:
            tag_list: AWS tag list or None

        Returns:
            Dictionary of tag key-value pairs
        """
        if not tag_list:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tag_list}

    def _handle_aws_error(self, error: ClientError, operation: str) -> None:
        """
        Handle AWS API errors with appropriate logging and exceptions.

        Args:
            error: The boto3 ClientError
            operation: Description of the operation that failed

        Raises:
            PermissionError: If the error is access-related
            ScannerError: For other AWS errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        if error_code in (
            "AccessDenied",
            "UnauthorizedAccess",
            "AccessDeniedException",
        ):
            logger.error(f"Permission denied: {operation} - {error_message}")
            raise PermissionError(
                f"Insufficient permissions for {operation}: {error_message}"
            )

        logger.error(f"AWS error during {operation}: {error_code} - {error_message}")
        raise ScannerError(f"AWS error during {operation}: {error_message}")


class ScannerRegistry:
    """
    Registry for available scanners.

    Provides a central place to register and retrieve scanners,
    enabling dynamic discovery and execution.
    """

    _scanners: ClassVar[list[type[BaseScanner]]] = []

    @classmethod
    def register(cls, scanner_class: type[BaseScanner]) -> type[BaseScanner]:
        """
        Register a scanner class.

        Can be used as a decorator:
            @ScannerRegistry.register
            class MyScanner(BaseScanner):
                ...

        Args:
            scanner_class: The scanner class to register

        Returns:
            The same scanner class (for decorator use)
        """
        if scanner_class not in cls._scanners:
            cls._scanners.append(scanner_class)
            logger.debug(f"Registered scanner: {scanner_class.__name__}")
        return scanner_class

    @classmethod
    def get_all(cls) -> list[type[BaseScanner]]:
        """Get all registered scanner classes."""
        return cls._scanners.copy()

    @classmethod
    def get_for_type(cls, resource_type: str) -> type[BaseScanner] | None:
        """
        Get the scanner that handles a specific resource type.

        Args:
            resource_type: Terraform resource type (e.g., 'aws_vpc')

        Returns:
            Scanner class if found, None otherwise
        """
        for scanner_class in cls._scanners:
            if resource_type in scanner_class.resource_types:
                return scanner_class
        return None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered scanners (useful for testing)."""
        cls._scanners.clear()


def run_all_scanners(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
) -> dict[str, Exception | None]:
    """
    Run all registered scanners.

    Args:
        session: Configured boto3 session
        region: AWS region to scan
        graph: The GraphEngine to populate

    Returns:
        Dictionary mapping scanner names to exceptions (None if successful)
    """
    results: dict[str, Exception | None] = {}

    for scanner_class in ScannerRegistry.get_all():
        scanner_name = scanner_class.__name__
        logger.info(f"Running {scanner_name}...")

        try:
            scanner = scanner_class(session, region)
            scanner.scan(graph)
            results[scanner_name] = None
            logger.info(f"{scanner_name} completed successfully")
        except Exception as e:
            results[scanner_name] = e
            logger.error(f"{scanner_name} failed: {e}")

    return results
