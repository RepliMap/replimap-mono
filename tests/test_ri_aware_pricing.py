"""
Tests for P3-4: RI/Savings Plan Aware Pricing.

Tests verify:
1. ReservedInstance and SavingsPlanCommitment models
2. RIAwarePricingEngine reservation-aware pricing
3. Right-sizing recommendation generation
4. Waste detection for underutilized reservations
5. Utilization level classification
"""

from datetime import datetime, timedelta
from decimal import Decimal

from replimap.cost.pricing_engine import Currency
from replimap.cost.ri_aware import (
    ReservationCoverage,
    ReservationState,
    ReservationType,
    ReservationWaste,
    ReservedInstance,
    RIAwareAnalysis,
    RIAwarePricingEngine,
    RightSizingAction,
    RightSizingRecommendation,
    SavingsPlanCommitment,
    UtilizationLevel,
    get_utilization_level,
)


class TestReservedInstance:
    """Test ReservedInstance model."""

    def test_create_reserved_instance(self):
        """Test creating a reserved instance."""
        ri = ReservedInstance(
            reservation_id="ri-12345",
            instance_type="m5.large",
            instance_count=2,
            availability_zone="us-east-1a",
            region="us-east-1",
            scope="Availability Zone",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now() - timedelta(days=100),
            end_date=datetime.now() + timedelta(days=265),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.096"),
        )

        assert ri.reservation_id == "ri-12345"
        assert ri.instance_type == "m5.large"
        assert ri.is_active

    def test_days_remaining(self):
        """Test days remaining calculation."""
        ri = ReservedInstance(
            reservation_id="ri-12345",
            instance_type="m5.large",
            instance_count=1,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now() - timedelta(days=300),
            end_date=datetime.now() + timedelta(days=65),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.096"),
        )

        assert ri.days_remaining > 0
        assert ri.days_remaining <= 66  # Allow some slack

    def test_is_expiring_soon(self):
        """Test expiration detection."""
        # Expiring soon
        expiring_ri = ReservedInstance(
            reservation_id="ri-expiring",
            instance_type="m5.large",
            instance_count=1,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now() - timedelta(days=350),
            end_date=datetime.now() + timedelta(days=15),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.096"),
        )

        assert expiring_ri.is_expiring_soon

        # Not expiring soon
        healthy_ri = ReservedInstance(
            reservation_id="ri-healthy",
            instance_type="m5.large",
            instance_count=1,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now() - timedelta(days=100),
            end_date=datetime.now() + timedelta(days=265),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.096"),
        )

        assert not healthy_ri.is_expiring_soon

    def test_to_dict(self):
        """Test serialization."""
        ri = ReservedInstance(
            reservation_id="ri-12345",
            instance_type="m5.large",
            instance_count=2,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="All Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now() - timedelta(days=100),
            end_date=datetime.now() + timedelta(days=265),
            fixed_price=Decimal("1000"),
            usage_price=Decimal("0"),
            utilization_percentage=95.5,
        )

        data = ri.to_dict()
        assert data["reservation_id"] == "ri-12345"
        assert data["instance_type"] == "m5.large"
        assert data["utilization"]["percentage"] == 95.5


