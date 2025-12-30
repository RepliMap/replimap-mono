"""
Comprehensive tests for the Cost Estimator feature.
"""

import json
import tempfile
from pathlib import Path

import pytest

from replimap.cost import (
    COST_DISCLAIMER_FULL,
    COST_DISCLAIMER_SHORT,
    EBS_VOLUME_PRICING,
    EC2_INSTANCE_PRICING,
    ELASTICACHE_PRICING,
    EXCLUDED_FACTORS,
    RDS_INSTANCE_PRICING,
    CostBreakdown,
    CostCategory,
    CostConfidence,
    CostEstimate,
    CostEstimator,
    CostReporter,
    OptimizationRecommendation,
    PricingLookup,
    PricingTier,
    ResourceCost,
)


class TestCostModels:
    """Tests for cost data models."""

    def test_pricing_tier_enum(self):
        """Test PricingTier enum values."""
        assert PricingTier.ON_DEMAND.value == "ON_DEMAND"
        assert PricingTier.RESERVED_1Y.value == "RESERVED_1Y"
        assert PricingTier.RESERVED_3Y.value == "RESERVED_3Y"
        assert PricingTier.SPOT.value == "SPOT"
        assert PricingTier.SAVINGS_PLAN.value == "SAVINGS_PLAN"

    def test_cost_category_enum(self):
        """Test CostCategory enum values."""
        assert CostCategory.COMPUTE.value == "COMPUTE"
        assert CostCategory.DATABASE.value == "DATABASE"
        assert CostCategory.STORAGE.value == "STORAGE"
        assert CostCategory.NETWORK.value == "NETWORK"
        assert CostCategory.SECURITY.value == "SECURITY"
        assert CostCategory.MONITORING.value == "MONITORING"
        assert CostCategory.OTHER.value == "OTHER"

    def test_cost_confidence_enum(self):
        """Test CostConfidence enum values."""
        assert CostConfidence.HIGH.value == "HIGH"
        assert CostConfidence.MEDIUM.value == "MEDIUM"
        assert CostConfidence.LOW.value == "LOW"
        assert CostConfidence.UNKNOWN.value == "UNKNOWN"

    def test_resource_cost_creation(self):
        """Test ResourceCost dataclass creation."""
        cost = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="web-server",
            monthly_cost=100.50,
            hourly_cost=0.1375,
            annual_cost=1206.00,
            category=CostCategory.COMPUTE,
            pricing_tier=PricingTier.ON_DEMAND,
            compute_cost=95.00,
            storage_cost=5.50,
            instance_type="t3.medium",
            region="us-east-1",
            confidence=CostConfidence.HIGH,
        )

        assert cost.resource_id == "i-12345"
        assert cost.resource_type == "aws_instance"
        assert cost.monthly_cost == 100.50
        assert cost.category == CostCategory.COMPUTE
        assert cost.confidence == CostConfidence.HIGH

    def test_resource_cost_to_dict(self):
        """Test ResourceCost serialization."""
        cost = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="web-server",
            monthly_cost=100.50,
            hourly_cost=0.1375,
            annual_cost=1206.00,
            category=CostCategory.COMPUTE,
            instance_type="t3.medium",
            region="us-east-1",
            confidence=CostConfidence.HIGH,
            optimization_potential=40.0,
            optimization_tips=["Consider Reserved Instances"],
        )

        data = cost.to_dict()

        assert data["resource_id"] == "i-12345"
        assert data["monthly_cost"] == 100.50
        assert data["category"] == "COMPUTE"
        assert data["confidence"] == "HIGH"
        assert data["optimization_potential"] == 40.0

    def test_cost_breakdown_creation(self):
        """Test CostBreakdown dataclass creation."""
        cost1 = ResourceCost(
            resource_id="i-1",
            resource_type="aws_instance",
            resource_name="web1",
            monthly_cost=100,
            category=CostCategory.COMPUTE,
        )
        cost2 = ResourceCost(
            resource_id="i-2",
            resource_type="aws_instance",
            resource_name="web2",
            monthly_cost=100,
            category=CostCategory.COMPUTE,
        )

        breakdown = CostBreakdown(
            category=CostCategory.COMPUTE,
            resources=[cost1, cost2],
            monthly_total=200.0,
            percentage=50.0,
        )

        assert breakdown.category == CostCategory.COMPUTE
        assert len(breakdown.resources) == 2
        assert breakdown.monthly_total == 200.0
        assert breakdown.percentage == 50.0

    def test_cost_breakdown_to_dict(self):
        """Test CostBreakdown serialization."""
        cost = ResourceCost(
            resource_id="i-1",
            resource_type="aws_instance",
            resource_name="web",
            monthly_cost=100,
            category=CostCategory.COMPUTE,
        )

        breakdown = CostBreakdown(
            category=CostCategory.COMPUTE,
            resources=[cost],
            monthly_total=100.0,
            percentage=25.0,
        )

        data = breakdown.to_dict()

        assert data["category"] == "COMPUTE"
        assert data["resource_count"] == 1
        assert data["monthly_total"] == 100.0
        assert data["percentage"] == 25.0

    def test_optimization_recommendation_creation(self):
        """Test OptimizationRecommendation dataclass creation."""
        rec = OptimizationRecommendation(
            title="Reserved Instances",
            description="Convert on-demand to reserved for savings",
            potential_savings=500.00,
            effort="MEDIUM",
            affected_resources=["i-123", "i-456"],
            action_items=["Analyze usage", "Purchase reserved capacity"],
        )

        assert rec.title == "Reserved Instances"
        assert rec.potential_savings == 500.00
        assert rec.effort == "MEDIUM"
        assert len(rec.affected_resources) == 2

    def test_optimization_recommendation_to_dict(self):
        """Test OptimizationRecommendation serialization."""
        rec = OptimizationRecommendation(
            title="Migrate gp2 to gp3",
            description="Cheaper and better performance",
            potential_savings=50.00,
            effort="LOW",
        )

        data = rec.to_dict()

        assert data["title"] == "Migrate gp2 to gp3"
        assert data["potential_savings"] == 50.00
        assert data["effort"] == "LOW"

    def test_cost_estimate_creation(self):
        """Test CostEstimate dataclass creation."""
        estimate = CostEstimate(
            monthly_total=1500.00,
            annual_total=18000.00,
            daily_average=50.00,
            resource_count=10,
            estimated_resources=8,
            unestimated_resources=2,
            confidence=CostConfidence.MEDIUM,
        )

        assert estimate.monthly_total == 1500.00
        assert estimate.annual_total == 18000.00
        assert estimate.resource_count == 10
        assert estimate.confidence == CostConfidence.MEDIUM

    def test_cost_estimate_to_dict(self):
        """Test CostEstimate serialization."""
        estimate = CostEstimate(
            monthly_total=1500.00,
            annual_total=18000.00,
            daily_average=50.00,
            resource_count=10,
            estimated_resources=8,
            unestimated_resources=2,
            confidence=CostConfidence.MEDIUM,
            total_optimization_potential=300.00,
            optimization_percentage=20.0,
        )

        data = estimate.to_dict()

        # Updated structure with disclaimer
        assert data["summary"]["monthly_estimate"] == 1500.00
        assert data["summary"]["annual_estimate"] == 18000.00
        assert data["resources"]["total"] == 10
        assert data["optimization"]["potential_monthly_savings"] == 300.00
        assert "disclaimer" in data
        assert "not_included" in data


