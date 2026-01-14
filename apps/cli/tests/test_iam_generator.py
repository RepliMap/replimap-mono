"""
Comprehensive tests for Graph-Aware IAM Generator.

Tests cover:
- Boundary-aware traversal (prevents over-connectivity)
- Intent-aware action mapping (Producer/Consumer)
- Safe resource compression
- ARN building with partition detection
- Policy optimization and sharding
- Terraform output generation
"""

from __future__ import annotations

import json

import pytest

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.security.iam_generator import (
    AccessRole,
    ARNBuilder,
    GraphAwareIAMGenerator,
    IAMPolicy,
    IAMStatement,
    IntentAwareActionMapper,
    PolicyOptimizer,
    PolicyScope,
    ResourceBoundary,
    SafeResourceCompressor,
    TraversalController,
)

# ============================================================
# TRAVERSAL CONTROLLER TESTS
# ============================================================


class TestTraversalController:
    """Test boundary-aware traversal."""

    def test_terminal_blocks_traversal(self):
        """TERMINAL resources should block traversal at depth > 1."""
        ctrl = TraversalController(strict_mode=True)

        assert ctrl.get_boundary("aws_lambda_function") == ResourceBoundary.TERMINAL
        assert ctrl.should_traverse_through("aws_lambda_function", 1) is True  # Direct
        assert (
            ctrl.should_traverse_through("aws_lambda_function", 2) is False
        )  # Blocked

    def test_data_grants_but_stops(self):
        """DATA resources should grant permissions but not traverse in strict mode."""
        ctrl = TraversalController(strict_mode=True)

        assert ctrl.get_boundary("aws_sqs_queue") == ResourceBoundary.DATA
        assert ctrl.should_include_in_results("aws_sqs_queue") is True
        assert ctrl.should_traverse_through("aws_sqs_queue", 2) is False

    def test_data_traverses_in_non_strict_mode(self):
        """DATA resources can traverse in non-strict mode."""
        ctrl = TraversalController(strict_mode=False)

        assert ctrl.should_traverse_through("aws_sqs_queue", 2) is True

    def test_security_always_traverses(self):
        """SECURITY resources should always traverse."""
        ctrl = TraversalController(strict_mode=True)

        assert ctrl.get_boundary("aws_kms_key") == ResourceBoundary.SECURITY
        assert ctrl.should_traverse_through("aws_kms_key", 2) is True
        assert ctrl.should_traverse_through("aws_kms_key", 5) is True

    def test_transitive_always_traverses(self):
        """TRANSITIVE resources should always traverse."""
        ctrl = TraversalController(strict_mode=True)

        assert ctrl.get_boundary("aws_vpc") == ResourceBoundary.TRANSITIVE
        assert ctrl.should_traverse_through("aws_vpc", 2) is True

    def test_transitive_not_included_by_default(self):
        """TRANSITIVE resources shouldn't be included in results by default."""
        ctrl = TraversalController(include_networking=False)

        assert ctrl.should_include_in_results("aws_vpc") is False
        assert ctrl.should_include_in_results("aws_subnet") is False

    def test_transitive_included_when_requested(self):
        """TRANSITIVE resources included when networking flag is set."""
        ctrl = TraversalController(include_networking=True)

        assert ctrl.should_include_in_results("aws_vpc") is True

    def test_ownership_edges_blocked(self):
        """Ownership edges should block even at depth 1."""
        ctrl = TraversalController()

        # event_source_mapping = SQS triggers Lambda (reverse direction)
        assert (
            ctrl.should_traverse_through(
                "aws_lambda_function", 1, "event_source_mapping"
            )
            is False
        )
        assert ctrl.should_include_in_results("aws_sqs_queue", "triggered_by") is False

    def test_unknown_type_defaults_to_data(self):
        """Unknown resource types should default to DATA boundary."""
        ctrl = TraversalController()

        assert ctrl.get_boundary("aws_unknown_service") == ResourceBoundary.DATA


# ============================================================
# OVER-CONNECTIVITY PREVENTION TESTS
# ============================================================


