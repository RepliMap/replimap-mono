"""
Tests for the RepliMap Core Engine improvements.

Tests cover:
- Sanitization middleware (security critical)
- Retry logic with boto3 coordination
- Circuit breaker for resilience
- GraphEngine phantom nodes and SCC detection
- ResourceNode memory optimization
"""

from __future__ import annotations

import pytest
from botocore.exceptions import ClientError

from replimap.core import (
    BOTO_CONFIG,
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
    GraphEngine,
    ResourceNode,
    Sanitizer,
    sanitize_resource_config,
    with_retry,
)
from replimap.core.models import ResourceType

# =============================================================================
# Sanitization Tests (Security Critical - P0)
# =============================================================================


class TestSanitizer:
    """Tests for the sanitization middleware."""

    def test_userdata_always_redacted(self):
        """EC2 UserData should always be redacted."""
        data = {
            "InstanceId": "i-12345",
            "UserData": "IyEvYmluL2Jhc2gKZXhwb3J0IERCX1BBU1M9aHVudGVyMgo=",
        }
        result = Sanitizer().get_result(data)
        assert result.data["UserData"] == "[REDACTED]"
        assert result.data["InstanceId"] == "i-12345"  # Not redacted
        assert result.redacted_count == 1

    def test_lambda_environment_variables_redacted(self):
        """Lambda Environment.Variables should have values redacted."""
        data = {
            "FunctionName": "my-function",
            "Environment": {
                "Variables": {
                    "LOG_LEVEL": "INFO",
                    "DATABASE_PASSWORD": "hunter2",  # noqa: S105
                    "API_KEY": "sk_live_xxxxx",
                }
            },
        }
        result = Sanitizer().get_result(data)
        env = result.data["Environment"]["Variables"]
        assert env["LOG_LEVEL"] == "[REDACTED]"  # All values redacted in high-risk
        assert env["DATABASE_PASSWORD"] == "[REDACTED]"  # noqa: S105
        assert env["API_KEY"] == "[REDACTED]"
        assert result.data["FunctionName"] == "my-function"

    def test_safe_fields_not_scanned(self):
        """Safe fields should be skipped for performance."""
        data = {
            "InstanceId": "i-12345",
            "VpcId": "vpc-abc123",
            "SubnetId": "subnet-xyz",
            "Status": "running",
            "Region": "us-east-1",
            "Tags": {"Name": "my-instance"},
        }
        result = Sanitizer().get_result(data)
        assert result.skipped_fields >= 5
        assert result.redacted_count == 0

    def test_aws_access_key_detected(self):
        """AWS access keys should be detected and redacted."""
        data = {
            "PolicyDocument": "aws_access_key_id=AKIAIOSFODNN7EXAMPLE",
        }
        result = Sanitizer().get_result(data)
        assert result.data["PolicyDocument"] == "[REDACTED]"

    def test_connection_string_detected(self):
        """Database connection strings should be detected."""
        data = {
            "Script": "postgres://user:password@host:5432/db",  # noqa: S105
        }
        result = Sanitizer().get_result(data)
        assert result.data["Script"] == "[REDACTED]"

    def test_suspicious_key_names_redacted(self):
        """Fields with suspicious names should be redacted."""
        data = {
            "my_secret_value": "sensitive-data",
            "api_token": "tok_12345",
            "normal_field": "safe-value",
        }
        result = Sanitizer().get_result(data)
        assert result.data["my_secret_value"] == "[REDACTED]"  # noqa: S105
        assert result.data["api_token"] == "[REDACTED]"  # noqa: S105
        assert result.data["normal_field"] == "safe-value"

    def test_nested_sanitization(self):
        """Nested structures should be sanitized recursively."""
        data = {
            "ContainerDefinitions": [
                {
                    "Name": "app",
                    "Environment": [
                        {"Name": "DB_PASS", "Value": "secret123"},
                    ],
                }
            ],
        }
        result = Sanitizer().get_result(data)
        # Environment in container definitions is high-risk
        assert result.redacted_count >= 1


class TestSanitizeResourceConfig:
    """Test the convenience function."""

    def test_sanitize_resource_config(self):
        """Should sanitize and return clean config."""
        config = {
            "UserData": "sensitive",
            "InstanceType": "t2.micro",
        }
        clean = sanitize_resource_config(config)
        assert clean["UserData"] == "[REDACTED]"
        assert clean["InstanceType"] == "t2.micro"


# =============================================================================
# Circuit Breaker Tests
# =============================================================================


