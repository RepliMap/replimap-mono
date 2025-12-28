"""
Tests for P1-4, P1-5, P1-6 Pricing Engine modules.

Tests cover:
- General Pricing Engine (P1-4)
- Australia Local Pricing (P1-5)
- Data Transfer Cost Analysis (P1-6)
"""

from decimal import Decimal

from replimap.cost.au_pricing import (
    AU_GST_RATE,
    AUD_EXCHANGE_RATE,
    AUPricingConfig,
    AustraliaPricingEngine,
    RegionComparison,
    add_gst,
    calculate_gst,
    compare_au_regions,
)
from replimap.cost.models import CostCategory, PricingTier
from replimap.cost.pricing_engine import (
    BasePricingEngine,
    Currency,
    DefaultPricingEngine,
    PricePoint,
    PricingUnit,
    ResourceCost,
)
from replimap.cost.transfer_analyzer import (
    DataTransferAnalyzer,
    TrafficDirection,
    TransferCost,
    TransferPath,
    TransferPricingTiers,
    TransferReport,
    TransferType,
)

# =============================================================================
# P1-4: GENERAL PRICING ENGINE TESTS
# =============================================================================


class TestCurrency:
    """Test Currency enum."""

    def test_all_currencies_exist(self) -> None:
        """Test all expected currencies exist."""
        expected = ["USD", "AUD", "EUR", "GBP", "JPY", "SGD", "INR", "BRL", "CAD"]
        for curr in expected:
            assert hasattr(Currency, curr)


class TestPricingUnit:
    """Test PricingUnit enum."""

    def test_all_units_exist(self) -> None:
        """Test all expected units exist."""
        expected = [
            "HOURLY",
            "MONTHLY",
            "YEARLY",
            "PER_GB",
            "PER_GB_MONTH",
            "PER_REQUEST",
            "PER_MILLION_REQUESTS",
            "PER_GB_TRANSFERRED",
        ]
        for unit in expected:
            assert hasattr(PricingUnit, unit)


class TestPricePoint:
    """Test PricePoint dataclass."""

    def test_create_price_point(self) -> None:
        """Test creating a price point."""
        price = PricePoint(
            amount=Decimal("0.10"),
            currency=Currency.USD,
            unit=PricingUnit.HOURLY,
            region="us-east-1",
            service="ec2",
            resource_type="instance",
        )

        assert price.amount == Decimal("0.10")
        assert price.currency == Currency.USD
        assert price.unit == PricingUnit.HOURLY

    def test_to_monthly_from_hourly(self) -> None:
        """Test converting hourly to monthly."""
        price = PricePoint(
            amount=Decimal("0.10"),
            currency=Currency.USD,
            unit=PricingUnit.HOURLY,
            region="us-east-1",
            service="ec2",
            resource_type="instance",
        )

        monthly = price.to_monthly()
        assert monthly == Decimal("73.0")  # 0.10 * 730 hours

    def test_to_hourly_from_monthly(self) -> None:
        """Test converting monthly to hourly."""
        price = PricePoint(
            amount=Decimal("73.0"),
            currency=Currency.USD,
            unit=PricingUnit.MONTHLY,
            region="us-east-1",
            service="ec2",
            resource_type="instance",
        )

        hourly = price.to_hourly()
        assert hourly == Decimal("0.1")  # 73.0 / 730 hours

    def test_with_tax(self) -> None:
        """Test adding tax to price."""
        price = PricePoint(
            amount=Decimal("100"),
            currency=Currency.USD,
            unit=PricingUnit.MONTHLY,
            region="us-east-1",
            service="ec2",
            resource_type="instance",
            tax_rate=Decimal("0.10"),
        )

        with_tax = price.with_tax()
        assert with_tax == Decimal("110")

    def test_currency_conversion(self) -> None:
        """Test currency conversion."""
        price = PricePoint(
            amount=Decimal("100"),
            currency=Currency.USD,
            unit=PricingUnit.MONTHLY,
            region="us-east-1",
            service="ec2",
            resource_type="instance",
        )

        exchange_rates = {"USD": Decimal("1.0"), "AUD": Decimal("1.55")}
        aud_price = price.convert_currency(Currency.AUD, exchange_rates)

        assert aud_price.currency == Currency.AUD
        assert aud_price.amount == Decimal("155.000000")