class TestOverConnectivityPrevention:
    """Critical test: prevent permissions from spreading to other compute."""

    @pytest.fixture
    def mock_graph(self):
        """
        Create graph: Lambda A -> SQS -> Lambda B -> DynamoDB

        Lambda A should ONLY get SQS permissions, NOT DynamoDB.
        """
        graph = GraphEngine()

        # Add resources
        lambda_a = ResourceNode(
            id="lambda-a",
            resource_type=ResourceType.UNKNOWN,
            region="us-east-1",
            config={"function_name": "processor-a"},
            terraform_name="processor_a",
            original_name="processor-a",
        )
        # Override resource_type since we need aws_lambda_function
        object.__setattr__(lambda_a, "resource_type", "aws_lambda_function")

        sqs = ResourceNode(
            id="sqs-queue",
            resource_type=ResourceType.SQS_QUEUE,
            region="us-east-1",
            config={"name": "orders-queue"},
            terraform_name="orders_queue",
            original_name="orders-queue",
        )

        lambda_b = ResourceNode(
            id="lambda-b",
            resource_type=ResourceType.UNKNOWN,
            region="us-east-1",
            config={"function_name": "processor-b"},
            terraform_name="processor_b",
            original_name="processor-b",
        )
        object.__setattr__(lambda_b, "resource_type", "aws_lambda_function")

        dynamodb = ResourceNode(
            id="dynamodb-table",
            resource_type=ResourceType.UNKNOWN,
            region="us-east-1",
            config={"name": "orders-table"},
            terraform_name="orders_table",
            original_name="orders-table",
        )
        object.__setattr__(dynamodb, "resource_type", "aws_dynamodb_table")

        graph.add_resource(lambda_a)
        graph.add_resource(sqs)
        graph.add_resource(lambda_b)
        graph.add_resource(dynamodb)

        # Add dependencies
        graph.add_dependency("lambda-a", "sqs-queue", DependencyType.USES)
        graph.add_dependency("sqs-queue", "lambda-b", DependencyType.USES)
        graph.add_dependency("lambda-b", "dynamodb-table", DependencyType.USES)

        return graph

    def test_lambda_a_cannot_access_dynamodb(self, mock_graph):
        """Lambda A should NOT get DynamoDB permissions."""
        gen = GraphAwareIAMGenerator(
            mock_graph, "123456789012", "us-east-1", strict_mode=True
        )
        policies = gen.generate_for_principal("lambda-a", PolicyScope.RUNTIME_WRITE)

        all_arns = []
        all_actions = []
        for p in policies:
            for s in p.statements:
                all_arns.extend(s.resources)
                all_actions.extend(s.actions)

        # Should have SQS
        assert any("sqs" in r for r in all_arns), "Should have SQS ARN"
        assert any("sqs:" in a for a in all_actions), "Should have SQS actions"

        # Should NOT have DynamoDB
        assert not any("dynamodb" in r for r in all_arns), (
            "Should NOT have DynamoDB ARN"
        )

        # Should NOT have Lambda B permissions
        assert not any("lambda" in r and "processor-b" in r for r in all_arns), (
            "Should NOT have Lambda B ARN"
        )

    def test_lambda_b_can_access_dynamodb(self, mock_graph):
        """Lambda B SHOULD get DynamoDB permissions (direct connection)."""
        gen = GraphAwareIAMGenerator(
            mock_graph, "123456789012", "us-east-1", strict_mode=True
        )
        policies = gen.generate_for_principal("lambda-b", PolicyScope.RUNTIME_FULL)

        all_arns = []
        for p in policies:
            for s in p.statements:
                all_arns.extend(s.resources)

        # Should have DynamoDB
        assert any("dynamodb" in r for r in all_arns), "Should have DynamoDB ARN"


# ============================================================
# INTENT-AWARE ACTION MAPPER TESTS
# ============================================================