class TestPricingData:
    """Tests for pricing data constants."""

    def test_ec2_pricing_data_exists(self):
        """Test EC2 pricing data is populated."""
        assert len(EC2_INSTANCE_PRICING) > 0
        assert "t3.micro" in EC2_INSTANCE_PRICING
        assert "t3.medium" in EC2_INSTANCE_PRICING
        assert "m5.large" in EC2_INSTANCE_PRICING

    def test_ec2_pricing_reasonable(self):
        """Test EC2 pricing values are reasonable."""
        # t3.micro should be cheap
        assert EC2_INSTANCE_PRICING["t3.micro"] < 0.05

        # Larger instances should cost more
        assert EC2_INSTANCE_PRICING["m5.xlarge"] > EC2_INSTANCE_PRICING["m5.large"]

    def test_rds_pricing_data_exists(self):
        """Test RDS pricing data is populated."""
        assert len(RDS_INSTANCE_PRICING) > 0
        assert "db.t3.micro" in RDS_INSTANCE_PRICING
        assert "db.m5.large" in RDS_INSTANCE_PRICING

    def test_rds_pricing_reasonable(self):
        """Test RDS pricing values are reasonable."""
        # RDS typically costs more than EC2
        t3_micro_rds = RDS_INSTANCE_PRICING["db.t3.micro"]
        t3_micro_ec2 = EC2_INSTANCE_PRICING["t3.micro"]
        assert t3_micro_rds >= t3_micro_ec2

    def test_elasticache_pricing_exists(self):
        """Test ElastiCache pricing data is populated."""
        assert len(ELASTICACHE_PRICING) > 0
        assert "cache.t3.micro" in ELASTICACHE_PRICING

    def test_ebs_pricing_exists(self):
        """Test EBS pricing data is populated."""
        assert len(EBS_VOLUME_PRICING) > 0
        assert "gp2" in EBS_VOLUME_PRICING
        assert "gp3" in EBS_VOLUME_PRICING
        assert "io1" in EBS_VOLUME_PRICING

    def test_gp3_cheaper_than_gp2(self):
        """Test gp3 is cheaper than gp2."""
        assert EBS_VOLUME_PRICING["gp3"] < EBS_VOLUME_PRICING["gp2"]


