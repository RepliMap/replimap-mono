"""
Unified VPC Scanner with full resilience stack.

This scanner discovers VPC resources including:
- VPCs
- Subnets
- Route Tables
- Internet Gateways
- NAT Gateways
- VPC Endpoints

Uses UnifiedScannerBase for:
- Circuit breaker protection
- Rate limiting
- Retry with error classification
- Backpressure monitoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from replimap.core.models import ResourceNode, ResourceType
from replimap.scanners.unified_base import ScanResult, UnifiedScannerBase

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


class UnifiedVPCScanner(UnifiedScannerBase):
    """
    Production-grade VPC scanner with full resilience stack.

    Scans VPC resources in a region including VPCs, subnets,
    route tables, and gateways.
    """

    service_name: ClassVar[str] = "ec2"
    resource_types: ClassVar[list[str]] = [
        "aws_vpc",
        "aws_subnet",
        "aws_route_table",
        "aws_internet_gateway",
        "aws_nat_gateway",
        "aws_vpc_endpoint",
    ]

    async def _do_scan(self, graph: GraphEngine) -> ScanResult:
        """
        Scan all VPC resources in the region.

        Args:
            graph: GraphEngine to populate with discovered resources

        Returns:
            ScanResult with scan statistics
        """
        result = ScanResult(scanner_name=self.__class__.__name__)

        async with await self._get_client() as client:
            # Scan VPCs first (other resources depend on them)
            vpc_count = await self._scan_vpcs(client, graph, result)
            result.resources_found += vpc_count

            # Scan subnets
            subnet_count = await self._scan_subnets(client, graph, result)
            result.resources_found += subnet_count

            # Scan route tables
            rt_count = await self._scan_route_tables(client, graph, result)
            result.resources_found += rt_count

            # Scan internet gateways
            igw_count = await self._scan_internet_gateways(client, graph, result)
            result.resources_found += igw_count

            # Scan NAT gateways
            nat_count = await self._scan_nat_gateways(client, graph, result)
            result.resources_found += nat_count

            # Scan VPC endpoints
            endpoint_count = await self._scan_vpc_endpoints(client, graph, result)
            result.resources_found += endpoint_count

        logger.info(
            f"VPC scan complete: {result.resources_found} resources found, "
            f"{result.resources_failed} failed"
        )

        return result

    async def _scan_vpcs(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan VPCs."""
        count = 0

        try:
            vpcs = await self._paginate(
                client=client,
                method_name="describe_vpcs",
                result_key="Vpcs",
                operation_name="DescribeVpcs",
            )

            for vpc in vpcs:
                try:
                    vpc_id = vpc["VpcId"]
                    tags = self._extract_tags(vpc)
                    name = tags.get("Name", vpc_id)

                    node = ResourceNode(
                        id=vpc_id,
                        resource_type=ResourceType.VPC,
                        region=self.region,
                        config=vpc,
                        arn=self._make_arn("vpc", vpc_id),
                        tags=tags,
                        dependencies=[],
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    count += 1

                except Exception as e:
                    logger.warning(f"Failed to process VPC {vpc.get('VpcId')}: {e}")
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan VPCs: {e}")
            result.errors.append(f"VPC scan error: {e}")

        return count

    async def _scan_subnets(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan subnets."""
        count = 0

        try:
            subnets = await self._paginate(
                client=client,
                method_name="describe_subnets",
                result_key="Subnets",
                operation_name="DescribeSubnets",
            )

            for subnet in subnets:
                try:
                    subnet_id = subnet["SubnetId"]
                    vpc_id = subnet["VpcId"]
                    tags = self._extract_tags(subnet)
                    name = tags.get("Name", subnet_id)

                    node = ResourceNode(
                        id=subnet_id,
                        resource_type=ResourceType.SUBNET,
                        region=self.region,
                        config=subnet,
                        arn=self._make_arn("subnet", subnet_id),
                        tags=tags,
                        dependencies=[vpc_id],
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    graph.add_dependency(subnet_id, vpc_id, "belongs_to")
                    count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process subnet {subnet.get('SubnetId')}: {e}"
                    )
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan subnets: {e}")
            result.errors.append(f"Subnet scan error: {e}")

        return count

    async def _scan_route_tables(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan route tables."""
        count = 0

        try:
            route_tables = await self._paginate(
                client=client,
                method_name="describe_route_tables",
                result_key="RouteTables",
                operation_name="DescribeRouteTables",
            )

            for rt in route_tables:
                try:
                    rt_id = rt["RouteTableId"]
                    vpc_id = rt["VpcId"]
                    tags = self._extract_tags(rt)
                    name = tags.get("Name", rt_id)

                    node = ResourceNode(
                        id=rt_id,
                        resource_type=ResourceType.ROUTE_TABLE,
                        region=self.region,
                        config=rt,
                        arn=self._make_arn("route-table", rt_id),
                        tags=tags,
                        dependencies=[vpc_id],
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    graph.add_dependency(rt_id, vpc_id, "belongs_to")
                    count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process route table {rt.get('RouteTableId')}: {e}"
                    )
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan route tables: {e}")
            result.errors.append(f"Route table scan error: {e}")

        return count

    async def _scan_internet_gateways(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan internet gateways."""
        count = 0

        try:
            igws = await self._paginate(
                client=client,
                method_name="describe_internet_gateways",
                result_key="InternetGateways",
                operation_name="DescribeInternetGateways",
            )

            for igw in igws:
                try:
                    igw_id = igw["InternetGatewayId"]
                    tags = self._extract_tags(igw)
                    name = tags.get("Name", igw_id)

                    # Get attached VPC
                    attachments = igw.get("Attachments", [])
                    vpc_ids = [a["VpcId"] for a in attachments if a.get("VpcId")]

                    node = ResourceNode(
                        id=igw_id,
                        resource_type=ResourceType.INTERNET_GATEWAY,
                        region=self.region,
                        config=igw,
                        arn=self._make_arn("internet-gateway", igw_id),
                        tags=tags,
                        dependencies=vpc_ids,
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    for vpc_id in vpc_ids:
                        graph.add_dependency(igw_id, vpc_id, "attached_to")
                    count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process IGW {igw.get('InternetGatewayId')}: {e}"
                    )
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan internet gateways: {e}")
            result.errors.append(f"Internet gateway scan error: {e}")

        return count

    async def _scan_nat_gateways(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan NAT gateways."""
        count = 0

        try:
            nat_gateways = await self._paginate(
                client=client,
                method_name="describe_nat_gateways",
                result_key="NatGateways",
                operation_name="DescribeNatGateways",
            )

            for nat in nat_gateways:
                # Skip deleted NAT gateways
                if nat.get("State") == "deleted":
                    continue

                try:
                    nat_id = nat["NatGatewayId"]
                    subnet_id = nat.get("SubnetId")
                    vpc_id = nat.get("VpcId")
                    tags = self._extract_tags(nat)
                    name = tags.get("Name", nat_id)

                    dependencies = []
                    if subnet_id:
                        dependencies.append(subnet_id)
                    if vpc_id:
                        dependencies.append(vpc_id)

                    node = ResourceNode(
                        id=nat_id,
                        resource_type=ResourceType.NAT_GATEWAY,
                        region=self.region,
                        config=nat,
                        arn=self._make_arn("natgateway", nat_id),
                        tags=tags,
                        dependencies=dependencies,
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    if subnet_id:
                        graph.add_dependency(nat_id, subnet_id, "in_subnet")
                    if vpc_id:
                        graph.add_dependency(nat_id, vpc_id, "belongs_to")
                    count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process NAT gateway {nat.get('NatGatewayId')}: {e}"
                    )
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan NAT gateways: {e}")
            result.errors.append(f"NAT gateway scan error: {e}")

        return count

    async def _scan_vpc_endpoints(
        self,
        client: Any,
        graph: GraphEngine,
        result: ScanResult,
    ) -> int:
        """Scan VPC endpoints."""
        count = 0

        try:
            endpoints = await self._paginate(
                client=client,
                method_name="describe_vpc_endpoints",
                result_key="VpcEndpoints",
                operation_name="DescribeVpcEndpoints",
            )

            for endpoint in endpoints:
                # Skip deleted endpoints
                if endpoint.get("State") == "deleted":
                    continue

                try:
                    endpoint_id = endpoint["VpcEndpointId"]
                    vpc_id = endpoint.get("VpcId")
                    tags = self._extract_tags(endpoint)
                    name = tags.get("Name", endpoint_id)

                    dependencies = []
                    if vpc_id:
                        dependencies.append(vpc_id)

                    # Add subnet dependencies for interface endpoints
                    subnet_ids = endpoint.get("SubnetIds", [])
                    dependencies.extend(subnet_ids)

                    node = ResourceNode(
                        id=endpoint_id,
                        resource_type=ResourceType.VPC_ENDPOINT,
                        region=self.region,
                        config=endpoint,
                        arn=self._make_arn("vpc-endpoint", endpoint_id),
                        tags=tags,
                        dependencies=dependencies,
                        terraform_name=None,
                        original_name=name,
                        is_phantom=False,
                        phantom_reason=None,
                    )

                    graph.add_resource(node)
                    if vpc_id:
                        graph.add_dependency(endpoint_id, vpc_id, "belongs_to")
                    for subnet_id in subnet_ids:
                        graph.add_dependency(endpoint_id, subnet_id, "in_subnet")
                    count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process VPC endpoint "
                        f"{endpoint.get('VpcEndpointId')}: {e}"
                    )
                    result.resources_failed += 1

        except Exception as e:
            logger.error(f"Failed to scan VPC endpoints: {e}")
            result.errors.append(f"VPC endpoint scan error: {e}")

        return count