class TestIntentAwareMapper:
    """Test Producer/Consumer action selection."""

    def test_sqs_producer_vs_consumer(self):
        mapper = IntentAwareActionMapper()

        producer = mapper.get_actions(
            "aws_sqs_queue", PolicyScope.RUNTIME_WRITE, AccessRole.PRODUCER
        )
        consumer = mapper.get_actions(
            "aws_sqs_queue", PolicyScope.RUNTIME_READ, AccessRole.CONSUMER
        )

        assert "sqs:SendMessage" in producer
        assert "sqs:SendMessage" not in consumer
        assert "sqs:ReceiveMessage" in consumer
        assert "sqs:ReceiveMessage" not in producer

    def test_s3_producer_vs_consumer(self):
        mapper = IntentAwareActionMapper()

        producer = mapper.get_actions(
            "aws_s3_bucket", PolicyScope.RUNTIME_WRITE, AccessRole.PRODUCER
        )
        consumer = mapper.get_actions(
            "aws_s3_bucket", PolicyScope.RUNTIME_READ, AccessRole.CONSUMER
        )

        assert "s3:PutObject" in producer
        assert "s3:GetObject" in consumer
        assert "s3:GetObject" not in producer
        assert "s3:PutObject" not in consumer

    def test_runtime_full_combines_read_write(self):
        mapper = IntentAwareActionMapper()

        full = mapper.get_actions(
            "aws_dynamodb_table", PolicyScope.RUNTIME_FULL, AccessRole.BIDIRECTIONAL
        )

        # Should have both read and write
        assert "dynamodb:GetItem" in full
        assert "dynamodb:PutItem" in full
        assert "dynamodb:Query" in full
        assert "dynamodb:DeleteItem" in full

    def test_edge_role_detection(self):
        mapper = IntentAwareActionMapper()

        # writes_to should be PRODUCER
        role = mapper.determine_access_role(
            "aws_lambda_function", "aws_sqs_queue", "writes_to"
        )
        assert role == AccessRole.PRODUCER

        # reads_from should be CONSUMER
        role = mapper.determine_access_role(
            "aws_lambda_function", "aws_s3_bucket", "reads_from"
        )
        assert role == AccessRole.CONSUMER

        # invokes should be CONTROLLER
        role = mapper.determine_access_role(
            "aws_lambda_function", "aws_lambda_function", "invokes"
        )
        assert role == AccessRole.CONTROLLER

    def test_is_compute_type(self):
        mapper = IntentAwareActionMapper()

        assert mapper.is_compute_type("aws_lambda_function") is True
        assert mapper.is_compute_type("aws_instance") is True
        assert mapper.is_compute_type("aws_s3_bucket") is False
        assert mapper.is_compute_type("aws_sqs_queue") is False


# ============================================================
# ARN BUILDER TESTS
# ============================================================