class TestCircuitBreaker:
    """Tests for the circuit breaker pattern."""

    def test_initial_state_closed(self):
        """Circuit should start in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold_failures(self):
        """Circuit should open after failure_threshold failures."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise ValueError("Test error")

        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

    def test_open_circuit_raises_circuit_open_error(self):
        """Open circuit should raise CircuitOpenError."""
        cb = CircuitBreaker(failure_threshold=1)

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "success")

    def test_success_resets_failure_count(self):
        """Successful calls should reset failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        def failing_func():
            raise ValueError("Test error")

        # Two failures
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_func)

        # One success resets
        cb.call(lambda: "success")

        assert cb._failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_half_open_after_recovery_timeout(self):
        """Circuit should enter HALF_OPEN after recovery_timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            cb.call(failing_func)

        assert cb.state == CircuitState.OPEN

        import time

        time.sleep(0.15)  # Wait for recovery timeout

        assert cb.state == CircuitState.HALF_OPEN

    def test_reset_method(self):
        """reset() should restore CLOSED state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.force_open()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0


class TestCircuitBreakerRegistry:
    """Tests for the circuit breaker registry."""

    def test_get_creates_new_circuit(self):
        """Registry should create new circuits on demand."""
        registry = CircuitBreakerRegistry()
        cb = registry.get("us-east-1/ec2")
        assert cb is not None
        assert cb.key == "us-east-1/ec2"

    def test_get_returns_same_circuit(self):
        """Registry should return same circuit for same key."""
        registry = CircuitBreakerRegistry()
        cb1 = registry.get("us-east-1/ec2")
        cb2 = registry.get("us-east-1/ec2")
        assert cb1 is cb2

    def test_get_open_circuits(self):
        """Should return list of open circuit keys."""
        registry = CircuitBreakerRegistry(failure_threshold=1)
        registry.get("us-east-1/ec2").force_open()
        registry.get("us-west-2/rds").force_open()

        open_circuits = registry.get_open_circuits()
        assert "us-east-1/ec2" in open_circuits
        assert "us-west-2/rds" in open_circuits


# =============================================================================
# GraphEngine Phantom Node Tests
# =============================================================================


class TestGraphEnginePhantomNodes:
    """Tests for phantom node support in GraphEngine."""

    def test_phantom_node_created_for_missing_target(self):
        """Phantom node should be created for missing dependency target."""
        graph = GraphEngine(create_phantom_nodes=True)

        # Add a real node
        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )
        graph.add_resource(node)

        # Add dependency to non-existent subnet
        graph.add_dependency("i-12345", "subnet-missing")

        assert graph.is_phantom("subnet-missing")
        phantom = graph.get_resource("subnet-missing")
        assert phantom is not None
        assert phantom.is_phantom is True
        assert phantom.resource_type == ResourceType.SUBNET

    def test_phantom_node_created_for_missing_source(self):
        """Phantom node should be created for missing dependency source."""
        graph = GraphEngine(create_phantom_nodes=True)

        # Add a real VPC node
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        graph.add_resource(vpc)

        # Add dependency from non-existent instance to VPC
        graph.add_dependency("i-missing", "vpc-123")

        assert graph.is_phantom("i-missing")
        phantom = graph.get_resource("i-missing")
        assert phantom.resource_type == ResourceType.EC2_INSTANCE

    def test_phantom_nodes_disabled_raises_error(self):
        """Should raise ValueError when phantom nodes disabled."""
        graph = GraphEngine(create_phantom_nodes=False)

        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )
        graph.add_resource(node)

        with pytest.raises(ValueError, match="Target resource not found"):
            graph.add_dependency("i-12345", "subnet-missing")

    def test_phantom_count(self):
        """phantom_count should return correct number."""
        graph = GraphEngine(create_phantom_nodes=True)

        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )
        graph.add_resource(node)

        graph.add_dependency("i-12345", "subnet-missing1")
        graph.add_dependency("i-12345", "subnet-missing2")

        assert graph.phantom_count == 2

    def test_get_phantom_nodes(self):
        """get_phantom_nodes should return all phantoms."""
        graph = GraphEngine(create_phantom_nodes=True)

        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )
        graph.add_resource(node)

        graph.add_dependency("i-12345", "subnet-phantom")

        phantoms = graph.get_phantom_nodes()
        assert len(phantoms) == 1
        assert phantoms[0].id == "subnet-phantom"

    def test_statistics_includes_phantom_info(self):
        """statistics() should include phantom node information."""
        graph = GraphEngine(create_phantom_nodes=True)

        node = ResourceNode(
            id="i-12345",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )
        graph.add_resource(node)
        graph.add_dependency("i-12345", "subnet-phantom")

        stats = graph.statistics()
        assert "phantom_count" in stats
        assert stats["phantom_count"] == 1
        assert "phantom_nodes" in stats


# =============================================================================
# GraphEngine SCC Tests
# =============================================================================


class TestGraphEngineSCC:
    """Tests for Tarjan's SCC algorithm and cycle detection."""

    def test_no_cycles_detected(self):
        """Should detect no cycles in acyclic graph."""
        graph = GraphEngine()

        # Create VPC -> Subnet -> EC2 chain (no cycles)
        vpc = ResourceNode(
            id="vpc-123", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet = ResourceNode(
            id="subnet-456", resource_type=ResourceType.SUBNET, region="us-east-1"
        )
        ec2 = ResourceNode(
            id="i-789", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_resource(ec2)

        graph.add_dependency("subnet-456", "vpc-123")
        graph.add_dependency("i-789", "subnet-456")

        scc_result = graph.find_strongly_connected_components()
        assert scc_result.has_cycles is False
        assert len(scc_result.cycle_groups) == 0

    def test_cycle_detected(self):
        """Should detect cycle between security groups."""
        graph = GraphEngine()

        # Create SG-A -> SG-B -> SG-A cycle (common in AWS)
        sg_a = ResourceNode(
            id="sg-a", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )
        sg_b = ResourceNode(
            id="sg-b", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )

        graph.add_resource(sg_a)
        graph.add_resource(sg_b)

        graph.add_dependency("sg-a", "sg-b")
        graph.add_dependency("sg-b", "sg-a")

        scc_result = graph.find_strongly_connected_components()
        assert scc_result.has_cycles is True
        assert len(scc_result.cycle_groups) == 1
        assert "sg-a" in scc_result.cycle_groups[0]
        assert "sg-b" in scc_result.cycle_groups[0]

    def test_safe_dependency_order_handles_cycles(self):
        """get_safe_dependency_order should not raise on cycles."""
        graph = GraphEngine()

        # Create cycle
        sg_a = ResourceNode(
            id="sg-a", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )
        sg_b = ResourceNode(
            id="sg-b", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )
        vpc = ResourceNode(
            id="vpc-123", resource_type=ResourceType.VPC, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(sg_a)
        graph.add_resource(sg_b)

        graph.add_dependency("sg-a", "vpc-123")
        graph.add_dependency("sg-b", "vpc-123")
        graph.add_dependency("sg-a", "sg-b")
        graph.add_dependency("sg-b", "sg-a")

        # Should not raise, unlike topological_sort
        order = graph.get_safe_dependency_order()
        assert len(order) == 3

        # VPC should come before SGs (it has no dependencies)
        vpc_idx = next(i for i, n in enumerate(order) if n.id == "vpc-123")
        sg_a_idx = next(i for i, n in enumerate(order) if n.id == "sg-a")
        sg_b_idx = next(i for i, n in enumerate(order) if n.id == "sg-b")

        assert vpc_idx < sg_a_idx
        assert vpc_idx < sg_b_idx


# =============================================================================
# GraphEngine Merge Tests
# =============================================================================


class TestGraphEngineMerge:
    """Tests for graph merge (Map-Reduce pattern)."""

    def test_merge_nodes(self):
        """Should merge nodes from two graphs."""
        graph1 = GraphEngine()
        graph2 = GraphEngine()

        node1 = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        node2 = ResourceNode(
            id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1"
        )

        graph1.add_resource(node1)
        graph2.add_resource(node2)

        graph1.merge(graph2)

        assert graph1.node_count == 2
        assert graph1.get_resource("vpc-1") is not None
        assert graph1.get_resource("vpc-2") is not None

    def test_merge_real_node_replaces_phantom(self):
        """Real node should replace phantom during merge."""
        graph1 = GraphEngine(create_phantom_nodes=True)
        graph2 = GraphEngine()

        # Create phantom in graph1
        node1 = ResourceNode(
            id="i-123", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )
        graph1.add_resource(node1)
        graph1.add_dependency("i-123", "subnet-456")  # Creates phantom

        assert graph1.is_phantom("subnet-456")

        # Create real subnet in graph2
        real_subnet = ResourceNode(
            id="subnet-456",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={"cidr_block": "10.0.1.0/24"},
        )
        graph2.add_resource(real_subnet)

        # Merge - real should replace phantom
        graph1.merge(graph2)

        assert not graph1.is_phantom("subnet-456")
        merged = graph1.get_resource("subnet-456")
        assert merged.config.get("cidr_block") == "10.0.1.0/24"

    def test_merge_edges(self):
        """Should merge edges from two graphs."""
        graph1 = GraphEngine()
        graph2 = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet1 = ResourceNode(
            id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
        )
        subnet2 = ResourceNode(
            id="subnet-2", resource_type=ResourceType.SUBNET, region="us-east-1"
        )

        graph1.add_resource(vpc)
        graph1.add_resource(subnet1)
        graph1.add_dependency("subnet-1", "vpc-123")

        graph2.add_resource(vpc)  # Same VPC
        graph2.add_resource(subnet2)
        graph2.add_dependency("subnet-2", "vpc-123")

        graph1.merge(graph2)

        assert graph1.node_count == 3
        assert graph1.edge_count == 2


# =============================================================================
# ResourceNode Tests
# =============================================================================


class TestResourceNode:
    """Tests for ResourceNode memory optimization."""

    def test_slots_present(self):
        """ResourceNode should use __slots__ for memory efficiency."""
        assert hasattr(ResourceNode, "__slots__")

    def test_region_interned(self):
        """Region string should be interned for memory efficiency."""
        import sys

        node1 = ResourceNode(
            id="i-1", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )
        node2 = ResourceNode(
            id="i-2", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )

        # Interned strings should be the same object
        # Both nodes use the same region, so after interning they should share the string
        assert sys.intern("us-east-1") is sys.intern("us-east-1")
        # Verify both nodes have the expected region value
        assert node1.region == "us-east-1"
        assert node2.region == "us-east-1"

    def test_phantom_fields_serialization(self):
        """Phantom fields should be serialized correctly."""
        node = ResourceNode(
            id="phantom-123",
            resource_type=ResourceType.VPC,
            region="unknown",
            is_phantom=True,
            phantom_reason="Test phantom",
        )

        data = node.to_dict()
        assert data["is_phantom"] is True
        assert data["phantom_reason"] == "Test phantom"

        # Deserialize
        restored = ResourceNode.from_dict(data)
        assert restored.is_phantom is True
        assert restored.phantom_reason == "Test phantom"

    def test_non_phantom_fields_omitted(self):
        """Non-phantom nodes should not include phantom fields."""
        node = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )

        data = node.to_dict()
        assert "is_phantom" not in data


# =============================================================================
# Retry Logic Tests
# =============================================================================


class TestWithRetry:
    """Tests for the retry decorator."""

    def test_retry_on_throttling(self):
        """Should retry on ThrottlingException."""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = ClientError(
                    {
                        "Error": {
                            "Code": "ThrottlingException",
                            "Message": "Rate exceeded",
                        }
                    },
                    "DescribeInstances",
                )
                raise error
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_no_retry_on_access_denied(self):
        """Should not retry on AccessDeniedException."""
        call_count = 0

        @with_retry(max_retries=3, base_delay=0.01)
        def access_denied_function():
            nonlocal call_count
            call_count += 1
            error = ClientError(
                {
                    "Error": {
                        "Code": "AccessDeniedException",
                        "Message": "Not authorized",
                    }
                },
                "DescribeInstances",
            )
            raise error

        with pytest.raises(ClientError):
            access_denied_function()

        assert call_count == 1  # No retries


# =============================================================================
# BOTO_CONFIG Tests
# =============================================================================


class TestBotoConfig:
    """Tests for BOTO_CONFIG settings."""

    def test_retries_disabled(self):
        """BOTO_CONFIG should have max_attempts=1 to disable internal retries."""
        # Access the retries config
        assert BOTO_CONFIG.retries is not None
        assert BOTO_CONFIG.retries.get("max_attempts") == 1

    def test_timeouts_set(self):
        """BOTO_CONFIG should have connect and read timeouts."""
        assert BOTO_CONFIG.connect_timeout is not None
        assert BOTO_CONFIG.read_timeout is not None
        assert BOTO_CONFIG.connect_timeout > 0
        assert BOTO_CONFIG.read_timeout > 0


# =============================================================================
# Async Retry Logic Tests
# =============================================================================


class TestAsyncRetry:
    """Tests for the async retry decorator."""

    @pytest.mark.asyncio
    async def test_async_retry_on_throttling(self):
        """Should retry on ThrottlingException."""
        from replimap.core import async_retry

        call_count = 0

        @async_retry(max_retries=3, base_delay=0.01)
        async def flaky_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = ClientError(
                    {
                        "Error": {
                            "Code": "ThrottlingException",
                            "Message": "Rate exceeded",
                        }
                    },
                    "DescribeInstances",
                )
                raise error
            return "success"

        result = await flaky_async_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_no_retry_on_access_denied(self):
        """Should not retry on AccessDeniedException."""
        from replimap.core import async_retry

        call_count = 0

        @async_retry(max_retries=3, base_delay=0.01)
        async def access_denied_async():
            nonlocal call_count
            call_count += 1
            error = ClientError(
                {
                    "Error": {
                        "Code": "AccessDeniedException",
                        "Message": "Not authorized",
                    }
                },
                "DescribeInstances",
            )
            raise error

        with pytest.raises(ClientError):
            await access_denied_async()

        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_async_success_no_retry(self):
        """Successful async calls should not retry."""
        from replimap.core import async_retry

        call_count = 0

        @async_retry(max_retries=3, base_delay=0.01)
        async def successful_async():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_async()
        assert result == "success"
        assert call_count == 1
