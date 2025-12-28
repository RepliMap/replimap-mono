"""AWS Resource Scanners for RepliMap."""

# Async scanners
from .async_base import (
    AsyncBaseScanner,
    AsyncScannerRegistry,
    run_all_async_scanners,
)
from .async_vpc_scanner import AsyncVPCScanner

# Unified async scanners (P0-4) - use AsyncAWSClient with full resilience
from .unified_scanners import (
    AsyncEC2Scanner,
    AsyncIAMScanner,
    AsyncRDSScanner,
    UnifiedScannerRegistry,
    run_unified_scanners,
)
from .base import (
    BaseScanner,
    ScannerRegistry,
    parallel_process_items,
    run_all_scanners,
    with_retry,
)
from .compute_scanner import ComputeScanner
from .ec2_scanner import EC2Scanner
from .elasticache_scanner import DBParameterGroupScanner, ElastiCacheScanner
from .messaging_scanner import SNSScanner, SQSScanner

# Phase 2 Scanners
from .networking_scanner import NetworkingScanner
from .rds_scanner import RDSScanner
from .s3_scanner import S3Scanner
from .storage_scanner import EBSScanner, S3PolicyScanner
from .vpc_scanner import VPCScanner

__all__ = [
    # Base classes and utilities
    "BaseScanner",
    "ScannerRegistry",
    "run_all_scanners",
    "with_retry",
    "parallel_process_items",
    # Phase 1 Sync scanners
    "VPCScanner",
    "EC2Scanner",
    "S3Scanner",
    "RDSScanner",
    # Phase 2 Sync scanners
    "NetworkingScanner",
    "ComputeScanner",
    "ElastiCacheScanner",
    "DBParameterGroupScanner",
    "EBSScanner",
    "S3PolicyScanner",
    "SQSScanner",
    "SNSScanner",
    # Async scanners (legacy)
    "AsyncBaseScanner",
    "AsyncScannerRegistry",
    "run_all_async_scanners",
    "AsyncVPCScanner",
    # Unified async scanners (P0-4)
    "AsyncEC2Scanner",
    "AsyncRDSScanner",
    "AsyncIAMScanner",
    "UnifiedScannerRegistry",
    "run_unified_scanners",
]