class TestARNBuilder:
    """Test ARN construction with partition detection."""

    def test_standard_partition(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        assert builder.partition == "aws"

    def test_china_partition(self):
        builder = ARNBuilder("123456789012", "cn-north-1")
        assert builder.partition == "aws-cn"

    def test_govcloud_partition(self):
        builder = ARNBuilder("123456789012", "us-gov-west-1")
        assert builder.partition == "aws-us-gov"

    def test_s3_bucket_arn(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_s3_bucket", "my-bucket", attributes={"bucket": "my-bucket"}
        )

        assert len(arns) == 2
        assert "arn:aws:s3:::my-bucket" in arns
        assert "arn:aws:s3:::my-bucket/*" in arns

    def test_dynamodb_table_arn(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_dynamodb_table", "my-table", attributes={"name": "my-table"}
        )

        assert len(arns) == 2
        assert "arn:aws:dynamodb:us-east-1:123456789012:table/my-table" in arns
        assert "arn:aws:dynamodb:us-east-1:123456789012:table/my-table/index/*" in arns

    def test_sqs_queue_arn(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_sqs_queue", "my-queue", attributes={"name": "my-queue"}
        )

        assert len(arns) == 1
        assert arns[0] == "arn:aws:sqs:us-east-1:123456789012:my-queue"

    def test_lambda_arn(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_lambda_function", "my-func", attributes={"function_name": "my-func"}
        )

        assert len(arns) == 1
        assert arns[0] == "arn:aws:lambda:us-east-1:123456789012:function:my-func"

    def test_secrets_manager_arn_has_wildcard(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_secretsmanager_secret", "my-secret", attributes={"name": "my-secret"}
        )

        # Secrets have random suffix, so ARN ends with *
        assert len(arns) == 1
        assert arns[0].endswith("*")

    def test_uses_arn_attribute_when_present(self):
        builder = ARNBuilder("123456789012", "us-east-1")
        arns = builder.build_arn(
            "aws_s3_bucket",
            "my-bucket",
            attributes={"arn": "arn:aws:s3:::custom-bucket"},
        )

        assert "arn:aws:s3:::custom-bucket" in arns


# ============================================================
# SAFE COMPRESSION TESTS
# ============================================================


class TestSafeCompression:
    """Test security-aware compression."""

    def test_s3_never_compressed(self):
        comp = SafeResourceCompressor(strict_mode=True)

        arns = [f"arn:aws:s3:::bucket-{i}" for i in range(15)]
        result = comp.compress(arns)

        # S3 should never compress
        assert len(result) == 15

    def test_kms_never_compressed(self):
        comp = SafeResourceCompressor(strict_mode=True)

        arns = [f"arn:aws:kms:us-east-1:123456789012:key/key-{i}" for i in range(15)]
        result = comp.compress(arns)

        # KMS should never compress
        assert len(result) == 15

    def test_below_threshold_not_compressed(self):
        comp = SafeResourceCompressor()

        arns = [f"arn:aws:sqs:us-east-1:123456789012:queue-{i}" for i in range(5)]
        result = comp.compress(arns)

        # Below threshold, no compression
        assert len(result) == 5


# ============================================================
# IAM STATEMENT AND POLICY TESTS
# ============================================================


class TestIAMStatement:
    """Test IAM statement structure."""

    def test_to_dict_single_resource(self):
        stmt = IAMStatement(
            sid="TestSid",
            actions=["s3:GetObject"],
            resources=["arn:aws:s3:::bucket/*"],
        )

        d = stmt.to_dict()
        assert d["Sid"] == "TestSid"
        assert d["Effect"] == "Allow"
        assert d["Action"] == ["s3:GetObject"]
        # Single resource should not be a list
        assert d["Resource"] == "arn:aws:s3:::bucket/*"

    def test_to_dict_multiple_resources(self):
        stmt = IAMStatement(
            sid="TestSid",
            actions=["s3:GetObject", "s3:PutObject"],
            resources=["arn:aws:s3:::bucket1/*", "arn:aws:s3:::bucket2/*"],
        )

        d = stmt.to_dict()
        assert len(d["Resource"]) == 2
        assert len(d["Action"]) == 2

    def test_estimated_size(self):
        stmt = IAMStatement(
            sid="Test",
            actions=["s3:GetObject"],
            resources=["arn:aws:s3:::bucket/*"],
        )

        size = stmt.estimated_size()
        assert size > 0
        assert size == len(json.dumps(stmt.to_dict()))


class TestIAMPolicy:
    """Test IAM policy structure."""

    def test_to_json(self):
        policy = IAMPolicy(
            name="test-policy",
            description="Test",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::bucket/*"],
                )
            ],
        )

        json_str = policy.to_json()
        parsed = json.loads(json_str)

        assert parsed["Version"] == "2012-10-17"
        assert len(parsed["Statement"]) == 1

    def test_is_least_privilege_true(self):
        policy = IAMPolicy(
            name="test",
            description="",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::specific-bucket/*"],
                )
            ],
        )

        assert policy.is_least_privilege() is True

    def test_is_least_privilege_false_wildcard_resource(self):
        policy = IAMPolicy(
            name="test",
            description="",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["*"],
                )
            ],
        )

        assert policy.is_least_privilege() is False

    def test_is_least_privilege_false_wildcard_action(self):
        policy = IAMPolicy(
            name="test",
            description="",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:*"],
                    resources=["arn:aws:s3:::bucket/*"],
                )
            ],
        )

        assert policy.is_least_privilege() is False

    def test_action_and_resource_counts(self):
        policy = IAMPolicy(
            name="test",
            description="",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject", "s3:PutObject"],
                    resources=["arn:aws:s3:::bucket1/*", "arn:aws:s3:::bucket2/*"],
                ),
                IAMStatement(
                    sid="SQS",
                    actions=["sqs:SendMessage"],
                    resources=["arn:aws:sqs:us-east-1:123:queue"],
                ),
            ],
        )

        assert policy.action_count() == 3
        assert policy.resource_count() == 3


# ============================================================
# TERRAFORM OUTPUT TESTS
# ============================================================


class TestTerraformOutput:
    """Test Terraform generation."""

    def test_policy_to_terraform(self):
        policy = IAMPolicy(
            name="test-policy",
            description="Test policy",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::bucket/*"],
                )
            ],
        )

        tf = policy.to_terraform()

        assert 'resource "aws_iam_policy"' in tf
        assert "test_policy" in tf  # sanitized name
        assert "POLICY" in tf

    def test_module_with_role(self):
        policy = IAMPolicy(
            name="test-policy",
            description="Test",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::bucket/*"],
                )
            ],
        )

        tf = policy.to_terraform_module("test-role", create_role=True)

        assert "aws_iam_role" in tf
        assert "assume_role_policy" in tf
        assert "aws_iam_policy" in tf
        assert "aws_iam_role_policy_attachment" in tf

    def test_module_without_role(self):
        policy = IAMPolicy(
            name="test-policy",
            description="Test",
            statements=[],
        )

        tf = policy.to_terraform_module("existing-role", create_role=False)

        # Should NOT have a role definition (but will have role_policy_attachment)
        assert 'resource "aws_iam_role"' not in tf
        assert "aws_iam_policy" in tf
        assert '"existing-role"' in tf

    def test_service_principal_detection(self):
        policy = IAMPolicy(name="test", description="", statements=[])

        # Lambda -> lambda.amazonaws.com
        tf = policy.to_terraform_module("role", True, "aws_lambda_function")
        assert "lambda.amazonaws.com" in tf

        # ECS -> ecs-tasks.amazonaws.com
        tf = policy.to_terraform_module("role", True, "aws_ecs_task_definition")
        assert "ecs-tasks.amazonaws.com" in tf


# ============================================================
# POLICY OPTIMIZER TESTS
# ============================================================


class TestPolicyOptimizer:
    """Test policy optimization."""

    def test_small_policy_not_sharded(self):
        optimizer = PolicyOptimizer()

        policy = IAMPolicy(
            name="small-policy",
            description="Small",
            statements=[
                IAMStatement(
                    sid="S3",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::bucket/*"],
                )
            ],
        )

        result = optimizer.optimize(policy)
        assert len(result) == 1
        assert result[0].name == "small-policy"


# ============================================================
# INTEGRATION TESTS
# ============================================================


class TestGraphAwareIAMGeneratorIntegration:
    """Integration tests for the full generator."""

    @pytest.fixture
    def simple_graph(self):
        """Lambda -> S3 -> KMS"""
        graph = GraphEngine()

        lambda_func = ResourceNode(
            id="lambda-processor",
            resource_type=ResourceType.UNKNOWN,
            region="us-east-1",
            config={"function_name": "data-processor"},
            terraform_name="data_processor",
            original_name="data-processor",
        )
        object.__setattr__(lambda_func, "resource_type", "aws_lambda_function")

        s3_bucket = ResourceNode(
            id="s3-data-bucket",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"bucket": "data-bucket"},
            terraform_name="data_bucket",
            original_name="data-bucket",
        )

        kms_key = ResourceNode(
            id="kms-encryption-key",
            resource_type=ResourceType.UNKNOWN,
            region="us-east-1",
            config={"key_id": "abc-123-def"},
            terraform_name="encryption_key",
            original_name="encryption-key",
        )
        object.__setattr__(kms_key, "resource_type", "aws_kms_key")

        graph.add_resource(lambda_func)
        graph.add_resource(s3_bucket)
        graph.add_resource(kms_key)

        graph.add_dependency("lambda-processor", "s3-data-bucket", DependencyType.USES)
        graph.add_dependency(
            "s3-data-bucket", "kms-encryption-key", DependencyType.USES
        )

        return graph

    def test_generates_policy_for_lambda(self, simple_graph):
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        policies = gen.generate_for_principal(
            "lambda-processor", PolicyScope.RUNTIME_FULL
        )

        assert len(policies) >= 1
        policy = policies[0]

        # Should have statements
        assert len(policy.statements) > 0

        # Should be least privilege
        assert policy.is_least_privilege()

    def test_includes_cloudwatch_logs_for_lambda(self, simple_graph):
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        policies = gen.generate_for_principal(
            "lambda-processor", PolicyScope.RUNTIME_FULL
        )

        all_sids = [s.sid for p in policies for s in p.statements]
        assert "CloudWatchLogs" in all_sids

    def test_includes_kms_through_s3(self, simple_graph):
        """KMS key should be included as it's a SECURITY resource."""
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        policies = gen.generate_for_principal(
            "lambda-processor", PolicyScope.RUNTIME_FULL
        )

        all_arns = [r for p in policies for s in p.statements for r in s.resources]

        # Should have KMS (traversed through S3)
        assert any("kms" in r for r in all_arns)

    def test_policy_name_includes_scope(self, simple_graph):
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        policies = gen.generate_for_principal(
            "lambda-processor", PolicyScope.RUNTIME_READ
        )

        assert "runtime_read" in policies[0].name

    def test_raises_for_nonexistent_resource(self, simple_graph):
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        with pytest.raises(ValueError, match="Resource not found"):
            gen.generate_for_principal("nonexistent-resource", PolicyScope.RUNTIME_READ)

    def test_terraform_output_generation(self, simple_graph):
        gen = GraphAwareIAMGenerator(simple_graph, "123456789012", "us-east-1")

        policies = gen.generate_for_principal(
            "lambda-processor", PolicyScope.RUNTIME_FULL
        )

        tf = gen.generate_terraform_output(policies, "processor-role", create_role=True)

        assert "aws_iam_role" in tf
        assert "aws_iam_policy" in tf
        assert "aws_iam_role_policy_attachment" in tf
        assert "lambda.amazonaws.com" in tf