class TestResourceCost:
    """Test ResourceCost dataclass."""

    def test_create_resource_cost(self) -> None:
        """Test creating a resource cost."""
        cost = ResourceCost(
            resource_id="i-1234",
            resource_type="aws_instance",
            resource_name="web-server",
            region="us-east-1",
            monthly_cost=Decimal("100"),
            currency=Currency.USD,
            category=CostCategory.COMPUTE,
        )

        assert cost.resource_id == "i-1234"
        assert cost.monthly_cost == Decimal("100")

    def test_to_dict(self) -> None:
        """Test resource cost serialization."""
        cost = ResourceCost(
            resource_id="i-1234",
            resource_type="aws_instance",
            resource_name="web-server",
            region="us-east-1",
            monthly_cost=Decimal("100"),
            currency=Currency.USD,
            category=CostCategory.COMPUTE,
            compute_cost=Decimal("100"),
        )

        data = cost.to_dict()

        assert data["resource_id"] == "i-1234"
        assert data["monthly_cost"] == 100.0
        assert data["breakdown"]["compute"] == 100.0


class TestDefaultPricingEngine:
    """Test DefaultPricingEngine."""

    def test_create_engine(self) -> None:
        """Test creating a pricing engine."""
        engine = DefaultPricingEngine("us-east-1")

        assert engine.region == "us-east-1"
        assert engine.currency == Currency.USD

    def test_get_ec2_price(self) -> None:
        """Test getting EC2 price."""
        engine = DefaultPricingEngine("us-east-1")
        price = engine.get_ec2_price("t3.medium")

        assert price.amount > 0
        assert price.unit == PricingUnit.HOURLY
        assert price.service == "ec2"

    def test_get_ec2_price_with_tier(self) -> None:
        """Test EC2 pricing with reserved tier."""
        engine = DefaultPricingEngine("us-east-1")

        on_demand = engine.get_ec2_price("t3.medium", PricingTier.ON_DEMAND)
        reserved = engine.get_ec2_price("t3.medium", PricingTier.RESERVED_1Y)

        assert reserved.amount < on_demand.amount

    def test_get_rds_price(self) -> None:
        """Test getting RDS price."""
        engine = DefaultPricingEngine("us-east-1")
        price = engine.get_rds_price("db.t3.medium")

        assert price.amount > 0
        assert price.service == "rds"

    def test_get_rds_price_multi_az(self) -> None:
        """Test RDS Multi-AZ pricing."""
        engine = DefaultPricingEngine("us-east-1")

        single = engine.get_rds_price("db.t3.medium", multi_az=False)
        multi = engine.get_rds_price("db.t3.medium", multi_az=True)

        assert multi.amount == single.amount * 2

    def test_get_storage_price(self) -> None:
        """Test getting storage price."""
        engine = DefaultPricingEngine("us-east-1")
        price = engine.get_storage_price("ebs_gp2")

        assert price.amount > 0
        assert price.unit == PricingUnit.PER_GB_MONTH

    def test_get_network_price(self) -> None:
        """Test getting network price."""
        engine = DefaultPricingEngine("us-east-1")
        price = engine.get_network_price("nat_gateway", "hourly")

        assert price.amount > 0

    def test_calculate_ec2_cost(self) -> None:
        """Test calculating EC2 resource cost."""
        engine = DefaultPricingEngine("us-east-1")
        cost = engine.calculate_resource_cost(
            "aws_instance",
            {"id": "i-1234", "name": "web-server", "instance_type": "t3.medium"},
        )

        assert cost.resource_id == "i-1234"
        assert cost.monthly_cost > 0
        assert cost.category == CostCategory.COMPUTE

    def test_region_multiplier(self) -> None:
        """Test regional price multiplier."""
        us_engine = DefaultPricingEngine("us-east-1")
        au_engine = DefaultPricingEngine("ap-southeast-2")

        us_price = us_engine.get_ec2_price("t3.medium")
        au_price = au_engine.get_ec2_price("t3.medium")

        # Australia should be more expensive
        assert au_price.amount > us_price.amount

    def test_for_region(self) -> None:
        """Test getting engine for region."""
        engine = BasePricingEngine.for_region("us-east-1")
        assert isinstance(engine, DefaultPricingEngine)