class TestSavingsPlanCommitment:
    """Test SavingsPlanCommitment model."""

    def test_create_savings_plan(self):
        """Test creating a savings plan."""
        sp = SavingsPlanCommitment(
            savings_plan_id="sp-12345",
            savings_plan_arn="arn:aws:savingsplans::123456789012:savingsplan/sp-12345",
            savings_plan_type="Compute",
            payment_option="No Upfront",
            term_duration="1yr",
            state="active",
            region=None,
            start_time=datetime.now() - timedelta(days=100),
            end_time=datetime.now() + timedelta(days=265),
            commitment=Decimal("10.00"),
        )

        assert sp.savings_plan_id == "sp-12345"
        assert sp.savings_plan_type == "Compute"
        assert sp.is_active

    def test_monthly_commitment(self):
        """Test monthly commitment calculation."""
        sp = SavingsPlanCommitment(
            savings_plan_id="sp-12345",
            savings_plan_arn="arn:aws:savingsplans::123456789012:savingsplan/sp-12345",
            savings_plan_type="Compute",
            payment_option="No Upfront",
            term_duration="1yr",
            state="active",
            region=None,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=365),
            commitment=Decimal("10.00"),  # $10/hour
        )

        # Monthly = hourly * 730
        assert sp.monthly_commitment == Decimal("7300.00")

    def test_to_dict(self):
        """Test serialization."""
        sp = SavingsPlanCommitment(
            savings_plan_id="sp-12345",
            savings_plan_arn="arn:aws:savingsplans::123456789012:savingsplan/sp-12345",
            savings_plan_type="Compute",
            payment_option="No Upfront",
            term_duration="1yr",
            state="active",
            region=None,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(days=365),
            commitment=Decimal("10.00"),
            utilization_percentage=80.0,
        )

        data = sp.to_dict()
        assert data["savings_plan_id"] == "sp-12345"
        assert data["savings_plan_type"] == "Compute"
        assert data["utilization"]["percentage"] == 80.0


class TestReservationCoverage:
    """Test ReservationCoverage model."""

    def test_coverage_to_dict(self):
        """Test coverage serialization."""
        coverage = ReservationCoverage(
            total_on_demand_cost=Decimal("10000"),
            covered_cost=Decimal("7000"),
            coverage_percentage=70.0,
            ri_coverage_percentage=40.0,
            sp_coverage_percentage=30.0,
            ec2_coverage=75.0,
            rds_coverage=65.0,
        )

        data = coverage.to_dict()
        assert data["coverage_percentage"] == 70.0
        assert data["breakdown"]["ri_coverage"] == 40.0
        assert data["by_service"]["ec2"] == 75.0


class TestRightSizingRecommendation:
    """Test RightSizingRecommendation model."""

    def test_create_recommendation(self):
        """Test creating a right-sizing recommendation."""
        rec = RightSizingRecommendation(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="my-instance",
            region="us-east-1",
            current_instance_type="m5.xlarge",
            current_monthly_cost=Decimal("200"),
            action=RightSizingAction.DOWNSIZE,
            recommended_instance_type="m5.large",
            recommended_monthly_cost=Decimal("100"),
            monthly_savings=Decimal("100"),
            savings_percentage=50.0,
        )

        assert rec.action == RightSizingAction.DOWNSIZE
        assert rec.monthly_savings == Decimal("100")
        assert rec.savings_percentage == 50.0

    def test_reservation_constrained(self):
        """Test recommendation with reservation constraint."""
        rec = RightSizingRecommendation(
            resource_id="i-12345",
            resource_type="aws_instance",
            resource_name="my-instance",
            region="us-east-1",
            current_instance_type="m5.xlarge",
            current_monthly_cost=Decimal("200"),
            action=RightSizingAction.NO_CHANGE,
            recommended_instance_type=None,
            recommended_monthly_cost=Decimal("200"),
            monthly_savings=Decimal("0"),
            savings_percentage=0.0,
            has_reservation=True,
            reservation_id="ri-12345",
            reservation_type=ReservationType.RESERVED_INSTANCE,
            is_reservation_constrained=True,
        )

        assert rec.has_reservation
        assert rec.is_reservation_constrained
        assert rec.action == RightSizingAction.NO_CHANGE


class TestReservationWaste:
    """Test ReservationWaste model."""

    def test_create_waste(self):
        """Test creating a waste record."""
        waste = ReservationWaste(
            reservation_id="ri-12345",
            reservation_type=ReservationType.RESERVED_INSTANCE,
            utilization_level=UtilizationLevel.LOW,
            utilization_percentage=55.0,
            monthly_waste=Decimal("500"),
            recommendation="Review running instances",
        )

        assert waste.utilization_level == UtilizationLevel.LOW
        assert waste.monthly_waste == Decimal("500")