class TestPricingLookup:
    """Tests for PricingLookup class."""

    def test_initialization(self):
        """Test pricing lookup initialization."""
        lookup = PricingLookup("us-east-1")
        assert lookup.region == "us-east-1"
        assert lookup.region_multiplier == 1.0

    def test_region_multiplier(self):
        """Test region multipliers are applied."""
        us_east = PricingLookup("us-east-1")
        eu_west = PricingLookup("eu-west-1")

        # EU should be more expensive
        assert eu_west.region_multiplier > us_east.region_multiplier

    def test_get_ec2_hourly_cost(self):
        """Test EC2 hourly cost lookup."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_ec2_hourly_cost("t3.medium")
        assert cost > 0
        assert cost == EC2_INSTANCE_PRICING["t3.medium"]

    def test_get_ec2_cost_with_reserved(self):
        """Test EC2 cost with reserved pricing."""
        lookup = PricingLookup("us-east-1")

        on_demand = lookup.get_ec2_hourly_cost("t3.medium", PricingTier.ON_DEMAND)
        reserved_1y = lookup.get_ec2_hourly_cost("t3.medium", PricingTier.RESERVED_1Y)
        reserved_3y = lookup.get_ec2_hourly_cost("t3.medium", PricingTier.RESERVED_3Y)

        # Reserved should be cheaper
        assert reserved_1y < on_demand
        assert reserved_3y < reserved_1y

    def test_get_ec2_cost_unknown_type(self):
        """Test EC2 cost estimation for unknown type."""
        lookup = PricingLookup("us-east-1")

        # Unknown instance type should still return estimate
        cost = lookup.get_ec2_hourly_cost("x99.unknown")
        assert cost > 0

    def test_get_rds_hourly_cost(self):
        """Test RDS hourly cost lookup."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_rds_hourly_cost("db.t3.medium")
        assert cost > 0

    def test_get_rds_multi_az_cost(self):
        """Test RDS Multi-AZ doubles cost."""
        lookup = PricingLookup("us-east-1")

        single_az = lookup.get_rds_hourly_cost("db.t3.medium", multi_az=False)
        multi_az = lookup.get_rds_hourly_cost("db.t3.medium", multi_az=True)

        assert multi_az == single_az * 2

    def test_get_rds_storage_cost(self):
        """Test RDS storage cost calculation."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_rds_storage_monthly_cost(100, "gp2")
        expected = 100 * EBS_VOLUME_PRICING["gp2"]
        assert cost == expected

    def test_get_elasticache_cost(self):
        """Test ElastiCache cost lookup."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_elasticache_hourly_cost("cache.t3.medium")
        assert cost > 0

    def test_get_elasticache_multiple_nodes(self):
        """Test ElastiCache cost with multiple nodes."""
        lookup = PricingLookup("us-east-1")

        single = lookup.get_elasticache_hourly_cost("cache.t3.medium", num_nodes=1)
        three = lookup.get_elasticache_hourly_cost("cache.t3.medium", num_nodes=3)

        assert three == single * 3

    def test_get_ebs_monthly_cost(self):
        """Test EBS volume cost calculation."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_ebs_monthly_cost(100, "gp2")
        expected = 100 * EBS_VOLUME_PRICING["gp2"]
        assert cost == expected

    def test_get_s3_monthly_cost(self):
        """Test S3 storage cost calculation."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_s3_monthly_cost(100.0, "STANDARD")
        assert cost > 0

    def test_get_nat_gateway_cost(self):
        """Test NAT Gateway cost calculation."""
        lookup = PricingLookup("us-east-1")

        cost = lookup.get_nat_gateway_monthly_cost(100.0)
        assert cost > 0
        # NAT Gateway has hourly + data costs
        assert cost > 30  # At least hourly cost

    def test_get_load_balancer_cost(self):
        """Test load balancer cost calculation."""
        lookup = PricingLookup("us-east-1")

        alb_cost = lookup.get_load_balancer_monthly_cost("alb")
        clb_cost = lookup.get_load_balancer_monthly_cost("clb")

        assert alb_cost > 0
        assert clb_cost > 0

    def test_get_resource_category(self):
        """Test resource category lookup."""
        lookup = PricingLookup("us-east-1")

        assert lookup.get_resource_category("aws_instance") == CostCategory.COMPUTE
        assert lookup.get_resource_category("aws_db_instance") == CostCategory.DATABASE
        assert lookup.get_resource_category("aws_s3_bucket") == CostCategory.STORAGE
        assert lookup.get_resource_category("aws_nat_gateway") == CostCategory.NETWORK
        assert (
            lookup.get_resource_category("aws_security_group") == CostCategory.SECURITY
        )
        assert lookup.get_resource_category("aws_unknown") == CostCategory.OTHER