# =============================================================================
# P1-5: AUSTRALIA PRICING TESTS
# =============================================================================


class TestAUConstants:
    """Test Australian pricing constants."""

    def test_gst_rate(self) -> None:
        """Test GST rate is 10%."""
        assert AU_GST_RATE == Decimal("0.10")

    def test_exchange_rate(self) -> None:
        """Test AUD exchange rate."""
        assert AUD_EXCHANGE_RATE > Decimal("1.0")


class TestAUPricingConfig:
    """Test AUPricingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = AUPricingConfig()

        assert config.include_gst is True
        assert config.currency == Currency.AUD
        assert config.edp_discount_percent == Decimal("0")

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = AUPricingConfig(
            include_gst=False,
            edp_discount_percent=Decimal("10"),
        )

        assert config.include_gst is False
        assert config.edp_discount_percent == Decimal("10")


class TestAustraliaPricingEngine:
    """Test AustraliaPricingEngine."""

    def test_sydney_engine(self) -> None:
        """Test creating Sydney pricing engine."""
        engine = AustraliaPricingEngine("ap-southeast-2")

        assert engine.region == "ap-southeast-2"
        assert engine.currency == Currency.AUD
        assert engine.is_melbourne is False

    def test_melbourne_engine(self) -> None:
        """Test creating Melbourne pricing engine."""
        engine = AustraliaPricingEngine("ap-southeast-4")

        assert engine.region == "ap-southeast-4"
        assert engine.is_melbourne is True

    def test_get_ec2_price_aud(self) -> None:
        """Test getting EC2 price in AUD."""
        engine = AustraliaPricingEngine("ap-southeast-2")
        price = engine.get_ec2_price("t3.medium")

        assert price.currency == Currency.AUD
        assert price.amount > 0

    def test_melbourne_premium(self) -> None:
        """Test Melbourne is more expensive than Sydney."""
        sydney = AustraliaPricingEngine("ap-southeast-2")
        melbourne = AustraliaPricingEngine("ap-southeast-4")

        sydney_price = sydney.get_ec2_price("t3.medium")
        melbourne_price = melbourne.get_ec2_price("t3.medium")

        assert melbourne_price.amount > sydney_price.amount

    def test_gst_included(self) -> None:
        """Test GST is applied to resource cost."""
        config = AUPricingConfig(include_gst=True)
        engine = AustraliaPricingEngine("ap-southeast-2", config=config)

        cost = engine.calculate_resource_cost(
            "aws_instance",
            {"id": "i-1234", "instance_type": "t3.medium"},
        )

        assert cost.tax_rate == AU_GST_RATE
        assert cost.tax_amount > 0
        assert "GST" in " ".join(cost.notes)

    def test_gst_excluded(self) -> None:
        """Test GST can be excluded."""
        config = AUPricingConfig(include_gst=False)
        engine = AustraliaPricingEngine("ap-southeast-2", config=config)

        cost = engine.calculate_resource_cost(
            "aws_instance",
            {"id": "i-1234", "instance_type": "t3.medium"},
        )

        assert cost.tax_amount == 0

    def test_edp_discount(self) -> None:
        """Test EDP discount is applied."""
        no_edp = AUPricingConfig(edp_discount_percent=Decimal("0"))
        with_edp = AUPricingConfig(edp_discount_percent=Decimal("10"))

        engine_no_edp = AustraliaPricingEngine("ap-southeast-2", config=no_edp)
        engine_with_edp = AustraliaPricingEngine("ap-southeast-2", config=with_edp)

        price_no_edp = engine_no_edp.get_ec2_price("t3.medium")
        price_with_edp = engine_with_edp.get_ec2_price("t3.medium")

        assert price_with_edp.amount < price_no_edp.amount

    def test_for_region_returns_au_engine(self) -> None:
        """Test for_region returns AustraliaPricingEngine for AU regions."""
        engine = BasePricingEngine.for_region("ap-southeast-2")
        assert isinstance(engine, AustraliaPricingEngine)


class TestCompareAURegions:
    """Test AU region comparison."""

    def test_compare_regions(self) -> None:
        """Test comparing Sydney vs Melbourne."""
        comparison = compare_au_regions(
            "aws_instance",
            {"id": "i-1234", "instance_type": "t3.medium"},
        )

        assert isinstance(comparison, RegionComparison)
        assert comparison.sydney_cost.region == "ap-southeast-2"
        assert comparison.melbourne_cost.region == "ap-southeast-4"
        assert comparison.difference_aud >= 0  # Melbourne should be >= Sydney

    def test_comparison_to_dict(self) -> None:
        """Test comparison serialization."""
        comparison = compare_au_regions(
            "aws_instance",
            {"id": "i-1234", "instance_type": "t3.medium"},
        )

        data = comparison.to_dict()

        assert "sydney" in data
        assert "melbourne" in data
        assert "difference" in data
        assert "recommendation" in data


class TestGSTHelpers:
    """Test GST helper functions."""

    def test_add_gst(self) -> None:
        """Test adding GST to amount."""
        base = Decimal("100")
        with_gst = add_gst(base)

        assert with_gst == Decimal("110")

    def test_calculate_gst(self) -> None:
        """Test calculating GST from total."""
        total = Decimal("110")
        pre_gst, gst = calculate_gst(total)

        assert pre_gst == Decimal("100")
        assert gst == Decimal("10")


# =============================================================================
# P1-6: DATA TRANSFER ANALYSIS TESTS
# =============================================================================


class TestTransferType:
    """Test TransferType enum."""

    def test_all_types_exist(self) -> None:
        """Test all expected transfer types exist."""
        expected = [
            "INTERNET_EGRESS",
            "INTERNET_INGRESS",
            "CROSS_AZ",
            "CROSS_REGION",
            "VPC_PEERING",
            "TRANSIT_GATEWAY",
            "NAT_GATEWAY",
            "VPC_ENDPOINT",
            "DIRECT_CONNECT",
            "CLOUDFRONT",
        ]
        for t in expected:
            assert hasattr(TransferType, t)


class TestTransferPath:
    """Test TransferPath dataclass."""

    def test_create_path(self) -> None:
        """Test creating a transfer path."""
        path = TransferPath(
            source_id="i-1234",
            source_type="aws_instance",
            source_region="ap-southeast-2",
            source_az="ap-southeast-2a",
            destination_id="i-5678",
            destination_type="aws_instance",
            destination_region="ap-southeast-2",
            destination_az="ap-southeast-2b",
            transfer_type=TransferType.CROSS_AZ,
            direction=TrafficDirection.BIDIRECTIONAL,
            estimated_gb_month=Decimal("100"),
        )

        assert path.source_id == "i-1234"
        assert path.is_cross_az is True
        assert path.is_cross_region is False

    def test_cross_region_detection(self) -> None:
        """Test cross-region detection."""
        path = TransferPath(
            source_id="i-1234",
            source_type="aws_instance",
            source_region="ap-southeast-2",
            source_az="",
            destination_id="i-5678",
            destination_type="aws_instance",
            destination_region="us-east-1",
            destination_az="",
            transfer_type=TransferType.CROSS_REGION,
            direction=TrafficDirection.OUTBOUND,
        )

        assert path.is_cross_region is True
        assert path.is_cross_az is False


class TestTransferPricingTiers:
    """Test TransferPricingTiers."""

    def test_internet_egress_rate(self) -> None:
        """Test tiered internet egress pricing."""
        rate = TransferPricingTiers.get_internet_egress_rate(
            "us-east-1", Decimal("1000")
        )

        assert rate > 0

    def test_cross_az_rate(self) -> None:
        """Test cross-AZ rate."""
        rate = TransferPricingTiers.get_cross_az_rate("ap-southeast-2")

        assert rate == Decimal("0.01")

    def test_nat_rates(self) -> None:
        """Test NAT Gateway rates."""
        rates = TransferPricingTiers.get_nat_rates("ap-southeast-2")

        assert "hourly" in rates
        assert "per_gb" in rates
        assert rates["hourly"] > 0

    def test_cross_region_rate(self) -> None:
        """Test cross-region transfer rate."""
        rate = TransferPricingTiers.get_cross_region_rate(
            "ap-southeast-2", "ap-southeast-4"
        )

        assert rate > 0


class TestDataTransferAnalyzer:
    """Test DataTransferAnalyzer."""

    def test_create_analyzer(self) -> None:
        """Test creating analyzer."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        assert analyzer.region == "ap-southeast-2"
        assert analyzer.currency == Currency.USD

    def test_analyze_paths(self) -> None:
        """Test analyzing transfer paths."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        paths = [
            TransferPath(
                source_id="i-1234",
                source_type="aws_instance",
                source_region="ap-southeast-2",
                source_az="ap-southeast-2a",
                destination_id="i-5678",
                destination_type="aws_instance",
                destination_region="ap-southeast-2",
                destination_az="ap-southeast-2b",
                transfer_type=TransferType.CROSS_AZ,
                direction=TrafficDirection.BIDIRECTIONAL,
                estimated_gb_month=Decimal("100"),
            )
        ]

        report = analyzer.analyze_paths(paths)

        assert isinstance(report, TransferReport)
        assert len(report.costs) == 1
        assert report.total_monthly_cost > 0

    def test_analyze_nat_gateway(self) -> None:
        """Test NAT Gateway analysis."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        cost = analyzer.analyze_nat_gateway(
            {"id": "nat-1234", "region": "ap-southeast-2"},
            estimated_gb_month=Decimal("500"),
        )

        assert cost.monthly_cost > 0
        assert cost.hourly_cost > 0
        assert cost.data_transfer_cost > 0

    def test_nat_gateway_optimization(self) -> None:
        """Test NAT Gateway optimization suggestions."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        cost = analyzer.analyze_nat_gateway(
            {"id": "nat-1234", "region": "ap-southeast-2"},
            estimated_gb_month=Decimal("1000"),
        )

        # Should suggest VPC Endpoint optimization for high traffic
        assert cost.optimization_available is True
        assert cost.potential_savings > 0

    def test_analyze_internet_egress(self) -> None:
        """Test internet egress analysis."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        cost = analyzer.analyze_internet_egress(
            "i-1234",
            "aws_instance",
            "ap-southeast-2",
            Decimal("5000"),
        )

        assert cost.monthly_cost > 0
        assert cost.path.transfer_type == TransferType.INTERNET_EGRESS

    def test_cloudfront_optimization_suggestion(self) -> None:
        """Test CloudFront optimization for high egress."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        cost = analyzer.analyze_internet_egress(
            "i-1234",
            "aws_instance",
            "ap-southeast-2",
            Decimal("5000"),  # 5TB egress
        )

        # Should suggest CloudFront
        assert cost.optimization_available is True
        assert "CloudFront" in cost.optimization_suggestion

    def test_analyze_cross_region(self) -> None:
        """Test cross-region transfer analysis."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        cost = analyzer.analyze_cross_region(
            {"id": "i-1234", "type": "aws_instance", "region": "ap-southeast-2"},
            {"id": "i-5678", "type": "aws_instance", "region": "ap-southeast-4"},
            Decimal("100"),
        )

        assert cost.monthly_cost > 0
        assert cost.path.is_cross_region is True

    def test_detect_cross_az_traffic(self) -> None:
        """Test cross-AZ traffic detection."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        resources = [
            {
                "id": "i-1234",
                "type": "aws_instance",
                "region": "ap-southeast-2",
                "availability_zone": "ap-southeast-2a",
            },
            {
                "id": "i-5678",
                "type": "aws_instance",
                "region": "ap-southeast-2",
                "availability_zone": "ap-southeast-2b",
            },
        ]

        connections = [
            {
                "source_id": "i-1234",
                "destination_id": "i-5678",
                "estimated_gb_month": 100,
            },
        ]

        paths = analyzer.detect_cross_az_traffic(resources, connections)

        assert len(paths) == 1
        assert paths[0].is_cross_az is True

    def test_vpc_endpoint_recommendation(self) -> None:
        """Test VPC Endpoint recommendation."""
        analyzer = DataTransferAnalyzer("ap-southeast-2")

        recommendation = analyzer.get_vpc_endpoint_recommendation(
            nat_monthly_cost=Decimal("500"),
            service="s3",
            estimated_gb_month=Decimal("1000"),
        )

        assert "s3" in recommendation["service"]
        assert recommendation["monthly_savings"] > 0
        # S3 Gateway endpoint should be free
        assert recommendation["endpoint_cost"] == 0


class TestTransferReport:
    """Test TransferReport."""

    def test_add_cost(self) -> None:
        """Test adding cost to report."""
        report = TransferReport(region="ap-southeast-2", currency=Currency.USD)

        path = TransferPath(
            source_id="i-1234",
            source_type="aws_instance",
            source_region="ap-southeast-2",
            source_az="ap-southeast-2a",
            destination_id="i-5678",
            destination_type="aws_instance",
            destination_region="ap-southeast-2",
            destination_az="ap-southeast-2b",
            transfer_type=TransferType.CROSS_AZ,
            direction=TrafficDirection.BIDIRECTIONAL,
            estimated_gb_month=Decimal("100"),
        )

        cost = TransferCost(
            path=path,
            monthly_cost=Decimal("2.00"),
            currency=Currency.USD,
            rate_per_gb=Decimal("0.01"),
            data_transfer_cost=Decimal("2.00"),
        )

        report.add_cost(cost)

        assert report.total_monthly_cost == Decimal("2.00")
        assert TransferType.CROSS_AZ in report.cost_by_type

    def test_report_to_dict(self) -> None:
        """Test report serialization."""
        report = TransferReport(region="ap-southeast-2", currency=Currency.USD)

        data = report.to_dict()

        assert "region" in data
        assert "summary" in data
        assert "cost_by_type" in data
        assert "optimization" in data


# =============================================================================
# MODULE IMPORT TESTS
# =============================================================================


class TestModuleImports:
    """Test module imports from cost package."""

    def test_import_pricing_engine(self) -> None:
        """Test importing pricing engine classes."""
        from replimap.cost import (
            BasePricingEngine,
            DefaultPricingEngine,
        )

        assert BasePricingEngine is not None
        assert DefaultPricingEngine is not None

    def test_import_au_pricing(self) -> None:
        """Test importing AU pricing classes."""
        from replimap.cost import (
            AU_GST_RATE,
            AustraliaPricingEngine,
        )

        assert AustraliaPricingEngine is not None
        assert AU_GST_RATE == Decimal("0.10")

    def test_import_transfer_analyzer(self) -> None:
        """Test importing transfer analyzer classes."""
        from replimap.cost import (
            DataTransferAnalyzer,
            TransferType,
        )

        assert DataTransferAnalyzer is not None
        assert TransferType is not None