class TestUtilizationLevel:
    """Test utilization level classification."""

    def test_get_utilization_level(self):
        """Test utilization level from percentage."""
        assert get_utilization_level(95) == UtilizationLevel.HIGH
        assert get_utilization_level(85) == UtilizationLevel.MEDIUM
        assert get_utilization_level(60) == UtilizationLevel.LOW
        assert get_utilization_level(40) == UtilizationLevel.CRITICAL


class TestRIAwarePricingEngine:
    """Test RIAwarePricingEngine."""

    def test_create_engine(self):
        """Test creating an RI-aware pricing engine."""
        engine = RIAwarePricingEngine(
            region="us-east-1",
            currency=Currency.USD,
        )

        assert engine.region == "us-east-1"

    def test_has_reservation_for(self):
        """Test checking for reservations."""
        ri = ReservedInstance(
            reservation_id="ri-12345",
            instance_type="m5.large",
            instance_count=1,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.096"),
            hours_available=730,
            hours_used=0,
        )

        engine = RIAwarePricingEngine(
            region="us-east-1",
            reserved_instances=[ri],
        )

        has_ri, ri_type, ri_id = engine.has_reservation_for("m5.large")
        assert has_ri
        assert ri_type == ReservationType.RESERVED_INSTANCE
        assert ri_id == "ri-12345"

        has_ri2, _, _ = engine.has_reservation_for("m5.xlarge")
        assert not has_ri2

    def test_right_sizing_impact(self):
        """Test right-sizing impact analysis."""
        ri = ReservedInstance(
            reservation_id="ri-12345",
            instance_type="m5.xlarge",
            instance_count=1,
            availability_zone=None,
            region="us-east-1",
            scope="Region",
            offering_class="standard",
            offering_type="No Upfront",
            state=ReservationState.ACTIVE,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=365),
            fixed_price=Decimal("0"),
            usage_price=Decimal("0.192"),
            hours_available=730,
            hours_used=0,
        )

        engine = RIAwarePricingEngine(
            region="us-east-1",
            reserved_instances=[ri],
        )

        # Check impact of changing from m5.xlarge to m5.large
        impact = engine.get_right_sizing_impact("m5.xlarge", "m5.large")
        assert impact["has_reservation"]
        assert not impact.get("can_proceed", True)  # Standard RI is type-specific


class TestRIAwareAnalysis:
    """Test RIAwareAnalysis model."""

    def test_create_analysis(self):
        """Test creating an analysis result."""
        from datetime import date

        analysis = RIAwareAnalysis(
            analysis_date=date.today(),
            region="us-east-1",
            total_reservation_cost=Decimal("5000"),
            total_waste=Decimal("500"),
            total_potential_savings=Decimal("1000"),
        )

        assert analysis.region == "us-east-1"
        assert analysis.total_reservation_cost == Decimal("5000")

    def test_to_dict(self):
        """Test analysis serialization."""
        from datetime import date

        analysis = RIAwareAnalysis(
            analysis_date=date.today(),
            region="us-east-1",
            total_reservation_cost=Decimal("5000"),
            total_waste=Decimal("500"),
            total_potential_savings=Decimal("1000"),
            warnings=["2 reservations expiring soon"],
        )

        data = analysis.to_dict()
        assert data["region"] == "us-east-1"
        assert data["summary"]["total_reservation_cost"] == 5000.0
        assert len(data["warnings"]) == 1


class TestReservationType:
    """Test ReservationType enum."""

    def test_reservation_type_values(self):
        """Test reservation type values."""
        assert ReservationType.RESERVED_INSTANCE.value == "reserved_instance"
        assert ReservationType.SAVINGS_PLAN_COMPUTE.value == "savings_plan_compute"
        assert ReservationType.SAVINGS_PLAN_EC2.value == "savings_plan_ec2"


class TestRightSizingAction:
    """Test RightSizingAction enum."""

    def test_action_values(self):
        """Test action values."""
        assert RightSizingAction.DOWNSIZE.value == "downsize"
        assert RightSizingAction.UPSIZE.value == "upsize"
        assert RightSizingAction.TERMINATE.value == "terminate"
        assert RightSizingAction.NO_CHANGE.value == "no_change"