class TestCostEstimator:
    """Tests for CostEstimator class."""

    def test_initialization(self):
        """Test estimator initialization."""
        estimator = CostEstimator("us-east-1")
        assert estimator.region == "us-east-1"
        assert isinstance(estimator.pricing, PricingLookup)

    def test_estimate_from_resources_empty(self):
        """Test estimating with no resources."""
        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources([])

        assert estimate.monthly_total == 0
        assert estimate.resource_count == 0

    def test_estimate_ec2_instance(self):
        """Test EC2 instance cost estimation."""
        resources = [
            {
                "id": "i-12345",
                "type": "aws_instance",
                "name": "web-server",
                "config": {"instance_type": "t3.medium"},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.COMPUTE
        assert estimate.resource_costs[0].instance_type == "t3.medium"

    def test_estimate_ec2_with_root_block_device_as_dict(self):
        """Test EC2 estimation when root_block_device is a dict (flattened by GraphEngine)."""
        resources = [
            {
                "id": "i-dict-rbd",
                "type": "aws_instance",
                "name": "web-server",
                "config": {
                    "instance_type": "t3.medium",
                    # Dict format - happens when GraphEngine flattens single-element lists
                    "root_block_device": {"volume_size": 50, "volume_type": "gp3"},
                },
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        cost = estimate.resource_costs[0]
        # Verify storage cost uses the dict values (50GB gp3)
        assert cost.storage_cost > 0
        # gp3 is $0.08/GB, so 50GB should be $4
        assert cost.storage_cost == pytest.approx(4.0, rel=0.1)

    def test_estimate_ec2_with_root_block_device_as_list(self):
        """Test EC2 estimation when root_block_device is a list (standard format)."""
        resources = [
            {
                "id": "i-list-rbd",
                "type": "aws_instance",
                "name": "web-server",
                "config": {
                    "instance_type": "t3.medium",
                    # List format - standard Terraform-style
                    "root_block_device": [{"volume_size": 100, "volume_type": "gp2"}],
                },
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        cost = estimate.resource_costs[0]
        # gp2 is $0.10/GB, so 100GB should be $10
        assert cost.storage_cost == pytest.approx(10.0, rel=0.1)

    def test_estimate_ec2_with_empty_root_block_device(self):
        """Test EC2 estimation with empty/missing root_block_device uses defaults."""
        resources = [
            {
                "id": "i-no-rbd",
                "type": "aws_instance",
                "name": "web-server",
                "config": {
                    "instance_type": "t3.medium",
                    # No root_block_device specified
                },
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        cost = estimate.resource_costs[0]
        # Default is 8GB gp2, so $0.80
        assert cost.storage_cost == pytest.approx(0.8, rel=0.1)

    def test_estimate_ec2_with_empty_list_root_block_device(self):
        """Test EC2 estimation with empty list root_block_device uses defaults."""
        resources = [
            {
                "id": "i-empty-list-rbd",
                "type": "aws_instance",
                "name": "web-server",
                "config": {
                    "instance_type": "t3.medium",
                    "root_block_device": [],  # Empty list
                },
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        cost = estimate.resource_costs[0]
        # Default is 8GB gp2, so $0.80
        assert cost.storage_cost == pytest.approx(0.8, rel=0.1)

    def test_estimate_rds_instance(self):
        """Test RDS instance cost estimation."""
        resources = [
            {
                "id": "db-12345",
                "type": "aws_db_instance",
                "name": "main-db",
                "config": {
                    "instance_class": "db.t3.medium",
                    "allocated_storage": 100,
                    "storage_type": "gp2",
                    "multi_az": False,
                },
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.DATABASE
        # Should have both compute and storage costs
        assert estimate.resource_costs[0].compute_cost > 0
        assert estimate.resource_costs[0].storage_cost > 0

    def test_estimate_rds_multi_az(self):
        """Test RDS Multi-AZ doubles compute cost."""
        estimator = CostEstimator("us-east-1")

        single_az = estimator.estimate_from_resources(
            [
                {
                    "id": "db-1",
                    "type": "aws_db_instance",
                    "name": "db",
                    "config": {"instance_class": "db.t3.medium", "multi_az": False},
                }
            ]
        )

        multi_az = estimator.estimate_from_resources(
            [
                {
                    "id": "db-2",
                    "type": "aws_db_instance",
                    "name": "db",
                    "config": {"instance_class": "db.t3.medium", "multi_az": True},
                }
            ]
        )

        # Multi-AZ should cost more (approximately double compute)
        assert multi_az.monthly_total > single_az.monthly_total

    def test_estimate_nat_gateway(self):
        """Test NAT Gateway cost estimation."""
        resources = [
            {
                "id": "nat-12345",
                "type": "aws_nat_gateway",
                "name": "main-nat",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert estimate.resource_costs[0].category == CostCategory.NETWORK

    def test_estimate_alb(self):
        """Test Application Load Balancer cost estimation."""
        resources = [
            {
                "id": "alb-12345",
                "type": "aws_lb",
                "name": "web-alb",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert estimate.resource_costs[0].category == CostCategory.NETWORK

    def test_estimate_ebs_volume(self):
        """Test EBS volume cost estimation."""
        resources = [
            {
                "id": "vol-12345",
                "type": "aws_ebs_volume",
                "name": "data-volume",
                "config": {"size": 500, "type": "gp2"},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert estimate.resource_costs[0].category == CostCategory.STORAGE
        # 500 GB * $0.10/GB = $50
        assert estimate.resource_costs[0].monthly_cost == pytest.approx(50.0, rel=0.1)

    def test_estimate_s3_bucket(self):
        """Test S3 bucket cost estimation."""
        resources = [
            {
                "id": "bucket-12345",
                "type": "aws_s3_bucket",
                "name": "data-bucket",
                "config": {"estimated_storage_gb": 1000},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert estimate.resource_costs[0].category == CostCategory.STORAGE
        assert (
            estimate.resource_costs[0].confidence == CostConfidence.LOW
        )  # Usage-based

    def test_estimate_free_resources(self):
        """Test that free resources have zero cost."""
        resources = [
            {
                "id": "vpc-12345",
                "type": "aws_vpc",
                "name": "main-vpc",
                "config": {},
            },
            {
                "id": "subnet-abc",
                "type": "aws_subnet",
                "name": "web-subnet",
                "config": {},
            },
            {
                "id": "igw-xyz",
                "type": "aws_internet_gateway",
                "name": "main-igw",
                "config": {},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Free resources should have zero cost
        for cost in estimate.resource_costs:
            assert cost.monthly_cost == 0

    def test_category_breakdown(self):
        """Test cost breakdown by category."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "web",
                "config": {"instance_type": "t3.medium"},
            },
            {
                "id": "db-1",
                "type": "aws_db_instance",
                "name": "db",
                "config": {"instance_class": "db.t3.medium"},
            },
            {"id": "nat-1", "type": "aws_nat_gateway", "name": "nat", "config": {}},
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        categories = {b.category for b in estimate.by_category}
        assert CostCategory.COMPUTE in categories
        assert CostCategory.DATABASE in categories
        assert CostCategory.NETWORK in categories

    def test_top_resources_sorted(self):
        """Test top resources are sorted by cost."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "small",
                "config": {"instance_type": "t3.nano"},
            },
            {
                "id": "i-2",
                "type": "aws_instance",
                "name": "large",
                "config": {"instance_type": "m5.4xlarge"},
            },
            {
                "id": "i-3",
                "type": "aws_instance",
                "name": "medium",
                "config": {"instance_type": "t3.medium"},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Top resources should be sorted by cost descending
        costs = [r.monthly_cost for r in estimate.top_resources]
        assert costs == sorted(costs, reverse=True)

    def test_optimization_tips_generated(self):
        """Test optimization tips are generated."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "expensive",
                "config": {"instance_type": "m5.4xlarge"},  # Expensive instance
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Expensive on-demand instance should have optimization tips
        cost = estimate.resource_costs[0]
        assert len(cost.optimization_tips) > 0

    def test_reserved_instance_recommendation(self):
        """Test reserved instance recommendations for high-cost resources."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "prod1",
                "config": {"instance_type": "m5.2xlarge"},
            },
            {
                "id": "i-2",
                "type": "aws_instance",
                "name": "prod2",
                "config": {"instance_type": "m5.2xlarge"},
            },
            {
                "id": "i-3",
                "type": "aws_instance",
                "name": "prod3",
                "config": {"instance_type": "m5.2xlarge"},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Should recommend reserved instances for expensive compute
        rec_titles = [r.title for r in estimate.recommendations]
        assert any("Reserved" in title for title in rec_titles)

    def test_annual_cost_calculated(self):
        """Test annual cost is 12x monthly."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "web",
                "config": {"instance_type": "t3.medium"},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.annual_total == pytest.approx(
            estimate.monthly_total * 12, rel=0.01
        )

    def test_daily_average_calculated(self):
        """Test daily average is monthly / 30."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "web",
                "config": {"instance_type": "t3.medium"},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.daily_average == pytest.approx(
            estimate.monthly_total / 30, rel=0.01
        )

    def test_estimate_documentdb(self):
        """Test DocumentDB cost estimation."""
        resources = [
            {
                "id": "docdb-12345",
                "type": "aws_docdb_cluster_instance",
                "name": "docdb-instance",
                "config": {"instance_class": "db.r5.large"},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.DATABASE
        # DocumentDB db.r5.large should be around $200+/month
        assert estimate.resource_costs[0].monthly_cost > 200

    def test_estimate_sqs(self):
        """Test SQS queue cost estimation."""
        resources = [
            {
                "id": "queue-12345",
                "type": "aws_sqs_queue",
                "name": "my-queue",
                "config": {"fifo_queue": False},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total >= 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.MONITORING

    def test_estimate_sns(self):
        """Test SNS topic cost estimation."""
        resources = [
            {
                "id": "topic-12345",
                "type": "aws_sns_topic",
                "name": "my-topic",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total >= 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.MONITORING

    def test_estimate_route53(self):
        """Test Route 53 hosted zone cost estimation."""
        resources = [
            {
                "id": "zone-12345",
                "type": "aws_route53_zone",
                "name": "example.com",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # Hosted zone is at least $0.50/month
        assert estimate.resource_costs[0].monthly_cost >= 0.50

    def test_estimate_kms(self):
        """Test KMS key cost estimation."""
        resources = [
            {
                "id": "key-12345",
                "type": "aws_kms_key",
                "name": "my-key",
                "config": {"customer_master_key_spec": "SYMMETRIC_DEFAULT"},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # Customer managed key is $1/month
        assert estimate.resource_costs[0].monthly_cost >= 1.0

    def test_estimate_secrets_manager(self):
        """Test Secrets Manager cost estimation."""
        resources = [
            {
                "id": "secret-12345",
                "type": "aws_secretsmanager_secret",
                "name": "my-secret",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # Secret is $0.40/month
        assert estimate.resource_costs[0].monthly_cost >= 0.40

    def test_estimate_ecr(self):
        """Test ECR repository cost estimation."""
        resources = [
            {
                "id": "repo-12345",
                "type": "aws_ecr_repository",
                "name": "my-repo",
                "config": {"estimated_storage_gb": 5.0},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # 5GB storage at $0.10/GB = $0.50
        assert estimate.resource_costs[0].monthly_cost >= 0.50

    def test_estimate_cloudfront(self):
        """Test CloudFront distribution cost estimation."""
        resources = [
            {
                "id": "dist-12345",
                "type": "aws_cloudfront_distribution",
                "name": "my-cdn",
                "config": {"estimated_transfer_gb": 100.0},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # 100GB transfer at ~$0.085/GB = ~$8.50
        assert estimate.resource_costs[0].monthly_cost > 5.0

    def test_estimate_guardduty(self):
        """Test GuardDuty detector cost estimation."""
        resources = [
            {
                "id": "detector-12345",
                "type": "aws_guardduty_detector",
                "name": "main-detector",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        assert estimate.resource_costs[0].category == CostCategory.SECURITY

    def test_estimate_cloudwatch_alarm(self):
        """Test CloudWatch alarm cost estimation."""
        resources = [
            {
                "id": "alarm-12345",
                "type": "aws_cloudwatch_metric_alarm",
                "name": "cpu-alarm",
                "config": {"period": 60},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # Standard alarm is $0.10/month
        assert estimate.resource_costs[0].monthly_cost == pytest.approx(0.10, rel=0.01)

    def test_estimate_cloudwatch_dashboard(self):
        """Test CloudWatch dashboard cost estimation."""
        resources = [
            {
                "id": "dashboard-12345",
                "type": "aws_cloudwatch_dashboard",
                "name": "my-dashboard",
                "config": {},
                "region": "us-east-1",
            }
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.monthly_total > 0
        assert len(estimate.resource_costs) == 1
        # Dashboard is $3/month
        assert estimate.resource_costs[0].monthly_cost == pytest.approx(3.0, rel=0.01)


class TestCostReporter:
    """Tests for CostReporter output."""

    def _create_sample_estimate(self) -> CostEstimate:
        """Create a sample estimate for testing."""
        cost1 = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="web-server",
            monthly_cost=150.00,
            hourly_cost=0.205,
            annual_cost=1800.00,
            category=CostCategory.COMPUTE,
            instance_type="t3.large",
            region="us-east-1",
            confidence=CostConfidence.HIGH,
            optimization_potential=60.0,
            optimization_tips=["Consider Reserved Instances"],
        )

        cost2 = ResourceCost(
            resource_id="db-67890",
            resource_type="aws_db_instance",
            resource_name="main-db",
            monthly_cost=200.00,
            hourly_cost=0.274,
            annual_cost=2400.00,
            category=CostCategory.DATABASE,
            instance_type="db.t3.large",
            region="us-east-1",
            confidence=CostConfidence.HIGH,
            compute_cost=180.00,
            storage_cost=20.00,
        )

        breakdown_compute = CostBreakdown(
            category=CostCategory.COMPUTE,
            resources=[cost1],
            monthly_total=150.00,
            percentage=42.9,
        )

        breakdown_db = CostBreakdown(
            category=CostCategory.DATABASE,
            resources=[cost2],
            monthly_total=200.00,
            percentage=57.1,
        )

        recommendation = OptimizationRecommendation(
            title="Reserved Instances",
            description="Convert on-demand to reserved for savings",
            potential_savings=100.00,
            effort="MEDIUM",
            affected_resources=["i-12345"],
            action_items=["Analyze usage patterns", "Purchase reserved capacity"],
        )

        return CostEstimate(
            monthly_total=350.00,
            annual_total=4200.00,
            daily_average=11.67,
            resource_costs=[cost1, cost2],
            by_category=[breakdown_db, breakdown_compute],
            by_region={"us-east-1": 350.00},
            top_resources=[cost2, cost1],
            total_optimization_potential=100.00,
            optimization_percentage=28.6,
            recommendations=[recommendation],
            resource_count=2,
            estimated_resources=2,
            unestimated_resources=0,
            confidence=CostConfidence.HIGH,
        )

    def test_reporter_initialization(self):
        """Test reporter initialization."""
        reporter = CostReporter()
        assert reporter is not None

    def test_to_console(self, capsys):
        """Test console output."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        # Should not raise
        reporter.to_console(estimate)

    def test_to_table(self, capsys):
        """Test table output."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        reporter.to_table(estimate)

    def test_to_json(self):
        """Test JSON export."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost-estimate.json"
            reporter.to_json(estimate, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            # Updated structure with disclaimer
            assert data["summary"]["monthly_estimate"] == 350.00
            assert data["resources"]["total"] == 2
            assert len(data["resource_costs"]) == 2
            assert len(data["by_category"]) == 2
            assert "_disclaimer" in data

    def test_to_html(self):
        """Test HTML export."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost-estimate.html"
            reporter.to_html(estimate, output_path)

            assert output_path.exists()

            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "$350" in content
            # Uses ECharts for treemap visualization
            assert "echarts" in content.lower()

    def test_to_csv(self):
        """Test CSV export."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost-estimate.csv"
            reporter.to_csv(estimate, output_path)

            assert output_path.exists()

            content = output_path.read_text()
            lines = content.strip().split("\n")

            # Disclaimer header (5 lines) + column header (1 line) + 2 resources
            assert len(lines) == 8
            assert lines[0].startswith("# DISCLAIMER:")
            assert "resource_id" in lines[5]  # Column header
            assert "i-12345" in content

    def test_empty_estimate(self):
        """Test handling of empty estimate."""
        reporter = CostReporter()
        estimate = CostEstimate(
            monthly_total=0,
            annual_total=0,
            daily_average=0,
            resource_count=0,
            confidence=CostConfidence.UNKNOWN,
        )

        # Should not raise
        reporter.to_console(estimate)

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "empty.json"
            reporter.to_json(estimate, json_path)
            assert json_path.exists()


class TestCostIntegration:
    """Integration tests for cost estimator feature."""

    def test_full_workflow(self):
        """Test complete workflow from resources to report."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "web-1",
                "config": {"instance_type": "t3.medium"},
            },
            {
                "id": "i-2",
                "type": "aws_instance",
                "name": "web-2",
                "config": {"instance_type": "t3.medium"},
            },
            {
                "id": "db-1",
                "type": "aws_db_instance",
                "name": "main-db",
                "config": {"instance_class": "db.r5.large", "allocated_storage": 100},
            },
            {
                "id": "nat-1",
                "type": "aws_nat_gateway",
                "name": "main-nat",
                "config": {},
            },
            {"id": "alb-1", "type": "aws_lb", "name": "web-alb", "config": {}},
            {
                "id": "vol-1",
                "type": "aws_ebs_volume",
                "name": "data",
                "config": {"size": 500, "type": "gp2"},
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Verify estimate
        assert estimate.monthly_total > 0
        assert estimate.resource_count == 6
        assert len(estimate.by_category) >= 3  # COMPUTE, DATABASE, NETWORK, STORAGE

        # Export to all formats
        reporter = CostReporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "cost.json"
            html_path = Path(tmpdir) / "cost.html"
            csv_path = Path(tmpdir) / "cost.csv"

            reporter.to_json(estimate, json_path)
            reporter.to_html(estimate, html_path)
            reporter.to_csv(estimate, csv_path)

            assert json_path.exists()
            assert html_path.exists()
            assert csv_path.exists()

    def test_large_infrastructure(self):
        """Test with larger infrastructure."""
        resources = []

        # 20 EC2 instances
        for i in range(20):
            resources.append(
                {
                    "id": f"i-{i:05d}",
                    "type": "aws_instance",
                    "name": f"server-{i}",
                    "config": {"instance_type": "t3.medium"},
                }
            )

        # 5 RDS instances
        for i in range(5):
            resources.append(
                {
                    "id": f"db-{i:05d}",
                    "type": "aws_db_instance",
                    "name": f"db-{i}",
                    "config": {"instance_class": "db.t3.medium"},
                }
            )

        # 3 NAT Gateways
        for i in range(3):
            resources.append(
                {
                    "id": f"nat-{i:05d}",
                    "type": "aws_nat_gateway",
                    "name": f"nat-{i}",
                    "config": {},
                }
            )

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        assert estimate.resource_count == 28
        assert estimate.monthly_total > 500  # Should be substantial

        # Check category breakdown
        compute_cost = sum(
            b.monthly_total
            for b in estimate.by_category
            if b.category == CostCategory.COMPUTE
        )
        db_cost = sum(
            b.monthly_total
            for b in estimate.by_category
            if b.category == CostCategory.DATABASE
        )
        network_cost = sum(
            b.monthly_total
            for b in estimate.by_category
            if b.category == CostCategory.NETWORK
        )

        assert compute_cost > 0
        assert db_cost > 0
        assert network_cost > 0

    def test_multi_region(self):
        """Test resources across multiple regions."""
        resources = [
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "us-web",
                "config": {"instance_type": "t3.medium"},
                "region": "us-east-1",
            },
            {
                "id": "i-2",
                "type": "aws_instance",
                "name": "eu-web",
                "config": {"instance_type": "t3.medium"},
                "region": "eu-west-1",
            },
            {
                "id": "i-3",
                "type": "aws_instance",
                "name": "ap-web",
                "config": {"instance_type": "t3.medium"},
                "region": "ap-northeast-1",
            },
        ]

        estimator = CostEstimator("us-east-1")
        estimate = estimator.estimate_from_resources(resources)

        # Different regions should have different costs
        assert len(estimate.by_region) >= 1


# =============================================================================
# DISCLAIMER TESTS
# =============================================================================


class TestCostDisclaimers:
    """Tests for cost estimate disclaimers and accuracy information."""

    def test_disclaimer_constants_exist(self):
        """Test that disclaimer constants are defined."""
        assert COST_DISCLAIMER_SHORT
        assert COST_DISCLAIMER_FULL
        assert EXCLUDED_FACTORS

    def test_disclaimer_short_contains_warning(self):
        """Test short disclaimer contains warning text."""
        assert "ESTIMATE" in COST_DISCLAIMER_SHORT.upper()
        assert "may vary" in COST_DISCLAIMER_SHORT.lower()

    def test_disclaimer_full_contains_included_excluded(self):
        """Test full disclaimer lists what's included and excluded."""
        assert "INCLUDED" in COST_DISCLAIMER_FULL
        assert "NOT INCLUDED" in COST_DISCLAIMER_FULL
        assert "Data transfer" in COST_DISCLAIMER_FULL

    def test_excluded_factors_list(self):
        """Test excluded factors list is populated."""
        assert len(EXCLUDED_FACTORS) > 5
        assert "Data transfer" in EXCLUDED_FACTORS[0]
        assert any("Reserved" in f for f in EXCLUDED_FACTORS)

    def test_confidence_accuracy_range(self):
        """Test confidence levels have accuracy ranges."""
        assert CostConfidence.HIGH.accuracy_range == "±10%"
        assert CostConfidence.MEDIUM.accuracy_range == "±20%"
        assert CostConfidence.LOW.accuracy_range == "±40%"
        assert CostConfidence.UNKNOWN.accuracy_range == "N/A"

    def test_confidence_multiplier(self):
        """Test confidence levels have multipliers."""
        assert CostConfidence.HIGH.multiplier == 0.10
        assert CostConfidence.MEDIUM.multiplier == 0.20
        assert CostConfidence.LOW.multiplier == 0.40
        assert CostConfidence.UNKNOWN.multiplier == 0.50

    def test_confidence_description(self):
        """Test confidence levels have descriptions."""
        assert "on-demand pricing" in CostConfidence.HIGH.description.lower()
        assert "assumptions" in CostConfidence.MEDIUM.description.lower()
        assert "rough" in CostConfidence.LOW.description.lower()

    def test_resource_cost_accuracy_range(self):
        """Test ResourceCost has accuracy_range property."""
        cost = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="test",
            monthly_cost=100.0,
            confidence=CostConfidence.HIGH,
        )
        assert cost.accuracy_range == "±10%"

        cost_low = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="test",
            monthly_cost=100.0,
            confidence=CostConfidence.LOW,
        )
        assert cost_low.accuracy_range == "±40%"

    def test_resource_cost_to_dict_includes_accuracy(self):
        """Test ResourceCost.to_dict includes accuracy_range."""
        cost = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="test",
            monthly_cost=100.0,
            confidence=CostConfidence.MEDIUM,
        )

        data = cost.to_dict()
        assert "accuracy_range" in data
        assert data["accuracy_range"] == "±20%"

    def test_estimate_range_calculation(self):
        """Test CostEstimate calculates range based on confidence."""
        estimate = CostEstimate(
            monthly_total=1000.0,
            confidence=CostConfidence.MEDIUM,  # ±20%
        )

        assert estimate.estimated_range_low == 800.0  # 1000 * 0.8
        assert estimate.estimated_range_high == 1200.0  # 1000 * 1.2
        assert estimate.accuracy_range == "±20%"

    def test_estimate_range_high_confidence(self):
        """Test range calculation with HIGH confidence."""
        estimate = CostEstimate(
            monthly_total=1000.0,
            confidence=CostConfidence.HIGH,  # ±10%
        )

        assert estimate.estimated_range_low == 900.0
        assert estimate.estimated_range_high == 1100.0

    def test_estimate_range_low_confidence(self):
        """Test range calculation with LOW confidence."""
        estimate = CostEstimate(
            monthly_total=1000.0,
            confidence=CostConfidence.LOW,  # ±40%
        )

        assert estimate.estimated_range_low == 600.0
        assert estimate.estimated_range_high == 1400.0

    def test_estimate_has_excluded_factors(self):
        """Test CostEstimate has excluded_factors by default."""
        estimate = CostEstimate(monthly_total=100.0)
        assert len(estimate.excluded_factors) > 0
        assert estimate.excluded_factors == EXCLUDED_FACTORS

    def test_estimate_to_dict_includes_disclaimer(self):
        """Test CostEstimate.to_dict includes disclaimer."""
        estimate = CostEstimate(
            monthly_total=1000.0,
            annual_total=12000.0,
            confidence=CostConfidence.MEDIUM,
        )

        data = estimate.to_dict()

        assert "disclaimer" in data
        assert data["disclaimer"] == COST_DISCLAIMER_SHORT
        assert "not_included" in data
        assert len(data["not_included"]) > 0
        assert "_note" in data

    def test_estimate_to_dict_includes_range(self):
        """Test CostEstimate.to_dict includes range information."""
        estimate = CostEstimate(
            monthly_total=1000.0,
            confidence=CostConfidence.MEDIUM,
        )

        data = estimate.to_dict()

        assert "summary" in data
        assert "range_low" in data["summary"]
        assert "range_high" in data["summary"]
        assert "accuracy" in data["summary"]
        assert data["summary"]["range_low"] == 800.0
        assert data["summary"]["range_high"] == 1200.0
        assert data["summary"]["accuracy"] == "±20%"


class TestCostReporterDisclaimers:
    """Tests for disclaimer output in CostReporter."""

    def _create_sample_estimate(self) -> CostEstimate:
        """Create a sample estimate for testing."""
        cost = ResourceCost(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="web-server",
            monthly_cost=150.00,
            category=CostCategory.COMPUTE,
            confidence=CostConfidence.HIGH,
        )

        breakdown = CostBreakdown(
            category=CostCategory.COMPUTE,
            resources=[cost],
            monthly_total=150.00,
            percentage=100.0,
        )

        return CostEstimate(
            monthly_total=150.00,
            annual_total=1800.00,
            daily_average=5.00,
            resource_costs=[cost],
            by_category=[breakdown],
            top_resources=[cost],
            resource_count=1,
            estimated_resources=1,
            confidence=CostConfidence.MEDIUM,
        )

    def test_json_includes_full_disclaimer(self):
        """Test JSON export includes full disclaimer."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.json"
            reporter.to_json(estimate, output_path)

            content = output_path.read_text()
            data = json.loads(content)

            assert "_disclaimer" in data
            assert "COST ESTIMATE DISCLAIMER" in data["_disclaimer"]
            assert "_generated_by" in data
            assert "_accuracy_note" in data

    def test_csv_includes_disclaimer_header(self):
        """Test CSV export includes disclaimer in header."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.csv"
            reporter.to_csv(estimate, output_path)

            content = output_path.read_text()
            lines = content.split("\n")

            # First lines should be comments with disclaimer
            assert lines[0].startswith("# DISCLAIMER:")
            assert "ESTIMATE" in lines[0].upper()
            assert "accuracy_range" in content

    def test_markdown_includes_disclaimer(self):
        """Test Markdown export includes disclaimer."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.md"
            reporter.to_markdown(estimate, output_path)

            content = output_path.read_text()

            assert "DISCLAIMER" in content
            assert "NOT Included" in content
            assert "AWS Cost Explorer" in content
            assert "AWS Pricing Calculator" in content
            assert "estimate only" in content.lower()

    def test_html_includes_disclaimer_banner(self):
        """Test HTML export includes disclaimer banner."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.html"
            reporter.to_html(estimate, output_path)

            content = output_path.read_text()

            assert "disclaimer-banner" in content
            assert "ESTIMATE ONLY" in content
            assert "NOT Included" in content
            assert "AWS Cost Explorer" in content

    def test_html_includes_range(self):
        """Test HTML export includes estimate range."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.html"
            reporter.to_html(estimate, output_path)

            content = output_path.read_text()

            # Should show range values
            assert str(int(estimate.estimated_range_low)) in content
            assert str(int(estimate.estimated_range_high)) in content

    def test_markdown_includes_range(self):
        """Test Markdown export includes estimate range."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "cost.md"
            reporter.to_markdown(estimate, output_path)

            content = output_path.read_text()

            assert "Estimated Range" in content
            assert estimate.accuracy_range in content

    def test_excluded_factors_in_all_formats(self):
        """Test excluded factors appear in all export formats."""
        reporter = CostReporter()
        estimate = self._create_sample_estimate()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "cost.json"
            md_path = Path(tmpdir) / "cost.md"
            html_path = Path(tmpdir) / "cost.html"

            reporter.to_json(estimate, json_path)
            reporter.to_markdown(estimate, md_path)
            reporter.to_html(estimate, html_path)

            json_content = json_path.read_text()
            md_content = md_path.read_text()
            html_content = html_path.read_text()

            # Check a common excluded factor appears in all
            assert "Data transfer" in json_content
            assert "Data transfer" in md_content
            assert "Data transfer" in html_content
