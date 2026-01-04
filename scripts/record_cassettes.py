#!/usr/bin/env python3
"""
Script to record VCR cassettes from real AWS.

Records actual AWS API responses for use in offline testing.
Cassettes are stored in tests/cassettes/ and can be committed to git.

Usage:
    # Record all scanners
    python scripts/record_cassettes.py --profile myprofile --region us-east-1

    # Record specific scanner
    python scripts/record_cassettes.py --profile myprofile --scanner ec2

    # Record with custom cassette prefix
    python scripts/record_cassettes.py --profile myprofile --prefix prod_

Prerequisites:
    - AWS credentials configured for the profile
    - vcrpy installed (pip install vcrpy)
    - Real AWS resources to record

Note:
    Cassettes are automatically sanitized to remove:
    - AWS account IDs
    - Access keys
    - Security tokens
    - Other sensitive data
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import TYPE_CHECKING

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if TYPE_CHECKING:
    import boto3

# Import after path setup
try:
    from tests.conftest import CASSETTES_DIR, VCR_AVAILABLE, vcr_config

    if not VCR_AVAILABLE:
        print("Error: vcrpy is not installed. Install with: pip install vcrpy")
        sys.exit(1)
except ImportError as e:
    print(f"Error importing VCR configuration: {e}")
    print("Make sure you're running from the project root.")
    sys.exit(1)


def get_session(profile: str, region: str) -> boto3.Session:
    """Get boto3 session for the given profile and region."""
    import boto3

    return boto3.Session(profile_name=profile, region_name=region)


async def record_vpc_cassettes(profile: str, region: str, prefix: str = "") -> None:
    """Record VPC scanner cassettes."""
    from replimap.core import GraphEngine
    from replimap.scanners.vpc_scanner import VPCScanner

    print(f"Recording VPC cassettes for {profile}/{region}...")

    cassette_name = f"{prefix}vpc_scan.yaml"
    with vcr_config.use_cassette(cassette_name, record_mode="new_episodes"):
        session = get_session(profile, region)
        graph = GraphEngine()
        scanner = VPCScanner(session, region)
        scanner.scan(graph)

        stats = graph.statistics()
        print(f"  Recorded {stats['total_resources']} VPC resources")
        print(f"  Cassette: {CASSETTES_DIR / cassette_name}")


async def record_ec2_cassettes(profile: str, region: str, prefix: str = "") -> None:
    """Record EC2 scanner cassettes."""
    from replimap.core import GraphEngine
    from replimap.scanners.ec2_scanner import EC2Scanner

    print(f"Recording EC2 cassettes for {profile}/{region}...")

    cassette_name = f"{prefix}ec2_scan.yaml"
    with vcr_config.use_cassette(cassette_name, record_mode="new_episodes"):
        session = get_session(profile, region)
        graph = GraphEngine()
        scanner = EC2Scanner(session, region)
        scanner.scan(graph)

        stats = graph.statistics()
        print(f"  Recorded {stats['total_resources']} EC2 resources")
        print(f"  Cassette: {CASSETTES_DIR / cassette_name}")


async def record_s3_cassettes(profile: str, region: str, prefix: str = "") -> None:
    """Record S3 scanner cassettes."""
    from replimap.core import GraphEngine
    from replimap.scanners.s3_scanner import S3Scanner

    print(f"Recording S3 cassettes for {profile}...")

    cassette_name = f"{prefix}s3_scan.yaml"
    with vcr_config.use_cassette(cassette_name, record_mode="new_episodes"):
        session = get_session(profile, region)
        graph = GraphEngine()
        scanner = S3Scanner(session, region)
        scanner.scan(graph)

        stats = graph.statistics()
        print(f"  Recorded {stats['total_resources']} S3 resources")
        print(f"  Cassette: {CASSETTES_DIR / cassette_name}")


async def record_rds_cassettes(profile: str, region: str, prefix: str = "") -> None:
    """Record RDS scanner cassettes."""
    from replimap.core import GraphEngine
    from replimap.scanners.rds_scanner import RDSScanner

    print(f"Recording RDS cassettes for {profile}/{region}...")

    cassette_name = f"{prefix}rds_scan.yaml"
    with vcr_config.use_cassette(cassette_name, record_mode="new_episodes"):
        session = get_session(profile, region)
        graph = GraphEngine()
        scanner = RDSScanner(session, region)
        scanner.scan(graph)

        stats = graph.statistics()
        print(f"  Recorded {stats['total_resources']} RDS resources")
        print(f"  Cassette: {CASSETTES_DIR / cassette_name}")


async def record_all(profile: str, region: str, prefix: str = "") -> None:
    """Record cassettes for all scanners."""
    print("\nRecording all scanner cassettes")
    print(f"Profile: {profile}")
    print(f"Region: {region}")
    print(f"Cassettes directory: {CASSETTES_DIR}")
    print("-" * 50)

    # Record in dependency order
    await record_vpc_cassettes(profile, region, prefix)
    await record_ec2_cassettes(profile, region, prefix)
    await record_s3_cassettes(profile, region, prefix)
    await record_rds_cassettes(profile, region, prefix)

    print("-" * 50)
    print(f"All cassettes saved to: {CASSETTES_DIR}")
    print("\nTo use in tests:")
    print("  from tests.conftest import use_cassette")
    print(f"  @use_cassette('{prefix}vpc_scan')")
    print("  def test_vpc_scanner():")
    print("      ...")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Record VCR cassettes from AWS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Record all scanners
    python scripts/record_cassettes.py --profile prod --region us-east-1

    # Record only EC2
    python scripts/record_cassettes.py --profile prod --scanner ec2

    # Record with prefix (for different environments)
    python scripts/record_cassettes.py --profile prod --prefix prod_
    python scripts/record_cassettes.py --profile staging --prefix staging_
        """,
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="AWS profile to use",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--scanner",
        choices=["vpc", "ec2", "s3", "rds", "all"],
        default="all",
        help="Specific scanner to record (default: all)",
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix for cassette names (e.g., 'prod_')",
    )

    args = parser.parse_args()

    # Ensure cassettes directory exists
    CASSETTES_DIR.mkdir(exist_ok=True)

    # Record requested cassettes
    scanner_map = {
        "vpc": record_vpc_cassettes,
        "ec2": record_ec2_cassettes,
        "s3": record_s3_cassettes,
        "rds": record_rds_cassettes,
        "all": record_all,
    }

    try:
        func = scanner_map[args.scanner]
        asyncio.run(func(args.profile, args.region, args.prefix))
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. AWS credentials are configured for the profile")
        print("  2. You have permission to describe resources")
        print("  3. The region is valid")
        sys.exit(1)


if __name__ == "__main__":
    main()
